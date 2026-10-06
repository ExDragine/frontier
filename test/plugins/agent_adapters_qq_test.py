"""Focused contract tests for the incremental QQ adapter facade."""

# ruff: noqa: S101

import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from plugins.agent.adapters.qq import (
    QqDelivery,
    QqHistoryStore,
    QqMessageAdapter,
    QqReplyPolicy,
    QqToolProvider,
)
from utils.agent_protocol import (
    AgentArtifact,
    AgentResponse,
    AudioPart,
    ChatMessage,
    ConversationRef,
    DeliveryReceipt,
    DeliveryStatus,
    FilePart,
    HistoryQuery,
    ImagePart,
    InboundMessage,
    MessageRef,
    Participant,
    QuotePart,
    TextPart,
    VideoPart,
)


def _group() -> ConversationRef:
    return ConversationRef(platform="qq", account_id="42", kind="group", conversation_id="100")


def _direct() -> ConversationRef:
    return ConversationRef(platform="qq", account_id="42", kind="direct", conversation_id="7")


def test_qq_message_adapter_normalizes_identity_and_downloaded_media():
    reply = MessageRef(platform="qq", conversation=_group(), message_id="8")
    message = QqMessageAdapter("42").text_message(
        message_id=9,
        group_id=100,
        user_id=7,
        user_name="Alice",
        text="hello",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        role="member",
        mentions_agent=True,
        images=(b"image",),
        audio=(b"audio",),
        videos=(b"video",),
        reply_to=reply,
        metadata={"source": "test"},
    )

    assert message.message_id == "9"
    assert message.conversation == _group()
    assert message.sender == Participant(id="7", display_name="Alice", role="member")
    assert message.mentions_agent is True
    assert isinstance(message.parts[0], TextPart)
    assert isinstance(message.parts[1], ImagePart)
    assert isinstance(message.parts[2], AudioPart)
    assert isinstance(message.parts[3], VideoPart)
    assert message.reply_to == reply
    assert message.metadata == {"source": "test"}


def test_qq_message_adapter_maps_resolved_reply_snapshot_to_quote_parts():
    reply = MessageRef(platform="qq", conversation=_group(), message_id="8")
    message = QqMessageAdapter("42").text_message(
        message_id=9,
        group_id=100,
        user_id=7,
        user_name="Alice",
        text="follow up",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        reply_to=reply,
        quoted_payload={
            "message_id": "8",
            "content": "quoted",
            "attachments": [{"path": "/memory/quote.txt", "file_name": "quote.txt", "mime_type": "text/plain"}],
        },
        quoted_images=(b"quoted-image",),
    )

    quote = message.parts[-1]
    assert isinstance(quote, QuotePart)
    assert quote.message_ref == reply
    assert [type(part) for part in quote.parts] == [TextPart, ImagePart, FilePart]
    assert quote.parts[-1].url == "/memory/quote.txt"


def test_qq_message_adapter_maps_current_file_refs_to_file_parts():
    message = QqMessageAdapter("42").text_message(
        message_id=9,
        group_id=100,
        user_id=7,
        user_name="Alice",
        text="read this",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        attachments=(
            {"kind": "image", "path": "/memory/image.png"},
            {"kind": "file", "path": "/memory/report.txt", "file_name": "report.txt", "mime_type": "text/plain"},
        ),
    )

    assert [type(part) for part in message.parts] == [TextPart, FilePart]
    assert message.parts[-1].url == "/memory/report.txt"


def test_qq_message_adapter_maps_serialized_history_envelope_to_chat_message():
    payload = {
        "schema": "frontier.qq_message.v1",
        "time": "2026-09-27 10:11:12",
        "sender": {"user_id": "7", "display_name": "Alice", "role": "user"},
        "content": "hello",
        "message_id": "99",
    }
    raw = json.dumps(payload, ensure_ascii=False)
    message = QqMessageAdapter("42").chat_message(
        {"role": "user", "id": "legacy-row", "content": raw},
        conversation=_group(),
    )

    assert message.role == "user"
    assert message.message_id == "99"
    assert message.content == raw
    assert message.conversation == _group()
    assert message.sender == Participant(id="7", display_name="Alice", role="user")
    assert message.created_at == datetime(2026, 9, 27, 10, 11, 12, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert message.metadata["qq_payload"] == payload


def test_qq_message_adapter_maps_context_rows_and_keeps_history_order():
    adapter = QqMessageAdapter("42")
    messages = adapter.chat_messages(
        [
            {"role": "user", "content": "first", "time": 1_000},
            {"role": "assistant", "content": "second", "time": 2_000},
        ],
        conversation=_direct(),
    )

    assert [message.content for message in messages] == ["first", "second"]
    assert [message.created_at for message in messages] == [
        datetime(1970, 1, 1, 0, 16, 40, tzinfo=UTC),
        datetime(1970, 1, 1, 0, 33, 20, tzinfo=UTC),
    ]
    assert all(message.conversation == _direct() for message in messages)


def test_qq_message_adapter_normalizes_langchain_style_history_roles():
    class HistoryRow:
        type = "ai"
        content = "assistant reply"
        id = "run-1"

    message = QqMessageAdapter("42").chat_message(HistoryRow(), conversation=_direct())

    assert message.role == "assistant"
    assert message.message_id == "run-1"
    assert message.content == "assistant reply"


def test_qq_history_adapter_rebinds_existing_neutral_message_to_query_scope():
    other = ConversationRef(platform="qq", account_id="42", kind="group", conversation_id="999")
    message = QqMessageAdapter("42").chat_message(
        ChatMessage(role="user", content="hello", conversation=other),
        conversation=_group(),
    )

    assert message.conversation == _group()


@pytest.mark.asyncio
async def test_qq_history_store_maps_opaque_group_ids_and_appends_legacy_rows():
    class Database:
        def __init__(self):
            self.prepare_calls = []
            self.insert_calls = []

        async def prepare_message(self, **kwargs):
            self.prepare_calls.append(kwargs)
            return [{"id": 7, "role": "user", "content": "hello"}]

        async def insert(self, **kwargs):
            self.insert_calls.append(kwargs)

    database = Database()
    store = QqHistoryStore(database)
    messages = await store.load(HistoryQuery(conversation=_group(), limit=3))
    assert messages == [
        ChatMessage(role="user", content="hello", message_id="7", conversation=_group())
    ]
    assert database.prepare_calls == [{"user_id": None, "group_id": 100, "query_numbers": 3, "before_time": None}]

    await store.append(
        ChatMessage(
            role="assistant",
            content="reply",
            message_id="8",
            conversation=_group(),
            sender=Participant(id="42", display_name="Bot"),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    assert database.insert_calls[0]["group_id"] == 100
    assert database.insert_calls[0]["user_id"] == 42
    assert database.insert_calls[0]["bot_user_id"] == 42
    assert database.insert_calls[0]["sender_user_id"] == 42
    assert database.insert_calls[0]["normalized_status"] == "complete"


@pytest.mark.asyncio
async def test_qq_history_store_keeps_private_assistant_history_under_user_scope():
    class Database:
        async def insert(self, **kwargs):
            self.values = kwargs

    database = Database()
    await QqHistoryStore(database).append(
        ChatMessage(
            role="assistant",
            content="reply",
            conversation=_direct(),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    assert database.values["user_id"] == 7
    assert database.values["group_id"] is None
    assert database.values["bot_user_id"] == 42


@pytest.mark.asyncio
async def test_qq_history_store_accepts_sync_loader_and_applies_before_bound():
    rows = [
        {"role": "user", "content": "old", "time": 1_000},
        {"role": "user", "content": "new", "time": 3_000},
    ]
    store = QqHistoryStore(loader=lambda _query: rows)
    messages = await store.load(
        HistoryQuery(
            conversation=_direct(),
            limit=10,
            before=datetime.fromtimestamp(2_000, tz=UTC),
        )
    )

    assert [message.content for message in messages] == ["old"]


@pytest.mark.asyncio
async def test_qq_delivery_uses_injected_senders_and_reports_partial_artifact_failure():
    calls = []

    async def send_artifacts(target, artifacts):
        calls.append(("artifacts", target, tuple(artifacts)))
        return DeliveryReceipt(DeliveryStatus.FAILED, errors=("media_failed",))

    async def send_text(target, text):
        calls.append(("text", target, text))
        return DeliveryReceipt(DeliveryStatus.DELIVERED)

    delivery = QqDelivery(text_sender=send_text, artifact_sender=send_artifacts)
    receipt = await delivery.send(
        _group(),
        AgentResponse(
            text="done",
            artifacts=(AgentArtifact(kind="image", data=b"x", mime_type="image/png"),),
        ),
    )
    # The final text was delivered, so the turn is committed even when a
    # preceding media artifact reports a partial failure.
    assert receipt.status == DeliveryStatus.DELIVERED
    assert receipt.errors == ("media_failed",)
    assert [call[0] for call in calls] == ["artifacts", "text"]


@pytest.mark.asyncio
async def test_qq_delivery_accepts_sync_sender_and_mapping_receipts():
    delivery = QqDelivery(
        text_sender=lambda _target, _text: {"success": True, "message_id": "msg-1"},
    )

    receipt = await delivery.send(_group(), AgentResponse(text="done"))

    assert receipt.status is DeliveryStatus.DELIVERED
    assert receipt.message_refs[0].message_id == "msg-1"


@pytest.mark.asyncio
async def test_qq_delivery_does_not_commit_when_final_text_fails_after_artifact():
    async def send_artifacts(_target, _artifacts):
        return DeliveryReceipt(DeliveryStatus.DELIVERED, message_refs=())

    async def send_text(_target, _text):
        return DeliveryReceipt(DeliveryStatus.FAILED, errors=("text_failed",))

    receipt = await QqDelivery(text_sender=send_text, artifact_sender=send_artifacts).send(
        _group(),
        AgentResponse(
            text="done",
            artifacts=(AgentArtifact(kind="image", data=b"x", mime_type="image/png"),),
        ),
    )

    assert receipt.status is DeliveryStatus.FAILED
    assert receipt.errors == ("text_failed",)


@pytest.mark.asyncio
async def test_qq_delivery_converts_neutral_artifacts_at_platform_boundary(monkeypatch):
    sent = []

    async def capture(messages):
        sent.extend(messages)
        return DeliveryReceipt(DeliveryStatus.DELIVERED)

    from utils import message as message_module

    monkeypatch.setattr(message_module, "send_artifacts", capture)
    receipt = await QqDelivery().send(
        _group(),
        AgentResponse(
            text="",
            artifacts=(
                AgentArtifact(kind="image", data=b"image", mime_type="image/png"),
                AgentArtifact(kind="audio", data=b"", mime_type="audio/ogg", url="https://example.test/a.ogg"),
                AgentArtifact(kind="video", data=b"", mime_type="video/mp4", path="video.mp4"),
                AgentArtifact(kind="file", data=b"file", mime_type="text/plain", name="notes.txt"),
            ),
        ),
    )

    assert receipt.status is DeliveryStatus.DELIVERED
    assert [segment.type for message in sent for segment in message] == ["image", "audio", "video", "file"]
    assert sent[0][0].raw == b"image"
    assert sent[1][0].url == "https://example.test/a.ogg"
    assert sent[2][0].path == "video.mp4"
    assert sent[3][0].name == "notes.txt"


@pytest.mark.asyncio
async def test_qq_reply_policy_accepts_injected_gate_and_has_conservative_fallback():
    current = InboundMessage(
        message_id="1",
        conversation=_group(),
        sender=Participant(id="7", display_name="User"),
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
        mentions_agent=False,
    )
    seen = []

    async def gate(message, history):
        seen.append((message, tuple(history)))
        return True

    assert (await QqReplyPolicy(gate).decide(current, ())).should_reply is True
    assert seen == [(current, ())]
    assert (await QqReplyPolicy().decide(current, ())).should_reply is False


def test_qq_tool_provider_requires_platform_capability_and_filters_modules():
    class Tool:
        def __init__(self, name):
            self.name = name

    qq_tool = Tool("send_message")
    group_tool = Tool("ban_member")
    unrelated = Tool("weather")

    class Registry:
        direct_tools = (qq_tool, group_tool, unrelated)
        tool_metadata = {
            "send_message": {"module": "milky_message"},
            "ban_member": {"module": "milky_group"},
            "weather": {"module": "weather"},
        }

    provider = QqToolProvider(Registry())
    assert provider.tools(frozenset()) == ()
    assert provider.tools(frozenset({"qq:message"})) == (qq_tool,)
    assert provider.tools(frozenset({"qq"})) == (qq_tool, group_tool)
    assert provider.tools(frozenset({"platform:qq"})) == (qq_tool, group_tool)
