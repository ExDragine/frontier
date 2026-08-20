"""ACP v1 stdio server exposing Frontier's built-in Deep Agent."""

from __future__ import annotations

import asyncio
import base64
import binascii
import contextlib
import datetime as dt
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import acp
from nonebot import logger

from utils.agents.progress import ProgressEvent
from utils.agents.runtime_gateway import (
    AgentRuntime,
    AgentRuntimeMedia,
    AgentRuntimeRequest,
    FrontierAgentRuntime,
)

_MAX_MEDIA_BYTES = 20 * 1024 * 1024
_MAX_PROMPT_BYTES = 2 * 1024 * 1024


@dataclass(slots=True)
class _ServerSession:
    session_id: str
    cwd: str
    updated_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    active_task: asyncio.Task[Any] | None = None


class _AcpProgressBridge:
    """Map sanitized Frontier progress events to ACP session updates."""

    def __init__(self, connection: Any, session_id: str) -> None:
        self._connection = connection
        self._session_id = session_id
        self._lock = asyncio.Lock()
        self._counter = 0
        self._tool_ids: dict[str, str] = {}

    async def _send(self, update: Any) -> None:
        async with self._lock:
            await self._connection.session_update(
                session_id=self._session_id,
                update=update,
            )

    def _tool_id(self, key: str) -> str:
        if key not in self._tool_ids:
            self._counter += 1
            self._tool_ids[key] = f"frontier-tool-{self._counter}"
        return self._tool_ids[key]

    async def __call__(self, event: ProgressEvent) -> None:
        detail = event.detail or {}
        if event.type == "assistant_preamble" and event.message.strip():
            await self._send(acp.update_agent_message_text(event.message.strip()))
            return
        if event.type == "thinking":
            await self._send(acp.update_agent_thought_text("Frontier 正在处理请求…"))
            return
        if event.type in {"tool_call", "subagent_start"}:
            key = str(detail.get("tool_name") or detail.get("name") or event.message)
            await self._send(
                acp.start_tool_call(
                    self._tool_id(key),
                    event.message,
                    kind="other",
                    status="in_progress",
                )
            )
            return
        if event.type in {"tool_result", "subagent_done"}:
            key = str(detail.get("tool_name") or detail.get("name") or event.message)
            success = detail.get("success") is not False and detail.get("status") not in {
                "failed",
                "error",
            }
            await self._send(
                acp.update_tool_call(
                    self._tool_id(key),
                    title=event.message,
                    status="completed" if success else "failed",
                )
            )


class FrontierAcpServer:
    """ACP Agent implementation backed by a restricted Frontier runtime."""

    def __init__(self, runtime: AgentRuntime | None = None) -> None:
        self._runtime = runtime or FrontierAgentRuntime()
        self._connection: Any | None = None
        self._sessions: dict[str, _ServerSession] = {}

    def on_connect(self, conn: Any) -> None:
        self._connection = conn

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Any | None = None,
        client_info: Any | None = None,
        **kwargs: Any,
    ) -> Any:
        del protocol_version, client_capabilities, client_info, kwargs
        return acp.InitializeResponse(
            protocol_version=acp.PROTOCOL_VERSION,
            agent_capabilities=acp.schema.AgentCapabilities(
                load_session=False,
                prompt_capabilities=acp.schema.PromptCapabilities(
                    image=True,
                    audio=True,
                    embedded_context=False,
                ),
                session_capabilities=acp.schema.SessionCapabilities(
                    list=acp.schema.SessionListCapabilities(),
                    close=acp.schema.SessionCloseCapabilities(),
                ),
            ),
            auth_methods=[],
            agent_info=acp.schema.Implementation(
                name="frontier",
                title="Frontier Deep Agent",
                version="0.1.3",
            ),
        )

    async def authenticate(self, method_id: str, **kwargs: Any) -> Any:
        del method_id, kwargs
        raise acp.RequestError.method_not_found("authenticate")

    async def new_session(
        self,
        cwd: str,
        additional_directories: list[str] | None = None,
        mcp_servers: list[Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        del kwargs
        if additional_directories or mcp_servers:
            raise acp.RequestError.invalid_params(
                {"reason": "Frontier ACP server does not accept additional directories or MCP servers"}
            )
        if not Path(cwd).is_absolute():
            raise acp.RequestError.invalid_params({"reason": "cwd must be an absolute path"})
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = _ServerSession(session_id=session_id, cwd=cwd)
        return acp.NewSessionResponse(session_id=session_id)

    async def list_sessions(
        self,
        cwd: str | None = None,
        cursor: str | None = None,
        **kwargs: Any,
    ) -> Any:
        del cursor, kwargs
        sessions = [session for session in self._sessions.values() if cwd is None or session.cwd == cwd]
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return acp.schema.ListSessionsResponse(
            sessions=[
                acp.schema.SessionInfo(
                    session_id=session.session_id,
                    cwd=session.cwd,
                    additional_directories=[],
                    title="Frontier ACP session",
                    updated_at=session.updated_at.isoformat().replace("+00:00", "Z"),
                )
                for session in sessions
            ]
        )

    @staticmethod
    def _decode_media(block: Any, kind: str) -> AgentRuntimeMedia:
        try:
            data = base64.b64decode(str(getattr(block, "data", "") or ""), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise acp.RequestError.invalid_params({"reason": f"invalid {kind} base64"}) from exc
        if not data or len(data) > _MAX_MEDIA_BYTES:
            raise acp.RequestError.invalid_params(
                {"reason": f"{kind} must contain 1 to {_MAX_MEDIA_BYTES} bytes"}
            )
        mime_type = str(getattr(block, "mime_type", "") or "application/octet-stream")
        return AgentRuntimeMedia(kind=kind, data=data, mime_type=mime_type)

    @classmethod
    def _request(cls, session_id: str, prompt: list[Any]) -> AgentRuntimeRequest:
        text_parts: list[str] = []
        images: list[AgentRuntimeMedia] = []
        audio: list[AgentRuntimeMedia] = []
        text_bytes = 0
        media_bytes = 0
        for block in prompt:
            kind = str(getattr(block, "type", "") or "")
            if kind == "text":
                value = str(getattr(block, "text", "") or "")
                text_bytes += len(value.encode("utf-8"))
                text_parts.append(value)
            elif kind in {"image", "audio"}:
                media = cls._decode_media(block, kind)
                media_bytes += len(media.data)
                (images if kind == "image" else audio).append(media)
            elif kind == "resource_link":
                uri = str(getattr(block, "uri", "") or "")
                if uri:
                    text_parts.append(f"[客户端资源链接，仅作引用：{uri}]")
                    text_bytes += len(uri.encode("utf-8"))
            else:
                raise acp.RequestError.invalid_params(
                    {"reason": f"unsupported prompt content type: {kind or 'unknown'}"}
                )
        if text_bytes > _MAX_PROMPT_BYTES:
            raise acp.RequestError.invalid_params({"reason": "prompt text is too large"})
        if media_bytes > _MAX_MEDIA_BYTES * 2:
            raise acp.RequestError.invalid_params({"reason": "prompt media payload is too large"})
        text = "\n".join(part for part in text_parts if part).strip()
        if not text and not images and not audio:
            raise acp.RequestError.invalid_params({"reason": "prompt must not be empty"})
        return AgentRuntimeRequest(
            session_id=session_id,
            prompt=text or "请分析客户端提供的媒体内容。",
            images=tuple(images),
            audio=tuple(audio),
        )

    async def prompt(  # noqa: C901
        self, session_id: str, prompt: list[Any], **kwargs: Any
    ) -> Any:
        del kwargs
        session = self._sessions.get(session_id)
        if session is None:
            raise acp.RequestError.resource_not_found(session_id)
        if self._connection is None:
            raise acp.RequestError.internal_error({"reason": "ACP connection is not ready"})
        request = self._request(session_id, prompt)
        async with session.lock:
            session.active_task = asyncio.current_task()
            bridge = _AcpProgressBridge(self._connection, session_id)
            try:
                result = await self._runtime.prompt(request, progress_reporter=bridge)
                if result.text:
                    await self._connection.session_update(
                        session_id=session_id,
                        update=acp.update_agent_message_text(result.text),
                    )
                for artifact in result.artifacts:
                    if artifact.kind == "image":
                        content = acp.image_block(
                            base64.b64encode(artifact.data).decode("ascii"),
                            artifact.mime_type,
                        )
                    elif artifact.kind == "audio":
                        content = acp.audio_block(
                            base64.b64encode(artifact.data).decode("ascii"),
                            artifact.mime_type,
                        )
                    else:
                        continue
                    await self._connection.session_update(
                        session_id=session_id,
                        update=acp.update_agent_message(content),
                    )
                if not result.text and not result.artifacts:
                    await self._connection.session_update(
                        session_id=session_id,
                        update=acp.update_agent_message_text("Frontier 已完成，但没有生成响应。"),
                    )
                return acp.PromptResponse(stop_reason="end_turn")
            except asyncio.CancelledError:
                return acp.PromptResponse(stop_reason="cancelled")
            except acp.RequestError:
                raise
            except Exception as exc:
                logger.exception("Frontier ACP session failed: %s", type(exc).__name__)
                raise acp.RequestError.internal_error({"type": type(exc).__name__}) from exc
            finally:
                session.active_task = None
                session.updated_at = dt.datetime.now(dt.UTC)

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        del kwargs
        session = self._sessions.get(session_id)
        if session is not None and session.active_task is not None:
            session.active_task.cancel()

    async def close_session(self, session_id: str, **kwargs: Any) -> Any:
        del kwargs
        session = self._sessions.pop(session_id, None)
        if session is None:
            raise acp.RequestError.resource_not_found(session_id)
        if session.active_task is not None:
            session.active_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await session.active_task
        return acp.schema.CloseSessionResponse()

    async def load_session(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise acp.RequestError.method_not_found("session/load")

    async def fork_session(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise acp.RequestError.method_not_found("session/fork")

    async def resume_session(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise acp.RequestError.method_not_found("session/resume")

    async def set_session_mode(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise acp.RequestError.method_not_found("session/set_mode")

    async def set_config_option(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise acp.RequestError.method_not_found("session/set_config_option")

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        del params
        raise acp.RequestError.method_not_found(method)

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        del params
        raise acp.RequestError.method_not_found(method)


async def run_frontier_acp_server() -> None:
    await acp.run_agent(FrontierAcpServer())


def main() -> None:
    asyncio.run(run_frontier_acp_server())


if __name__ == "__main__":
    main()


__all__ = ["FrontierAcpServer", "main", "run_frontier_acp_server"]
