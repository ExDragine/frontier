# ruff: noqa: S101

import asyncio

import acp
import pytest
from acp.experimental.v2 import schema

from plugins.acp.client_v2 import FrontierAcpV2Client
from plugins.acp.server_v2 import FrontierAcpV2Server
from utils.agents.progress import ProgressEvent
from utils.agents.runtime_gateway import AgentRuntimeResult


class _Connection:
    def __init__(self):
        self.updates = []

    async def session_update(self, notification):
        self.updates.append(notification.update)


class _Runtime:
    def __init__(self):
        self.requests = []

    async def prompt(self, request, *, progress_reporter):
        self.requests.append(request)
        await progress_reporter(ProgressEvent(type="thinking", message="do not expose thoughts"))
        await progress_reporter(ProgressEvent(type="tool_call", message="Read", detail={"tool_name": "read"}))
        await progress_reporter(ProgressEvent(type="tool_result", message="Read done", detail={"tool_name": "read"}))
        return AgentRuntimeResult(text="answer")


@pytest.mark.asyncio
async def test_v2_prompt_ack_state_replay_and_resumed_context(tmp_path):
    runtime = _Runtime()
    server = FrontierAcpV2Server(runtime)
    connection = _Connection()
    server.on_connect(connection)
    initialized = await server.initialize(schema.InitializeRequest(
        protocol_version=2, info=schema.Implementation(name="test", version="1"),
    ))
    assert initialized.capabilities.session.prompt.image is not None
    created = await server.new_session(schema.NewSessionRequest(cwd=str(tmp_path)))
    response = await server.prompt(schema.PromptRequest(
        session_id=created.session_id, prompt=[schema.TextContentBlock(text="hello")],
    ))
    assert response.model_dump(exclude_none=True) == {}
    assert runtime.requests == []  # acceptance returns before execution begins
    await server._sessions[created.session_id].task
    kinds = [update.session_update for update in connection.updates]
    assert kinds == ["user_message", "state_update", "agent_thought_chunk", "tool_call_update",
                     "tool_call_update", "agent_message", "state_update"]
    assert connection.updates[1].state == "running"
    assert connection.updates[-1].state == "idle"
    assert connection.updates[-1].stop_reason == "end_turn"
    assert "do not expose thoughts" not in str(connection.updates)
    assert all(update.message_id for update in connection.updates if "message" in update.session_update)
    history = list(connection.updates)
    await server.close_session(schema.CloseSessionRequest(session_id=created.session_id))
    with pytest.raises(acp.RequestError):
        await server.prompt(schema.PromptRequest(session_id=created.session_id, prompt=[]))
    listed = await server.list_sessions(schema.ListSessionsRequest())
    assert [item.session_id for item in listed.sessions] == [created.session_id]
    await server.resume_session(schema.ResumeSessionRequest(session_id=created.session_id, cwd=str(tmp_path)))
    assert connection.updates == history
    await server.resume_session(schema.ResumeSessionRequest(
        session_id=created.session_id, cwd=str(tmp_path), replay_from=schema.ReplayFromStartVariant(),
    ))
    assert connection.updates == history * 2
    await server.prompt(schema.PromptRequest(
        session_id=created.session_id, prompt=[schema.TextContentBlock(text="continue")],
    ))
    await server._sessions[created.session_id].task
    assert [message["role"] for message in runtime.requests[-1].messages] == ["user", "assistant", "user"]


@pytest.mark.asyncio
@pytest.mark.parametrize("immediate", [True, False])
async def test_v2_cancel_confirms_idle_and_rejects_concurrent_prompt(tmp_path, immediate):
    started = asyncio.Event()

    class BlockingRuntime:
        async def prompt(self, *_args, **_kwargs):
            started.set()
            await asyncio.Event().wait()

    server = FrontierAcpV2Server(BlockingRuntime())
    connection = _Connection()
    server.on_connect(connection)
    created = await server.new_session(schema.NewSessionRequest(cwd=str(tmp_path)))
    request = schema.PromptRequest(session_id=created.session_id, prompt=[schema.TextContentBlock(text="wait")])
    await server.prompt(request)
    with pytest.raises(acp.RequestError):
        await server.prompt(request)
    if not immediate:
        await asyncio.wait_for(started.wait(), timeout=1)
    await asyncio.wait_for(server.cancel_session(schema.CancelSessionNotification(session_id=created.session_id)), 1)
    assert connection.updates[-1].state == "idle"
    assert connection.updates[-1].stop_reason == "cancelled"
    assert server._sessions[created.session_id].task is None


@pytest.mark.asyncio
async def test_v2_runtime_error_is_sanitized_and_completes(tmp_path):
    class FailedRuntime:
        async def prompt(self, *_args, **_kwargs):
            raise RuntimeError("secret-value-must-not-be-sent")

    server = FrontierAcpV2Server(FailedRuntime())
    connection = _Connection()
    server.on_connect(connection)
    created = await server.new_session(schema.NewSessionRequest(cwd=str(tmp_path)))
    await server.prompt(schema.PromptRequest(session_id=created.session_id, prompt=[schema.TextContentBlock(text="run")]))
    await server._sessions[created.session_id].task
    assert connection.updates[-1].stop_reason == "refusal"
    assert "secret-value" not in str(connection.updates)


@pytest.mark.asyncio
async def test_v2_client_upserts_chunks_clear_and_completion():
    client = FrontierAcpV2Client(acp, "deny")
    client.session_id = "s"
    client.begin_turn(None)

    async def update(raw, session_id="s"):
        await client.session_update(schema.UpdateSessionNotification.model_validate({"sessionId": session_id, "update": raw}))

    await update({"sessionUpdate": "agent_message", "messageId": "a", "content": [{"type": "text", "text": "old"}]})
    await update({"sessionUpdate": "agent_message_chunk", "messageId": "b", "content": {"type": "text", "text": "second"}})
    await update({"sessionUpdate": "agent_message", "messageId": "a", "content": [{"type": "text", "text": "new"}]})
    await update({"sessionUpdate": "agent_message_chunk", "messageId": "a", "content": {"type": "text", "text": "!"}})
    await update({"sessionUpdate": "agent_message", "messageId": "a"})  # omitted leaves content untouched
    await update({"sessionUpdate": "agent_message", "messageId": "b", "content": None})
    await update({"sessionUpdate": "state_update", "state": "idle"})
    assert not client.completed.is_set()
    await update({"sessionUpdate": "state_update", "state": "idle", "stopReason": "end_turn"}, session_id="other")
    assert not client.completed.is_set()
    await update({"sessionUpdate": "state_update", "state": "idle", "stopReason": "end_turn"})
    assert client.completed.is_set()
    await update({"sessionUpdate": "agent_message", "messageId": "background", "content": [{"type": "text", "text": "ignore"}]})
    assert client.finish_turn() == ("new!", ())


@pytest.mark.asyncio
@pytest.mark.parametrize("policy,expected", [("deny", "cancelled"), ("allow_once", "selected"), ("allow_always", "selected")])
async def test_v2_permissions_obey_policy_and_cancellation(policy, expected):
    client = FrontierAcpV2Client(acp, policy)
    client.session_id = "s"
    client.begin_turn(None)
    request = schema.RequestPermissionRequest.model_validate({
        "sessionId": "s", "title": "Read?", "subject": {"type": "tool_call", "toolCall": {"toolCallId": "t"}},
        "options": [{"optionId": "yes", "name": "Allow", "kind": "allow_once"}],
    })
    assert (await client.request_permission(request)).outcome.outcome == expected
    client.cancel_requested = True
    assert (await client.request_permission(request)).outcome.outcome == "cancelled"


@pytest.mark.asyncio
async def test_v2_server_validates_resume_scope_and_request_before_ack(tmp_path):
    server = FrontierAcpV2Server(_Runtime())
    server.on_connect(_Connection())
    created = await server.new_session(schema.NewSessionRequest(cwd=str(tmp_path)))
    for request in (
        schema.ResumeSessionRequest(session_id=created.session_id, cwd=str(tmp_path / "other")),
        schema.ResumeSessionRequest(session_id=created.session_id, cwd=str(tmp_path), mcp_servers=[
            schema.StdioMcpServer(name="untrusted", command="untrusted"),
        ]),
    ):
        with pytest.raises(acp.RequestError):
            await server.resume_session(request)
    with pytest.raises(acp.RequestError):
        await server.prompt(schema.PromptRequest(session_id=created.session_id, prompt=[]))
    assert server._sessions[created.session_id].task is None
