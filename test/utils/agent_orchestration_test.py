"""Focused tests for the platform-neutral application orchestration layer."""

# ruff: noqa: S101

from datetime import UTC, datetime

import pytest

from utils.agent_orchestration import ConversationOrchestrator, TurnStatus
from utils.agent_protocol import (
    AgentArtifact,
    AgentResponse,
    ChatMessage,
    ConversationRef,
    DeliveryReceipt,
    DeliveryStatus,
    GateDecision,
    InboundMessage,
    MessageRef,
    Participant,
    TextPart,
)


@pytest.fixture
def message() -> InboundMessage:
    conversation = ConversationRef(
        platform="feishu",
        account_id="bot-1",
        tenant_id="tenant-1",
        kind="chat",
        conversation_id="chat-1",
    )
    return InboundMessage(
        message_id="in-1",
        conversation=conversation,
        sender=Participant(id="user-1", display_name="Alice"),
        created_at=datetime(2026, 9, 25, 12, 0, tzinfo=UTC),
        parts=(TextPart("hello"),),
    )


class FakeHistory:
    def __init__(self) -> None:
        self.loaded_queries = []
        self.appended: list[ChatMessage] = []

    async def load(self, query):
        self.loaded_queries.append(query)
        return [ChatMessage(role="user", content="previous")]

    async def append(self, message):
        self.appended.append(message)


class FakePolicy:
    def __init__(self, should_reply: bool) -> None:
        self.should_reply = should_reply
        self.calls = []

    async def decide(self, message, history):
        self.calls.append((message, tuple(history)))
        return GateDecision(self.should_reply, reason="test")


class FakeTools:
    def __init__(self) -> None:
        self.capabilities = None

    def tools(self, capabilities):
        self.capabilities = capabilities
        return ["weather-tool"]


class FakeCore:
    def __init__(self) -> None:
        self.requests = []
        self.tools = []

    async def run(self, request, *, tools=()):
        self.requests.append(request)
        self.tools.append(tuple(tools))
        return AgentResponse(text="hi", run_id="run-1")


class FailedCore(FakeCore):
    async def run(self, request, *, tools=()):
        self.requests.append(request)
        self.tools.append(tuple(tools))
        return AgentResponse(
            text="temporary failure",
            status="failed",
            should_reply=False,
            run_id="run-failed",
        )


class FakeDelivery:
    def __init__(self, status: DeliveryStatus) -> None:
        self.status = status
        self.calls = []

    async def send(self, target, response):
        self.calls.append((target, response))
        return DeliveryReceipt(status=self.status)


class MultiMessageDelivery(FakeDelivery):
    async def send(self, target, response):
        self.calls.append((target, response))
        return DeliveryReceipt(
            status=DeliveryStatus.DELIVERED,
            message_refs=(
                MessageRef(platform=target.platform, conversation=target, message_id="attachment-1"),
                MessageRef(platform=target.platform, conversation=target, message_id="text-1"),
            ),
        )


@pytest.mark.asyncio
async def test_gate_rejection_stops_before_agent_and_delivery(message):
    history = FakeHistory()
    policy = FakePolicy(False)
    core = FakeCore()
    delivery = FakeDelivery(DeliveryStatus.DELIVERED)

    outcome = await ConversationOrchestrator(core, request_id_factory=lambda: "req-1").handle(
        message,
        policy=policy,
        history=history,
        delivery=delivery,
    )

    assert outcome.status is TurnStatus.GATED
    assert outcome.request_id == "req-1"
    assert len(policy.calls) == 1
    assert core.requests == []
    assert delivery.calls == []
    assert history.appended == []


@pytest.mark.asyncio
async def test_success_passes_workspace_and_capabilities_and_appends_after_delivery(message):
    history = FakeHistory()
    core = FakeCore()
    tools = FakeTools()
    delivery = FakeDelivery(DeliveryStatus.DELIVERED)
    capabilities = frozenset({"feishu.send_file", "weather.read"})

    outcome = await ConversationOrchestrator(core, request_id_factory=lambda: "req-2").handle(
        message,
        policy=FakePolicy(True),
        history=history,
        delivery=delivery,
        tools=tools,
        workspace_key="tenant-1:chat-1",
        capabilities=capabilities,
        execution_profile="feishu",
    )

    assert outcome.status is TurnStatus.DELIVERED
    assert outcome.history_appended is True
    assert core.requests[0].workspace_key == "tenant-1:chat-1"
    assert core.requests[0].capabilities == capabilities
    assert core.requests[0].execution_profile == "feishu"
    assert tools.capabilities == capabilities
    assert core.tools == [("weather-tool",)]
    assert len(delivery.calls) == 1
    assert len(history.appended) == 1
    assert history.appended[0].role == "assistant"
    assert history.appended[0].content == "hi"


@pytest.mark.asyncio
async def test_artifact_only_delivery_does_not_append_empty_assistant_history(message):
    class ArtifactCore(FakeCore):
        async def run(self, request, *, tools=()):
            return AgentResponse(
                text="",
                artifacts=(AgentArtifact(kind="image", data=b"x", mime_type="image/png"),),
            )

    history = FakeHistory()
    outcome = await ConversationOrchestrator(ArtifactCore()).handle(
        message,
        policy=FakePolicy(True),
        history=history,
        delivery=FakeDelivery(DeliveryStatus.DELIVERED),
    )

    assert outcome.status is TurnStatus.DELIVERED
    assert outcome.history_appended is False
    assert history.appended == []


@pytest.mark.asyncio
async def test_history_boundary_uses_final_delivery_message(message):
    history = FakeHistory()
    outcome = await ConversationOrchestrator(FakeCore()).handle(
        message,
        policy=FakePolicy(True),
        history=history,
        delivery=MultiMessageDelivery(DeliveryStatus.DELIVERED),
    )

    assert outcome.status is TurnStatus.DELIVERED
    assert history.appended[0].message_id == "text-1"


@pytest.mark.asyncio
async def test_invalid_core_response_is_reported_as_agent_failure(message):
    class InvalidCore:
        async def run(self, request, *, tools=()):
            return {"text": "not an AgentResponse"}

    outcome = await ConversationOrchestrator(InvalidCore()).handle(
        message,
        policy=FakePolicy(True),
        history=FakeHistory(),
        delivery=FakeDelivery(DeliveryStatus.DELIVERED),
    )

    assert outcome.status is TurnStatus.AGENT_FAILED
    assert outcome.error == "Agent Core returned an invalid response"


@pytest.mark.asyncio
async def test_failed_delivery_does_not_append_assistant_history(message):
    history = FakeHistory()
    outcome = await ConversationOrchestrator(FakeCore()).handle(
        message,
        policy=FakePolicy(True),
        history=history,
        delivery=FakeDelivery(DeliveryStatus.FAILED),
    )

    assert outcome.status is TurnStatus.DELIVERY_FAILED
    assert outcome.history_appended is False
    assert history.appended == []


@pytest.mark.asyncio
async def test_failed_agent_status_is_not_misclassified_as_silent(message):
    history = FakeHistory()
    delivery = FakeDelivery(DeliveryStatus.DELIVERED)

    outcome = await ConversationOrchestrator(FailedCore()).handle(
        message,
        policy=FakePolicy(True),
        history=history,
        delivery=delivery,
    )

    assert outcome.status is TurnStatus.AGENT_FAILED
    assert delivery.calls == []
    assert history.appended == []


@pytest.mark.asyncio
async def test_explicit_workspace_key_is_normalized_before_agent_execution(message):
    core = FakeCore()

    outcome = await ConversationOrchestrator(core).handle(
        message,
        policy=FakePolicy(True),
        history=FakeHistory(),
        delivery=FakeDelivery(DeliveryStatus.DELIVERED),
        workspace_key="tenant/../chat",
    )

    assert outcome.status is TurnStatus.DELIVERED
    assert core.requests[0].workspace_key.startswith("workspace-h-")


@pytest.mark.asyncio
async def test_session_turn_is_forwarded_to_agent_request(message):
    history = FakeHistory()
    core = FakeCore()
    session_turn = object()

    outcome = await ConversationOrchestrator(core).handle(
        message,
        policy=FakePolicy(True),
        history=history,
        delivery=FakeDelivery(DeliveryStatus.DELIVERED),
        session_turn=session_turn,
    )

    assert outcome.status is TurnStatus.DELIVERED
    assert core.requests[0].session_turn is session_turn
