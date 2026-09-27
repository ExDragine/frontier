"""Contract tests for the neutral Agent Core compatibility bridge."""

# ruff: noqa: S101

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from utils.agent_protocol import (
    AgentRequest,
    AudioPart,
    ChatMessage,
    ConversationRef,
    ImagePart,
    InboundMessage,
    MessageRef,
    Participant,
    QuotePart,
    TextPart,
    VideoPart,
)
from utils.agents.neutral_core import FrontierAgentCore
from utils.agents.runtime_gateway import AgentRuntimeMedia, AgentRuntimeResult


@pytest.fixture
def agent_request() -> AgentRequest:
    conversation = ConversationRef(
        platform="feishu",
        account_id="bot-1",
        tenant_id="tenant-1",
        kind="chat",
        conversation_id="chat-1",
    )
    sender = Participant(id="user-1", display_name="Alice", role="member")
    return AgentRequest(
        request_id="request-1",
        current=InboundMessage(
            message_id="message-1",
            conversation=conversation,
            sender=sender,
            created_at=datetime(2026, 9, 27, tzinfo=UTC),
            parts=(
                TextPart("hello "),
                ImagePart(data=b"image-bytes", mime_type="image/png"),
                AudioPart(data=b"audio-bytes", mime_type="audio/ogg"),
                VideoPart(data=b"video-bytes", mime_type="video/mp4"),
                TextPart("world"),
            ),
        ),
        history=(ChatMessage(role="user", content="previous"),),
        workspace_key="feishu:tenant-1:chat-1",
        capabilities=frozenset({"feishu:message"}),
        execution_profile="frontier",
    )


class FakeRuntime:
    def __init__(self) -> None:
        self.requests = []
        self.tools = []

    async def run(self, runtime_request, *, tools=()):
        self.requests.append(runtime_request)
        self.tools.append(tuple(tools))
        return AgentRuntimeResult(
            text="reply",
            artifacts=(AgentRuntimeMedia("image", b"result", "image/png"),),
            run_id="run-1",
            usage={"input_tokens": 3},
        )


@pytest.mark.asyncio
async def test_bridge_maps_neutral_request_and_result(agent_request):
    runtime = FakeRuntime()
    response = await FrontierAgentCore(runtime).run(agent_request, tools=("tool-1",))

    runtime_request = runtime.requests[0]
    assert runtime.tools == [("tool-1",)]
    assert runtime_request.tool_overrides == ("tool-1",)
    assert runtime_request.prompt == "hello [image][audio][video]world"
    assert runtime_request.user_id == "user-1"
    assert runtime_request.user_name == "Alice"
    assert runtime_request.conversation == agent_request.current.conversation
    assert runtime_request.principal == agent_request.current.sender
    assert runtime_request.capabilities == frozenset({"feishu:message"})
    assert runtime_request.workspace_key == "feishu:tenant-1:chat-1"
    assert runtime_request.image_inputs == (b"image-bytes",)
    assert runtime_request.audio_inputs == (b"audio-bytes",)
    assert runtime_request.video_inputs == (b"video-bytes",)
    assert [item["role"] for item in runtime_request.messages] == ["user", "user"]
    assert response.text == "reply"
    assert response.run_id == "run-1"
    assert response.artifacts[0].data == b"result"
    assert response.should_reply is True


@pytest.mark.asyncio
async def test_bridge_keeps_media_nested_in_current_quote(agent_request):
    quote = QuotePart(
        message_ref=MessageRef(
            platform="feishu",
            conversation=agent_request.current.conversation,
            message_id="quoted-1",
        ),
        parts=(TextPart("quoted"), ImagePart(data=b"quoted-image", mime_type="image/png")),
    )
    request = replace(
        agent_request,
        current=replace(agent_request.current, parts=(TextPart("follow up"), quote)),
    )
    runtime = FakeRuntime()

    await FrontierAgentCore(runtime).run(request)

    runtime_request = runtime.requests[0]
    assert runtime_request.prompt == "follow up[引用: quoted[image]]"
    assert runtime_request.image_inputs == (b"quoted-image",)
    current_blocks = runtime_request.messages[-1]["content"]
    assert [block["type"] for block in current_blocks] == ["text", "text", "image"]


@pytest.mark.asyncio
async def test_bridge_preserves_session_message_boundaries(agent_request):
    history = ChatMessage(role="user", content="previous", message_id="history-1")
    request = replace(
        agent_request,
        history=(history,),
        session_turn=SimpleNamespace(current_id="qq:42:message:9"),
    )
    runtime = FakeRuntime()

    await FrontierAgentCore(runtime).run(request)

    messages = runtime.requests[0].messages
    assert messages[0]["id"] == "history-1"
    assert messages[-1]["id"] == "qq:42:message:9"


class MappingRuntime:
    async def run(self, runtime_agent_request):
        class Media:
            type = "image"
            raw = b"legacy-image"
            mimetype = "image/png"

        return {
            "response": {"messages": [{"content": "mapping reply"}]},
            "uni_messages": [Media()],
            "status": "success",
            "run_id": "run-mapping",
        }


@pytest.mark.asyncio
async def test_bridge_accepts_legacy_mapping_runtime_result(agent_request):
    response = await FrontierAgentCore(MappingRuntime()).run(agent_request)

    assert response.text == "mapping reply"
    assert response.run_id == "run-mapping"
    assert response.artifacts[0].kind == "image"
    assert response.artifacts[0].data == b"legacy-image"


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["video", "file"])
async def test_bridge_preserves_non_image_legacy_artifacts(agent_request, kind):
    class MappingRuntime:
        async def run(self, runtime_agent_request):
            class Media:
                type = kind
                raw = b"legacy-artifact"
                mimetype = "video/mp4" if kind == "video" else "text/plain"

            return {
                "response": {"messages": [{"content": "mapping reply"}]},
                "uni_messages": [Media()],
                "status": "success",
            }

    response = await FrontierAgentCore(MappingRuntime()).run(agent_request)

    assert len(response.artifacts) == 1
    assert response.artifacts[0].kind == kind
    assert response.artifacts[0].data == b"legacy-artifact"


class SilentRuntime:
    async def prompt(self, runtime_agent_request):
        return AgentRuntimeResult(text="", status="silent")


@pytest.mark.asyncio
async def test_bridge_preserves_silent_runtime_status(agent_request):
    response = await FrontierAgentCore(SilentRuntime()).run(agent_request)

    assert response.status == "silent"
    assert response.should_reply is False


class FailedRuntime:
    async def prompt(self, runtime_request):
        return AgentRuntimeResult(text="temporary failure", status="failed", error="RuntimeError")


@pytest.mark.asyncio
async def test_bridge_keeps_failed_status_visible_to_orchestrator(agent_request):
    response = await FrontierAgentCore(FailedRuntime()).run(agent_request)

    assert response.status == "failed"
    assert response.should_reply is True
