# ruff: noqa: S101

import asyncio
import base64

import acp
import pytest

from utils.agents.acp.server import FrontierAcpServer
from utils.agents.progress import ProgressEvent
from utils.agents.runtime_gateway import (
    AgentRuntimeMedia,
    AgentRuntimeRequest,
    AgentRuntimeResult,
    FrontierAgentRuntime,
)


class _Connection:
    def __init__(self):
        self.updates = []

    async def session_update(self, *, session_id, update):
        self.updates.append((session_id, update))


class _Runtime:
    def __init__(self):
        self.requests = []

    async def prompt(self, request, *, progress_reporter=None):
        self.requests.append(request)
        await progress_reporter(ProgressEvent(type="thinking", message="raw thought must not leak"))
        await progress_reporter(
            ProgressEvent(
                type="tool_call",
                message="正在读取资料",
                detail={"tool_name": "read_file"},
            )
        )
        await progress_reporter(
            ProgressEvent(
                type="tool_result",
                message="资料读取完成",
                detail={"tool_name": "read_file", "success": True},
            )
        )
        return AgentRuntimeResult(
            text="final answer",
            artifacts=(AgentRuntimeMedia("image", b"image", "image/png"),),
        )


@pytest.mark.asyncio
async def test_frontier_acp_server_runs_runtime_and_streams_safe_updates(tmp_path):
    runtime = _Runtime()
    connection = _Connection()
    server = FrontierAcpServer(runtime)
    server.on_connect(connection)

    initialized = await server.initialize(acp.PROTOCOL_VERSION)
    created = await server.new_session(str(tmp_path))
    response = await server.prompt(
        created.session_id,
        [
            acp.text_block("inspect this"),
            acp.image_block(base64.b64encode(b"input").decode(), "image/png"),
        ],
    )

    assert initialized.protocol_version == acp.PROTOCOL_VERSION
    assert initialized.agent_capabilities.prompt_capabilities.image is True
    assert response.stop_reason == "end_turn"
    assert runtime.requests[0].prompt == "inspect this"
    assert runtime.requests[0].images[0].data == b"input"
    updates = [update for _session_id, update in connection.updates]
    assert [update.session_update for update in updates] == [
        "agent_thought_chunk",
        "tool_call",
        "tool_call_update",
        "agent_message_chunk",
        "agent_message_chunk",
    ]
    assert updates[0].content.text == "Frontier 正在处理请求…"
    assert "raw thought" not in str(updates)
    assert updates[-2].content.text == "final answer"
    assert base64.b64decode(updates[-1].content.data) == b"image"

    listed = await server.list_sessions(cwd=str(tmp_path))
    assert [item.session_id for item in listed.sessions] == [created.session_id]


@pytest.mark.asyncio
async def test_frontier_acp_server_cancels_active_prompt(tmp_path):
    started = asyncio.Event()

    class BlockingRuntime:
        async def prompt(self, _request, *, progress_reporter=None):
            del progress_reporter
            started.set()
            await asyncio.Event().wait()

    server = FrontierAcpServer(BlockingRuntime())
    server.on_connect(_Connection())
    created = await server.new_session(str(tmp_path))
    task = asyncio.create_task(server.prompt(created.session_id, [acp.text_block("wait")]))
    await started.wait()

    await server.cancel(created.session_id)
    response = await task

    assert response.stop_reason == "cancelled"


@pytest.mark.asyncio
async def test_frontier_acp_server_rejects_untrusted_workspace_extensions(tmp_path):
    server = FrontierAcpServer(_Runtime())

    with pytest.raises(acp.RequestError):
        await server.new_session(str(tmp_path), additional_directories=[str(tmp_path / "other")])

    with pytest.raises(acp.RequestError):
        await server.new_session("relative/path")


@pytest.mark.asyncio
async def test_runtime_gateway_applies_restricted_acp_profile():
    captured = {}

    class Cognitive:
        async def chat_agent(self, messages, **kwargs):
            captured["messages"] = messages
            captured["kwargs"] = kwargs
            artifact = type(
                "Artifact",
                (),
                {"type": "image", "raw": b"result-image", "mimetype": "image/png"},
            )()
            response = type("Message", (), {"content": "answer"})()
            return {
                "response": {"messages": [response]},
                "uni_messages": [[artifact]],
            }

    runtime = FrontierAgentRuntime(Cognitive())
    result = await runtime.prompt(
        AgentRuntimeRequest(
            session_id="session-1",
            prompt="inspect",
            images=(AgentRuntimeMedia("image", b"input-image", "image/png"),),
        )
    )

    assert captured["kwargs"]["access_profile"] == "acp"
    assert captured["kwargs"]["enable_acp_subagents"] is False
    assert captured["kwargs"]["user_id"] == "acp-session-1"
    assert [block["type"] for block in captured["messages"][0]["content"]] == [
        "text",
        "image",
    ]
    assert result.text == "answer"
    assert result.artifacts[0].data == b"result-image"
