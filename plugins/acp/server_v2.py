"""Frontier ACP v2 Draft server with ACK/state turns and in-process replay."""

from __future__ import annotations

import asyncio
import base64
import datetime as dt
import uuid
from contextlib import suppress
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from nonebot import logger

from acp import RequestError
from acp.experimental.v2 import schema
from utils.agents.runtime_gateway import AgentRuntime, FrontierAgentRuntime
from utils.media import resolve_media, standard_media_block

from .server import FrontierAcpServer, _AcpProgressBridge


@dataclass(slots=True)
class _Session:
    session_id: str
    cwd: str
    updated_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))
    task: asyncio.Task[None] | None = None
    started: asyncio.Event = field(default_factory=asyncio.Event)
    cancel_requested: bool = False
    closed: bool = False
    replaying: bool = False
    updates: list[Any] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class _ProgressSink:
    """Reuse Frontier's sanitized progress bridge with v2 update shapes."""

    def __init__(self, server: FrontierAcpV2Server, session: _Session) -> None:
        self.server = server
        self.session = session
        self.turn_id = str(uuid.uuid4())

    async def session_update(self, *, session_id: str, update: Any) -> None:
        del session_id
        raw = update.model_dump(by_alias=True, exclude_none=True)
        kind = raw["sessionUpdate"]
        if kind in {"agent_message_chunk", "agent_thought_chunk"}:
            raw["messageId"] = str(uuid.uuid4())
        if kind in {"tool_call", "tool_call_update"}:
            raw["sessionUpdate"] = "tool_call_update"
            raw["toolCallId"] = f"{self.turn_id}:{raw['toolCallId']}"
        notification = schema.UpdateSessionNotification.model_validate({
            "sessionId": self.session.session_id, "update": raw,
        })
        await self.server._send(self.session, notification.update)


class FrontierAcpV2Server:
    """The v2 session surface; cwd remains metadata for Frontier's sandbox."""

    def __init__(self, runtime: AgentRuntime | None = None) -> None:
        self._runtime = runtime or FrontierAgentRuntime()
        self._connection: Any = None
        self._sessions: dict[str, _Session] = {}

    def on_connect(self, connection: Any) -> None:
        self._connection = connection

    async def initialize(self, request: schema.InitializeRequest) -> schema.InitializeResponse:
        if request.protocol_version != 2:
            raise RequestError.invalid_params({"reason": "This entry point requires ACP v2"})
        return schema.InitializeResponse(
            protocol_version=2,
            info=schema.Implementation(name="frontier", title="Frontier Deep Agent", version="0.1.3"),
            capabilities=schema.AgentCapabilities(session=schema.SessionCapabilities(
                prompt=schema.PromptCapabilities(
                    image=schema.PromptImageCapabilities(), audio=schema.PromptAudioCapabilities(),
                ),
            )),
            auth_methods=[],
        )

    @staticmethod
    def _workspace(request: Any) -> None:
        if not Path(request.cwd).is_absolute():
            raise RequestError.invalid_params({"reason": "cwd must be an absolute path"})
        if request.additional_directories or request.mcp_servers:
            raise RequestError.invalid_params({"reason": "Additional directories and MCP servers are not supported"})

    def _session(self, session_id: str, *, active: bool = True) -> _Session:
        session = self._sessions.get(session_id)
        if session is None or (active and session.closed):
            raise RequestError.resource_not_found(session_id)
        return session

    async def new_session(self, request: schema.NewSessionRequest) -> schema.NewSessionResponse:
        self._workspace(request)
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = _Session(session_id, request.cwd)
        return schema.NewSessionResponse(session_id=session_id)

    async def list_sessions(self, request: schema.ListSessionsRequest) -> schema.ListSessionsResponse:
        if request.cursor is not None:
            raise RequestError.invalid_params({"reason": "No pagination cursor was issued"})
        return schema.ListSessionsResponse(sessions=[
            schema.SessionInfo(
                session_id=session.session_id, cwd=session.cwd, title="Frontier ACP session",
                updated_at=session.updated_at.isoformat().replace("+00:00", "Z"),
            )
            for session in sorted(self._sessions.values(), key=lambda item: item.updated_at, reverse=True)
            if request.cwd is None or request.cwd == session.cwd
        ])

    async def _send(self, session: _Session, update: Any, *, record: bool = True) -> None:
        async with session.send_lock:
            if record:
                session.updates.append(update.model_copy(deep=True))
            await self._connection.session_update(schema.UpdateSessionNotification(
                session_id=session.session_id, update=update,
            ))

    async def resume_session(self, request: schema.ResumeSessionRequest) -> schema.ResumeSessionResponse:
        self._workspace(request)
        session = self._session(request.session_id, active=False)
        if session.cwd != request.cwd:
            raise RequestError.invalid_params({"reason": "cwd does not match the session"})
        if session.task is not None or session.replaying:
            raise RequestError.invalid_request({"reason": "Session is busy"})
        if request.replay_from is not None and request.replay_from.type != "start":
            raise RequestError.invalid_params({"reason": "Unsupported replay cursor"})
        session.replaying = True
        try:
            if request.replay_from is not None:
                for update in session.updates:
                    await self._send(session, update, record=False)
            session.closed = False
            return schema.ResumeSessionResponse()
        finally:
            session.replaying = False

    async def prompt(self, request: schema.PromptRequest) -> schema.PromptResponse:
        session = self._session(request.session_id)
        if self._connection is None:
            raise RequestError.internal_error({"reason": "ACP connection is not ready"})
        if session.task is not None or session.replaying:
            raise RequestError.invalid_request({"reason": "Session is busy"})
        # Validate before ACK; reserve the session before the background task
        # can run so concurrent prompts cannot both be accepted.
        runtime_request = FrontierAcpServer._request(session.session_id, request.prompt)
        session.started.clear()
        session.cancel_requested = False
        session.task = asyncio.create_task(self._execute(session, request, runtime_request))
        return schema.PromptResponse()

    async def _execute(self, session: _Session, request: Any, runtime_request: Any) -> None:
        stop_reason = "end_turn"
        session.started.set()
        try:
            await self._send(session, schema.UserMessageUpdate(
                message_id=str(uuid.uuid4()), content=request.prompt,
            ))
            await self._send(session, schema.RunningSessionStateUpdate())
            content: list[dict[str, Any]] = [{"type": "text", "text": runtime_request.prompt}]
            content.extend(standard_media_block(resolve_media(item.data, item.kind, declared_mime=item.mime_type))
                           for item in (*runtime_request.images, *runtime_request.audio))
            session.messages.append({"role": "user", "content": content})
            if session.cancel_requested:
                raise asyncio.CancelledError
            bridge = _AcpProgressBridge(_ProgressSink(self, session), session.session_id)
            result = await self._runtime.prompt(
                replace(runtime_request, messages=tuple(session.messages)), progress_reporter=bridge,
            )
            if result.error:
                raise RuntimeError("Frontier runtime failed")
            blocks: list[Any] = []
            if result.text:
                blocks.append(schema.TextContentBlock(text=result.text))
            for artifact in result.artifacts:
                block_class = schema.ImageContentBlock if artifact.kind == "image" else schema.AudioContentBlock
                blocks.append(block_class(data=base64.b64encode(artifact.data).decode("ascii"),
                                          mime_type=artifact.mime_type))
            if not blocks:
                blocks.append(schema.TextContentBlock(text="Frontier 已完成，但没有生成响应。"))
            await self._send(session, schema.AgentMessageUpdate(message_id=str(uuid.uuid4()), content=blocks))
            session.messages.append({"role": "assistant", "content": result.text or "[已生成媒体]"})
        except asyncio.CancelledError:
            stop_reason = "cancelled"
        except Exception as exc:
            logger.warning("Frontier ACP v2 session failed: {}", type(exc).__name__)
            stop_reason = "refusal"
            with suppress(Exception):
                await self._send(session, schema.AgentMessageUpdate(
                    message_id=str(uuid.uuid4()), content=[schema.TextContentBlock(text="Frontier 执行失败，请稍后重试。")],
                ))
        finally:
            try:
                await self._send(session, schema.IdleSessionStateUpdate(stop_reason=stop_reason))
            except Exception as exc:
                logger.warning("ACP v2 completion delivery failed: {}", type(exc).__name__)
            finally:
                session.updated_at = dt.datetime.now(dt.UTC)
                session.task = None

    async def cancel_session(self, notification: schema.CancelSessionNotification) -> None:
        session = self._sessions.get(notification.session_id)
        if session is None or session.task is None:
            return
        task = session.task
        if session.cancel_requested:
            await asyncio.shield(task)
            return
        was_started = session.started.is_set()
        session.cancel_requested = True
        # Let a newly accepted task install its cancellation/final-state guard.
        await session.started.wait()
        if was_started and not task.done():
            task.cancel()
        await asyncio.shield(task)

    async def close_session(self, request: schema.CloseSessionRequest) -> schema.CloseSessionResponse:
        session = self._session(request.session_id)
        if session.replaying:
            raise RequestError.invalid_request({"reason": "Session is replaying"})
        session.closed = True
        await self.cancel_session(schema.CancelSessionNotification(session_id=session.session_id))
        return schema.CloseSessionResponse()

    async def aclose(self) -> None:
        for session in list(self._sessions.values()):
            await self.cancel_session(schema.CancelSessionNotification(session_id=session.session_id))
