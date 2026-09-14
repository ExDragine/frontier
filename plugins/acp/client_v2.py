"""ACP v2 Draft adaptation using the official SDK's experimental transport."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

from acp.experimental import v2
from acp.experimental.v2 import schema
from acp.transports import spawn_stdio_transport

from .service import AcpUnavailableError, _CollectedMessage, _FrontierAcpClient


class _V2Collector(_FrontierAcpClient):
    def _message(self, message_id: str | None) -> _CollectedMessage:
        for message in self._messages:
            if message.message_id == message_id:
                return message
        return super()._message(message_id)


class FrontierAcpV2Client:
    """Collect v2 message upserts and wait for foreground completion, not ACK."""

    def __init__(self, sdk: Any, permission_policy: Any) -> None:
        self._collector = _V2Collector(sdk, permission_policy)
        self.session_id: str | None = None
        self.completed = asyncio.Event()
        self.stop_reason = "end_turn"
        self.cancel_requested = False
        self._update_lock = asyncio.Lock()

    @property
    def active(self) -> bool:
        return self._collector.active

    def begin_turn(self, reporter: Any) -> None:
        self._collector.begin_turn(reporter)
        self.completed.clear()
        self.cancel_requested = False

    def finish_turn(self) -> Any:
        return self._collector.finish_turn()

    async def session_update(self, notification: schema.UpdateSessionNotification) -> None:
        async with self._update_lock:
            if notification.session_id != self.session_id or not self.active or self.completed.is_set():
                return
            update = notification.update
            kind = update.session_update
            if kind == "state_update":
                if update.state == "idle" and update.stop_reason is not None:
                    self.stop_reason = update.stop_reason
                    self.completed.set()
                return
            if kind == "agent_message":
                message = self._collector._message(update.message_id)
                if "content" in update.model_fields_set:
                    message.text_parts.clear()
                    message.artifacts.clear()
                    for block in update.content or []:
                        self._collector._collect_agent_message(SimpleNamespace(message_id=update.message_id, content=block))
                return
            if kind == "agent_thought":
                # Emit only the standard thinking notice, never raw reasoning.
                update = SimpleNamespace(session_update="agent_thought_chunk")
            if kind == "tool_call_update" and update.tool_call_id not in self._collector._tool_titles:
                await self._collector._handle_tool_start(update)
            await self._collector.session_update(notification.session_id, update)

    async def request_permission(self, request: schema.RequestPermissionRequest) -> schema.RequestPermissionResponse:
        if not self.active or self.cancel_requested or request.session_id != self.session_id:
            return schema.RequestPermissionResponse(outcome=schema.CancelledPermissionOutcome(outcome="cancelled"))
        # v2 moves toolCall into subject. The configured policy still selects
        # only known allow options, and requires no host filesystem access.
        result = await self._collector.request_permission(request.session_id, request.subject, request.options)
        return schema.RequestPermissionResponse.model_validate(result.model_dump(by_alias=True, exclude_none=True))

    async def create_elicitation(self, request: Any) -> Any:
        del request
        return schema.DeclineElicitationResponse(action="decline")


class _V2Connection:
    """Expose the existing service lifecycle over v2's typed connection API."""

    def __init__(self, connection: Any, client: FrontierAcpV2Client, process: Any) -> None:
        self.connection = connection
        self.client = client
        self.process = process

    async def initialize(self, *, protocol_version: int, client_info: Any, **kwargs: Any) -> Any:
        del kwargs
        response = await self.connection.initialize(schema.InitializeRequest(
            protocol_version=protocol_version,
            info=schema.Implementation.model_validate(client_info.model_dump(by_alias=True, exclude_none=True)),
            capabilities=schema.ClientCapabilities(),
        ))
        session = getattr(response.capabilities, "session", None)
        if session is None:
            raise AcpUnavailableError("ACP v2 Agent 未声明 session 能力")
        prompt = session.prompt
        return SimpleNamespace(
            protocol_version=response.protocol_version,
            agent_capabilities=SimpleNamespace(prompt_capabilities=SimpleNamespace(
                image=getattr(prompt, "image", None) is not None,
                audio=getattr(prompt, "audio", None) is not None,
            )),
            auth_methods=[
                SimpleNamespace(id=method.method_id)
                for method in response.auth_methods or [] if method.type == "agent"
            ],
        )

    async def authenticate(self, *, method_id: str) -> Any:
        return await self.connection.login(schema.LoginAuthRequest(method_id=method_id))

    async def new_session(self, *, cwd: str, mcp_servers: list[Any]) -> Any:
        result = await self.connection.new_session(schema.NewSessionRequest(cwd=cwd, mcp_servers=mcp_servers))
        self.client.session_id = result.session_id
        return result

    async def prompt(self, *, session_id: str, prompt: list[Any]) -> Any:
        await self.connection.prompt(schema.PromptRequest.model_validate({
            "sessionId": session_id,
            "prompt": [block.model_dump(by_alias=True, exclude_none=True) for block in prompt],
        }))
        completion = asyncio.create_task(self.client.completed.wait())
        exited = asyncio.create_task(self.process.wait())
        try:
            await asyncio.wait((completion, exited), return_when=asyncio.FIRST_COMPLETED)
            if not self.client.completed.is_set():
                raise AcpUnavailableError("ACP v2 Agent 在发送完成状态前退出")
            return SimpleNamespace(stop_reason=self.client.stop_reason)
        finally:
            completion.cancel()
            exited.cancel()
            await asyncio.gather(completion, exited, return_exceptions=True)

    async def cancel(self, *, session_id: str) -> None:
        self.client.cancel_requested = True
        await self.connection.cancel_session(schema.CancelSessionNotification(session_id=session_id))


@asynccontextmanager
async def spawn_v2_agent_process(client: FrontierAcpV2Client, command: str, *args: str, **kwargs: Any):
    async with spawn_stdio_transport(command, *args, **kwargs) as (reader, writer, process):
        async with v2.connect_to_agent(client, writer, reader) as connection:
            yield _V2Connection(connection, client, process), process
