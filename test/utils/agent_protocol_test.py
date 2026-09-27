"""Contract tests for the platform-neutral Agent protocol values."""

# ruff: noqa: S101

from datetime import UTC, datetime

import pytest

from utils.agent_protocol import (
    AgentArtifact,
    AgentRequest,
    AgentResponse,
    AudioPart,
    ChatMessage,
    ConversationRef,
    DeliveryPort,
    DeliveryReceipt,
    DeliveryStatus,
    FilePart,
    GateDecision,
    HistoryQuery,
    HistoryStore,
    ImagePart,
    InboundMessage,
    MentionPart,
    MessagePart,
    MessageRef,
    Participant,
    PlatformToolProvider,
    QuotePart,
    ReplyPolicy,
    TextPart,
    VideoPart,
)


@pytest.fixture
def conversation() -> ConversationRef:
    return ConversationRef(
        platform="feishu",
        account_id="bot-1",
        kind="thread",
        conversation_id="chat-1",
        tenant_id="tenant-1",
        parent_id="root-1",
    )


def test_message_values_keep_platform_ids_opaque(conversation: ConversationRef) -> None:
    participant = Participant(
        id="user-1",
        display_name="Alice",
        role="member",
        permissions=frozenset({"read"}),
    )
    reference = MessageRef(platform="feishu", conversation=conversation, message_id="msg-1")
    created_at = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
    parts: tuple[MessagePart, ...] = (
        TextPart("hello"),
        ImagePart(data=b"image", mime_type="image/png", name="a.png"),
        AudioPart(url="https://example.test/a.ogg", mime_type="audio/ogg"),
        VideoPart(data=b"video", mime_type="video/mp4"),
        FilePart(data=b"file", mime_type="text/plain", name="a.txt"),
        MentionPart(participant_id=participant.id, display_name=participant.display_name),
        QuotePart(message_ref=reference, parts=(TextPart("quoted"),)),
    )
    message = InboundMessage(
        message_id="msg-2",
        conversation=conversation,
        sender=participant,
        created_at=created_at,
        parts=parts,
        reply_to=reference,
        mentions_agent=True,
        metadata={"thread": "root-1"},
    )

    assert message.conversation.conversation_id == "chat-1"
    assert message.reply_to == reference
    assert isinstance(message.parts[0], TextPart)
    assert isinstance(message.parts[1], ImagePart)
    assert isinstance(message.parts[-1], QuotePart)
    assert message.parts[-1].message_ref == reference

    with pytest.raises(AttributeError):
        message.message_id = "changed"  # type: ignore[misc]


def test_agent_request_and_response_are_platform_neutral(conversation: ConversationRef) -> None:
    sender = Participant(id="user-1", display_name="Alice")
    current = InboundMessage(
        message_id="msg-1",
        conversation=conversation,
        sender=sender,
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
    )
    history = (ChatMessage(role="user", content="previous", conversation=conversation),)
    request = AgentRequest(
        request_id="request-1",
        current=current,
        history=history,
        workspace_key="feishu:tenant-1:thread:chat-1",
        capabilities=frozenset({"common.weather"}),
        execution_profile="frontier",
    )
    response = AgentResponse(
        text="hi",
        artifacts=(AgentArtifact(kind="file", data=b"data", mime_type="text/plain", name="x.txt"),),
        run_id="run-1",
        usage={"input_tokens": 2},
    )

    assert request.current is current
    assert request.workspace_key.startswith("feishu:")
    assert response.artifacts[0].mime_type == "text/plain"
    assert response.usage["input_tokens"] == 2
    assert AgentResponse(text="silent", should_reply=False).should_reply is False


def test_delivery_receipt_uses_explicit_status_and_opaque_message_refs(conversation: ConversationRef) -> None:
    reference = MessageRef(platform="feishu", conversation=conversation, message_id="sent-1")
    delivered = DeliveryReceipt(status=DeliveryStatus.DELIVERED, message_refs=(reference,))
    failed = DeliveryReceipt(status=DeliveryStatus.FAILED, errors=("transport",))
    unknown = DeliveryReceipt(status=DeliveryStatus.UNKNOWN)

    assert delivered.status == "delivered"
    assert delivered.message_refs == (reference,)
    assert failed.errors == ("transport",)
    assert unknown.status is DeliveryStatus.UNKNOWN


def test_port_protocols_are_usable_without_platform_sdk(conversation: ConversationRef) -> None:
    message = InboundMessage(
        message_id="msg-1",
        conversation=conversation,
        sender=Participant(id="user-1", display_name="Alice"),
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
    )

    class Policy:
        async def decide(self, _message, _history):
            return GateDecision(should_reply=True)

    class History:
        async def load(self, _query):
            return []

        async def append(self, _message):
            return None

    class Delivery:
        async def send(self, _target, _response):
            return DeliveryReceipt(status=DeliveryStatus.DELIVERED)

    class Tools:
        def tools(self, _capabilities):
            return []

    assert isinstance(Policy(), ReplyPolicy)
    assert isinstance(History(), HistoryStore)
    assert isinstance(Delivery(), DeliveryPort)
    assert isinstance(Tools(), PlatformToolProvider)
    assert Policy().decide is not None
    assert HistoryQuery(conversation=message.conversation).limit == 50
    assert GateDecision(should_reply=False).allowed is False
