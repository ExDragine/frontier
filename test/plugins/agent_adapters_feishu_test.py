"""Contract tests for the dependency-free Feishu text facade."""

# ruff: noqa: S101

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from plugins.agent.adapters.feishu import (
    FeishuDelivery,
    FeishuHistoryStore,
    FeishuMessageAdapter,
    FeishuReplyPolicy,
    FeishuTextGateway,
    FeishuToolProvider,
)
from utils.agent_protocol import (
    AgentArtifact,
    AgentResponse,
    ChatMessage,
    ConversationRef,
    DeliveryReceipt,
    DeliveryStatus,
    HistoryQuery,
    InboundMessage,
    MessageRef,
    Participant,
    TextPart,
)


def _group() -> ConversationRef:
    return ConversationRef(
        platform="feishu",
        account_id="app-1",
        kind="group",
        conversation_id="oc_group",
        tenant_id="tenant-1",
    )


def _direct() -> ConversationRef:
    return ConversationRef(
        platform="feishu",
        account_id="app-1",
        kind="direct",
        conversation_id="ou_user",
        tenant_id="tenant-1",
    )


def test_feishu_message_adapter_normalizes_string_identity_and_text_only_payload():
    adapter = FeishuMessageAdapter("app-1")
    message = adapter.text_message(
        message_id="om-1",
        tenant_id="tenant-1",
        chat_id="oc_group",
        chat_type="group",
        user_id="ou-user",
        user_name="Alice",
        text="hello",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        mentions_agent=True,
        metadata={"event_type": "im.message.receive_v1"},
    )

    assert message.message_id == "om-1"
    assert message.conversation == _group()
    assert message.sender == Participant(id="ou-user", display_name="Alice")
    assert message.parts == (TextPart("hello"),)
    assert message.mentions_agent is True
    assert message.metadata["event_type"] == "im.message.receive_v1"


def test_feishu_message_adapter_maps_chat_types_and_rejects_unknown_type():
    adapter = FeishuMessageAdapter("app-1")
    assert adapter.conversation(tenant_id="tenant-1", chat_id="ou-user", chat_type="p2p").kind == "direct"
    assert adapter.conversation(tenant_id="tenant-1", chat_id="oc-chat", chat_type="group").kind == "group"
    assert adapter.conversation(
        tenant_id="tenant-1", chat_id="oc-chat", chat_type="topic", parent_id="om-root"
    ).kind == "thread"
    with pytest.raises(ValueError, match="unsupported Feishu chat type"):
        adapter.conversation(tenant_id="tenant-1", chat_id="oc-chat", chat_type="unknown")


def test_feishu_message_adapter_maps_generic_history_rows_without_platform_objects():
    message = FeishuMessageAdapter.chat_message(
        {
            "role": "ai",
            "id": "om-2",
            "content": "reply",
            "time": 1_000,
            "sender": {"id": "app-1", "name": "Bot"},
        },
        conversation=_direct(),
    )

    assert message == ChatMessage(
        role="assistant",
        content="reply",
        message_id="om-2",
        conversation=_direct(),
        sender=Participant(id="app-1", display_name="Bot", role="assistant"),
        created_at=datetime(1970, 1, 1, 0, 16, 40, tzinfo=UTC),
    )


def test_feishu_message_adapter_parses_v2_text_event_without_leaking_payload():
    adapter = FeishuMessageAdapter("app-1")
    message = adapter.from_event(
        {
            "header": {"event_id": "evt-1", "tenant_key": "tenant-1", "token": "secret"},
            "event": {
                "sender": {"sender_id": {"open_id": "ou-user"}, "sender_type": "user"},
                "message": {
                    "message_id": "om-1",
                    "chat_id": "oc-group",
                    "chat_type": "group",
                    "message_type": "text",
                    "content": '{"text":"hello"}',
                    "create_time": "1700000000000",
                    "parent_id": "om-root",
                    "mentions": [{"id": {"open_id": "ou-bot"}, "name": "Frontier"}],
                },
            },
        },
        bot_open_id="ou-bot",
    )

    assert message.message_id == "om-1"
    assert message.conversation == ConversationRef(
        platform="feishu",
        account_id="app-1",
        kind="group",
        conversation_id="oc-group",
        tenant_id="tenant-1",
    )
    assert message.sender.id == "ou-user"
    assert message.parts == (TextPart("hello"),)
    assert message.mentions_agent is True
    assert message.reply_to == MessageRef(
        platform="feishu", conversation=message.conversation, message_id="om-root"
    )
    assert "token" not in message.metadata


@pytest.mark.asyncio
async def test_feishu_reply_policy_rejects_reply_until_thread_support_is_enabled():
    message = InboundMessage(
        message_id="om-reply",
        conversation=_direct(),
        sender=Participant(id="ou-user", display_name="Alice"),
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
        reply_to=MessageRef(platform="feishu", conversation=_direct(), message_id="om-root"),
    )
    decision = await FeishuReplyPolicy().decide(message, ())
    assert decision.should_reply is False
    assert decision.reason == "reply_not_supported"


@pytest.mark.asyncio
async def test_feishu_reply_policy_rejects_thread_messages_in_text_mvp():
    thread = ConversationRef(
        platform="feishu",
        account_id="app-1",
        kind="thread",
        conversation_id="oc-group",
        tenant_id="tenant-1",
        parent_id="om-root",
    )
    message = InboundMessage(
        message_id="om-thread",
        conversation=thread,
        sender=Participant(id="ou-user", display_name="Alice"),
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
        mentions_agent=True,
    )
    decision = await FeishuReplyPolicy().decide(message, ())
    assert decision.should_reply is False
    assert decision.reason == "thread_not_supported"


@pytest.mark.asyncio
async def test_feishu_history_store_scopes_load_and_append_to_tenant_chat():
    loaded = []
    appended = []

    async def loader(query):
        loaded.append(query)
        return [
            {"role": "user", "content": "before", "time": 1_000},
            {"role": "assistant", "content": "after", "time": 2_000},
        ]

    async def appender(message):
        appended.append(message)

    store = FeishuHistoryStore(loader=loader, appender=appender)
    messages = await store.load(HistoryQuery(conversation=_group(), limit=1))
    assert [item.content for item in messages] == ["before"]
    assert loaded[0].conversation == _group()
    current = ChatMessage(
        role="assistant",
        content="done",
        conversation=_group(),
        sender=Participant(id="app-1", display_name="Bot", role="assistant"),
    )
    await store.append(current)
    assert appended == [current]


@pytest.mark.asyncio
async def test_feishu_memory_history_keeps_newest_bounded_turns():
    store = FeishuHistoryStore()
    for index in range(3):
        await store.append(
            ChatMessage(
                role="assistant",
                content=f"reply-{index}",
                conversation=_direct(),
                sender=Participant(id="app-1", display_name="Bot", role="assistant"),
                created_at=datetime(2026, 1, 1, 0, index, tzinfo=UTC),
            )
        )

    messages = await store.load(HistoryQuery(conversation=_direct(), limit=2))
    assert [item.content for item in messages] == ["reply-1", "reply-2"]


@pytest.mark.asyncio
async def test_feishu_delivery_sends_text_and_maps_message_reference():
    calls = []

    async def send_text(target, text):
        calls.append((target, text))
        return {"success": True, "message_id": "om-reply"}

    receipt = await FeishuDelivery(text_sender=send_text).send(_group(), AgentResponse(text="done"))
    assert receipt == DeliveryReceipt(
        DeliveryStatus.DELIVERED,
        message_refs=(
            MessageRef(platform="feishu", conversation=_group(), message_id="om-reply"),
        ),
    )
    assert calls == [(_group(), "done")]


@pytest.mark.asyncio
async def test_feishu_delivery_rejects_artifacts_and_empty_text_without_sending():
    calls = []

    async def send_text(*args):
        calls.append(args)
        return True

    delivery = FeishuDelivery(text_sender=send_text)
    artifact_receipt = await delivery.send(
        _group(),
        AgentResponse(text="done", artifacts=(AgentArtifact(kind="image", data=b"x", mime_type="image/png"),)),
    )
    empty_receipt = await delivery.send(_group(), AgentResponse(text="  "))
    assert artifact_receipt.status == DeliveryStatus.FAILED
    assert artifact_receipt.errors == ("feishu_text_only_artifact",)
    assert empty_receipt.errors == ("empty_response",)
    assert calls == []


@pytest.mark.asyncio
async def test_feishu_reply_policy_is_conservative_for_groups_and_allows_direct_messages():
    direct = InboundMessage(
        message_id="om-direct",
        conversation=_direct(),
        sender=Participant(id="ou-user", display_name="Alice"),
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
    )
    group = InboundMessage(
        message_id="om-group",
        conversation=_group(),
        sender=Participant(id="ou-user", display_name="Alice"),
        created_at=datetime.now(UTC),
        parts=(TextPart("hello"),),
    )
    assert (await FeishuReplyPolicy().decide(direct, ())).should_reply is True
    assert (await FeishuReplyPolicy().decide(group, ())).should_reply is False
    mentioned = replace(group, mentions_agent=True)
    assert (await FeishuReplyPolicy().decide(mentioned, ())).should_reply is True


def test_feishu_tool_provider_is_empty_by_default_and_only_returns_injected_tools_with_capability():
    tool = object()
    provider = FeishuToolProvider((tool,))
    assert provider.tools(frozenset()) == ()
    assert provider.tools(frozenset({"platform:qq"})) == ()
    assert provider.tools(frozenset({"feishu:message"})) == (tool,)


@pytest.mark.asyncio
async def test_feishu_text_gateway_runs_once_and_deduplicates_webhook_retries():
    class Core:
        def __init__(self):
            self.requests = []

        async def run(self, request, *, tools=()):
            self.requests.append((request, tuple(tools)))
            return AgentResponse(text="reply")

    sent = []

    async def send_text(target, text):
        sent.append((target, text))
        return {"success": True, "message_id": "om-reply"}

    event = {
        "header": {"event_id": "evt-1", "tenant_key": "tenant-1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou-user"}},
            "message": {
                "message_id": "om-1",
                "chat_id": "ou-user",
                "chat_type": "p2p",
                "message_type": "text",
                "content": '{"text":"hello"}',
                "create_time": "1700000000000",
            },
        },
    }
    core = Core()
    gateway = FeishuTextGateway(
        core=core,
        history=FeishuHistoryStore(),
        delivery=FeishuDelivery(text_sender=send_text),
        account_id="app-1",
    )

    first = await gateway.handle_event(event)
    duplicate = await gateway.handle_event(event)

    assert first is not None and first.status.value == "delivered"
    assert duplicate is None
    assert len(core.requests) == 1
    assert sent == [(first.request.current.conversation, "reply")]


@pytest.mark.asyncio
async def test_feishu_gateway_allows_retry_after_pre_agent_history_failure():
    class History:
        def __init__(self):
            self.calls = 0

        async def load(self, query):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary history failure")
            return []

        async def append(self, message):
            return None

    class Core:
        async def run(self, request, *, tools=()):
            return AgentResponse(text="reply")

    event = {
        "header": {"event_id": "evt-retry", "tenant_key": "tenant-1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou-user"}},
            "message": {
                "message_id": "om-retry",
                "chat_id": "ou-user",
                "chat_type": "p2p",
                "message_type": "text",
                "content": '{"text":"hello"}',
            },
        },
    }
    gateway = FeishuTextGateway(
        core=Core(),
        history=History(),
        delivery=FeishuDelivery(text_sender=lambda *_args: True),
        account_id="app-1",
    )

    first = await gateway.handle_event(event)
    second = await gateway.handle_event(event)
    assert first is not None and first.status.value == "history_failed"
    assert second is not None and second.status.value == "delivered"
