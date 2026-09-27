"""Platform-neutral facades for a minimal Feishu text integration.

The module intentionally does not import the Feishu/Lark SDK.  A webhook or
long-connection entry point can pass a plain mapping to
:meth:`FeishuMessageAdapter.from_event`, and an SDK-specific sender can be
injected into :class:`FeishuDelivery`.  This keeps the P4 text loop testable
without credentials, network access, or a particular Feishu SDK version.

Only text messages are accepted by the event adapter.  Images, files, cards,
threads, and platform management tools stay outside this first facade.
"""

from __future__ import annotations

import inspect
import json
from collections import OrderedDict, defaultdict
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime

from utils.agent_orchestration import ConversationOrchestrator, TurnOutcome, workspace_key_for
from utils.agent_protocol import (
    AgentResponse,
    ChatMessage,
    ConversationRef,
    DeliveryReceipt,
    DeliveryStatus,
    GateDecision,
    HistoryQuery,
    InboundMessage,
    MessageRef,
    Participant,
    StoredMessage,
    TextPart,
)

FEISHU_PLATFORM = "feishu"
FEISHU_TEXT_CAPABILITIES = frozenset({"platform:feishu", "feishu:message"})
_DIRECT_CHAT_TYPES = frozenset({"p2p", "direct", "private", "user"})
_GROUP_CHAT_TYPES = frozenset({"group", "chat", "group_chat"})
_THREAD_CHAT_TYPES = frozenset({"topic", "thread", "topic_group"})


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _first(value: Mapping[str, object], *keys: str) -> object | None:
    for key in keys:
        candidate = value.get(key)
        if candidate is not None and candidate != "":
            return candidate
    return None


def _nested(mapping: Mapping[str, object], *keys: str) -> Mapping[str, object]:
    value: object = mapping
    for key in keys:
        value = _mapping(value).get(key)
    return _mapping(value)


def _coerce_datetime(value: object) -> datetime | None:
    """Parse Feishu webhook timestamps without depending on an SDK model."""

    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        timestamp = float(value)
        # Feishu sends create_time in milliseconds in some event versions and
        # seconds in others.  Handle both while preserving UTC explicitly.
        if abs(timestamp) > 10_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (OverflowError, OSError, ValueError):
            pass
    if isinstance(value, str) and value.strip():
        candidate = value.strip()
        if candidate.isdigit():
            return _coerce_datetime(float(candidate))
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            pass
        else:
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def _text_content(value: object) -> str:
    """Extract text from Feishu's JSON encoded ``message.content`` field."""

    if isinstance(value, Mapping):
        nested_text = _first(value, "text", "content")
        return "" if nested_text is None else str(nested_text)
    if value is None:
        return ""
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.startswith("{"):
            try:
                parsed = json.loads(candidate)
            except (TypeError, ValueError):
                pass
            else:
                if isinstance(parsed, Mapping):
                    nested_text = _first(parsed, "text", "content")
                    if nested_text is not None:
                        return str(nested_text)
        return value
    return str(value)


def _sender_id(sender: Mapping[str, object]) -> str | None:
    identity = _first(sender, "sender_id", "senderId", "user_id", "open_id", "id")
    identity_mapping = _mapping(identity)
    identity = _first(identity_mapping, "open_id", "user_id", "union_id", "id") or identity
    if identity is None:
        return None
    return str(identity)


def _sender_name(sender: Mapping[str, object], sender_id: str) -> str:
    name = _first(sender, "display_name", "name", "nickname")
    return str(name if name is not None else sender_id)


def _normalize_role(value: object) -> str:
    role = str(value or "user").lower()
    return {"human": "user", "ai": "assistant", "bot": "assistant"}.get(role, role)


def _as_chat_message(item: object, conversation: ConversationRef | None = None) -> ChatMessage:
    """Convert neutral or callback-provided history rows to ``ChatMessage``."""

    if isinstance(item, ChatMessage):
        if conversation is None or item.conversation == conversation:
            return item
        return ChatMessage(
            role=item.role,
            content=item.content,
            message_id=item.message_id,
            conversation=conversation,
            sender=item.sender,
            created_at=item.created_at,
            metadata=item.metadata,
        )
    row = _mapping(item)
    if row:
        role = _normalize_role(row.get("role", row.get("type", "user")))
        content = row.get("content", row.get("text", ""))
        message_id = _first(row, "message_id", "id")
        created_at = _coerce_datetime(_first(row, "created_at", "time", "create_time"))
        sender_value = _mapping(row.get("sender"))
        metadata = row.get("metadata", {})
    else:
        role = _normalize_role(getattr(item, "role", getattr(item, "type", "user")))
        content = getattr(item, "content", getattr(item, "text", ""))
        message_id = getattr(item, "message_id", getattr(item, "id", None))
        created_at = _coerce_datetime(
            getattr(item, "created_at", getattr(item, "time", getattr(item, "create_time", None)))
        )
        sender_value = _mapping(getattr(item, "sender", None))
        metadata = getattr(item, "metadata", {})
    sender = None
    if sender_value:
        identity = _sender_id(sender_value)
        if identity is not None:
            sender = Participant(id=identity, display_name=_sender_name(sender_value, identity), role=role)
    return ChatMessage(
        role=role,
        content=_text_content(content),
        message_id=None if message_id is None else str(message_id),
        conversation=conversation,
        sender=sender,
        created_at=created_at,
        metadata=dict(metadata) if isinstance(metadata, Mapping) else {},
    )


class FeishuMessageAdapter:
    """Normalize Feishu text events while keeping SDK objects out of core."""

    def __init__(self, account_id: str, *, tenant_id: str | None = None) -> None:
        self.account_id = str(account_id)
        self.tenant_id = tenant_id

    def conversation(
        self,
        *,
        chat_id: str,
        chat_type: str = "group",
        tenant_id: str | None = None,
        parent_id: str | None = None,
    ) -> ConversationRef:
        normalized = str(chat_type or "group").lower()
        if normalized in _DIRECT_CHAT_TYPES:
            kind = "direct"
        elif normalized in _GROUP_CHAT_TYPES:
            kind = "group"
        elif normalized in _THREAD_CHAT_TYPES:
            kind = "thread"
        else:
            raise ValueError(f"unsupported Feishu chat type {chat_type!r}")
        return ConversationRef(
            platform=FEISHU_PLATFORM,
            account_id=self.account_id,
            kind=kind,
            conversation_id=str(chat_id),
            tenant_id=self.tenant_id if tenant_id is None else str(tenant_id),
            parent_id=None if parent_id is None else str(parent_id),
        )

    @staticmethod
    def participant(*, user_id: str, display_name: str | None = None, role: str | None = None) -> Participant:
        identity = str(user_id)
        return Participant(id=identity, display_name=display_name or identity, role=role)

    def text_message(
        self,
        *,
        message_id: str,
        chat_id: str,
        sender_id: str | None = None,
        sender_name: str | None = None,
        user_id: str | None = None,
        user_name: str | None = None,
        text: str,
        created_at: datetime | int | float | str | None = None,
        chat_type: str = "group",
        tenant_id: str | None = None,
        parent_id: str | None = None,
        reply_to: MessageRef | None = None,
        mentions_agent: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> InboundMessage:
        sender_id = sender_id or user_id
        if sender_id is None:
            raise ValueError("Feishu text message requires sender_id")
        sender_name = sender_name or user_name
        conversation = self.conversation(
            chat_id=chat_id,
            chat_type=chat_type,
            tenant_id=tenant_id,
            parent_id=parent_id,
        )
        sender = self.participant(user_id=sender_id, display_name=sender_name)
        return InboundMessage(
            message_id=str(message_id),
            conversation=conversation,
            sender=sender,
            created_at=_coerce_datetime(created_at) or datetime.now(UTC),
            parts=(TextPart(str(text)),),
            reply_to=reply_to,
            mentions_agent=mentions_agent,
            metadata=dict(metadata or {}),
        )

    def from_event(
        self,
        event: Mapping[str, object],
        *,
        bot_open_id: str | None = None,
        mentions_agent: bool | None = None,
    ) -> InboundMessage:
        """Parse common Feishu webhook shapes using only mapping operations.

        The parser accepts both the v2 event envelope (``event.message`` and
        ``event.sender``) and a flattened message mapping used by tests or a
        custom webhook endpoint.  It deliberately rejects non-text messages.
        """

        root = _mapping(event)
        message = _nested(root, "event", "message") or _mapping(root.get("message")) or root
        sender = _nested(root, "event", "sender") or _mapping(root.get("sender"))
        message_type = str(_first(message, "message_type", "messageType", "type") or "text").lower()
        if message_type != "text":
            raise ValueError(f"Feishu text adapter does not support message type {message_type!r}")
        message_id = _first(message, "message_id", "messageId", "id") or _first(root, "event_id", "eventId")
        chat_id = _first(message, "chat_id", "chatId")
        sender_id = _sender_id(sender)
        if message_id is None or chat_id is None or sender_id is None:
            raise ValueError("Feishu text event requires message_id, chat_id, and sender identity")
        chat_type = str(_first(message, "chat_type", "chatType") or "group")
        sender_name = _sender_name(sender, sender_id)
        content = _text_content(_first(message, "content", "text"))
        create_time = _first(message, "create_time", "createTime", "created_at", "time")
        if create_time is None:
            create_time = _first(root, "create_time", "createTime", "timestamp")
        header = _mapping(root.get("header"))
        tenant_id = (
            _first(message, "tenant_key", "tenant_id", "tenantId")
            or _first(root, "tenant_key", "tenant_id")
            or _first(header, "tenant_key", "tenant_id", "tenantId")
        )
        parent_id = _first(message, "parent_id", "parentId", "root_id", "rootId")
        mention_rows = _first(message, "mentions")
        mention_ids = set()
        if isinstance(mention_rows, Sequence) and not isinstance(mention_rows, (str, bytes, bytearray)):
            for mention in mention_rows:
                mention_mapping = _mapping(mention)
                mention_id = _sender_id(mention_mapping)
                if mention_id:
                    mention_ids.add(mention_id)
        detected_mention = bot_open_id is not None and str(bot_open_id) in mention_ids
        final_mentions_agent = detected_mention if mentions_agent is None else mentions_agent
        safe_metadata = {
            "message_type": "text",
            "chat_type": chat_type,
        }
        if event_identifier := self.event_id(root):
            safe_metadata["event_id"] = event_identifier
        conversation = self.conversation(
            chat_id=str(chat_id),
            chat_type=chat_type,
            tenant_id=None if tenant_id is None else str(tenant_id),
        )
        reply_to = (
            MessageRef(platform=FEISHU_PLATFORM, conversation=conversation, message_id=str(parent_id))
            if parent_id is not None
            else None
        )
        return self.text_message(
            message_id=str(message_id),
            chat_id=str(chat_id),
            sender_id=sender_id,
            sender_name=sender_name,
            text=content,
            created_at=create_time if create_time is not None else datetime.now(UTC),
            chat_type=chat_type,
            tenant_id=None if tenant_id is None else str(tenant_id),
            reply_to=reply_to,
            mentions_agent=bool(final_mentions_agent),
            metadata=safe_metadata,
        )

    @staticmethod
    def event_id(event: Mapping[str, object]) -> str | None:
        """Return the provider event ID used to reject webhook retries."""

        root = _mapping(event)
        header = _mapping(root.get("header"))
        message = _nested(root, "event", "message") or _mapping(root.get("message")) or root
        value = (
            _first(header, "event_id", "eventId")
            or _first(root, "event_id", "eventId")
            or _first(message, "message_id", "messageId", "id")
        )
        return str(value) if value is not None and str(value).strip() else None

    @staticmethod
    def chat_message(
        item: object,
        *,
        conversation: ConversationRef | None = None,
    ) -> ChatMessage:
        return _as_chat_message(item, conversation)

    @staticmethod
    def chat_messages(
        items: Sequence[object],
        *,
        conversation: ConversationRef | None = None,
    ) -> tuple[ChatMessage, ...]:
        return tuple(FeishuMessageAdapter.chat_message(item, conversation=conversation) for item in items)


HistoryLoader = Callable[[HistoryQuery], Awaitable[Sequence[object]] | Sequence[object]]
HistoryAppender = Callable[[StoredMessage], Awaitable[object] | object]


class FeishuHistoryStore:
    """History facade with callback injection and an isolated in-memory mode.

    The in-memory mode is useful for the P4 smoke path and contract tests.  A
    production adapter can inject a durable loader/appender without changing
    the application ports or importing a Feishu SDK here.
    """

    def __init__(
        self,
        *,
        adapter: FeishuMessageAdapter | None = None,
        loader: HistoryLoader | None = None,
        appender: HistoryAppender | None = None,
        records: Mapping[ConversationRef, Sequence[object]] | None = None,
    ) -> None:
        self.adapter = adapter or FeishuMessageAdapter("history")
        self._loader = loader
        self._appender = appender
        self._records: defaultdict[ConversationRef, list[StoredMessage]] = defaultdict(list)
        for conversation, values in (records or {}).items():
            self._records[conversation].extend(
                self.adapter.chat_message(value, conversation=conversation) for value in values
            )

    async def load(self, query: HistoryQuery) -> list[ChatMessage]:
        if query.limit <= 0:
            return []
        if query.conversation.platform.lower() != FEISHU_PLATFORM:
            raise ValueError("FeishuHistoryStore only handles feishu conversations")
        loaded_from_callback = self._loader is not None
        if loaded_from_callback:
            result = self._loader(query)
            records = await result if inspect.isawaitable(result) else result
            messages = [self.adapter.chat_message(value, conversation=query.conversation) for value in records]
        else:
            messages = list(self._records.get(query.conversation, ()))
        if query.before is not None:
            messages = [message for message in messages if message.created_at is None or message.created_at < query.before]
        if query.after is not None:
            messages = [message for message in messages if message.created_at is None or message.created_at >= query.after]
        # A callback owns its ordering and may already apply the database
        # limit.  The local smoke store keeps chronological rows, so return
        # the newest bounded suffix there.
        return messages[: query.limit] if loaded_from_callback else messages[-query.limit :]

    async def append(self, message: StoredMessage) -> None:
        if message.conversation is None:
            raise ValueError("Feishu history messages require a conversation")
        if message.conversation.platform.lower() != FEISHU_PLATFORM:
            raise ValueError("FeishuHistoryStore only handles feishu conversations")
        if self._appender is not None:
            result = self._appender(message)
            if inspect.isawaitable(result):
                await result
            return
        self._records[message.conversation].append(message)


def _message_refs(target: ConversationRef, value: object) -> tuple[MessageRef, ...]:
    mapping = _mapping(value)
    data = _mapping(mapping.get("data"))
    raw_ids: object = _first(mapping, "message_ids", "messageIds")
    if raw_ids is None:
        raw_ids = _first(data, "message_ids", "messageIds")
    if raw_ids is None:
        one = _first(mapping, "message_id", "messageId", "id") or _first(data, "message_id", "messageId", "id")
        raw_ids = () if one is None else (one,)
    if isinstance(raw_ids, (str, bytes, bytearray)):
        raw_ids = (raw_ids,)
    if not isinstance(raw_ids, Sequence):
        return ()
    return tuple(MessageRef(platform=FEISHU_PLATFORM, conversation=target, message_id=str(item)) for item in raw_ids)


def _delivery_receipt(target: ConversationRef, result: object) -> DeliveryReceipt:
    if isinstance(result, DeliveryReceipt):
        return result
    if isinstance(result, bool):
        return DeliveryReceipt(DeliveryStatus.DELIVERED if result else DeliveryStatus.FAILED)
    if isinstance(result, str):
        return DeliveryReceipt(DeliveryStatus.DELIVERED, _message_refs(target, {"message_id": result}))
    mapping = _mapping(result)
    status_value = _first(mapping, "status", "delivery_status")
    success_value = _first(mapping, "successful", "success", "ok")
    if status_value is not None:
        normalized = str(status_value).lower()
        status = {
            "delivered": DeliveryStatus.DELIVERED,
            "success": DeliveryStatus.DELIVERED,
            "sent": DeliveryStatus.DELIVERED,
            "failed": DeliveryStatus.FAILED,
            "error": DeliveryStatus.FAILED,
            "unknown": DeliveryStatus.UNKNOWN,
        }.get(normalized, DeliveryStatus.UNKNOWN)
    elif success_value is not None:
        status = DeliveryStatus.DELIVERED if bool(success_value) else DeliveryStatus.FAILED
    else:
        successful = getattr(result, "successful", None)
        status = DeliveryStatus.DELIVERED if successful is True else DeliveryStatus.FAILED if successful is False else DeliveryStatus.UNKNOWN
    errors_value: object = _first(mapping, "errors", "error", "message")
    if errors_value is None:
        errors = ()
    elif isinstance(errors_value, Sequence) and not isinstance(errors_value, (str, bytes, bytearray)):
        errors = tuple(str(error) for error in errors_value)
    else:
        errors = (str(errors_value),)
    if status == DeliveryStatus.UNKNOWN and not errors:
        errors = ("delivery_result_unknown",)
    return DeliveryReceipt(status, _message_refs(target, result), errors)


TextSender = Callable[[ConversationRef, str], Awaitable[object] | object]


class FeishuDelivery:
    """Deliver text through an injected Feishu sender.

    Artifact responses are rejected explicitly in the P4 text-only facade so
    callers cannot accidentally claim a card/image was delivered as text.
    """

    def __init__(self, *, text_sender: TextSender | None = None) -> None:
        self._text_sender = text_sender

    async def send(self, target: ConversationRef, response: AgentResponse) -> DeliveryReceipt:
        if target.platform.lower() != FEISHU_PLATFORM:
            raise ValueError("FeishuDelivery only handles feishu conversations")
        if not response.should_reply:
            return DeliveryReceipt(DeliveryStatus.DELIVERED)
        if response.artifacts:
            return DeliveryReceipt(DeliveryStatus.FAILED, errors=("feishu_text_only_artifact",))
        if not response.text.strip():
            return DeliveryReceipt(DeliveryStatus.FAILED, errors=("empty_response",))
        if self._text_sender is None:
            return DeliveryReceipt(DeliveryStatus.FAILED, errors=("text_sender_required",))
        try:
            result = self._text_sender(target, response.text)
            if inspect.isawaitable(result):
                result = await result
        except Exception as error:
            return DeliveryReceipt(DeliveryStatus.FAILED, errors=(type(error).__name__,))
        return _delivery_receipt(target, result)


class FeishuReplyPolicy:
    """Default Feishu gate: direct chats reply, groups require an @ mention."""

    def __init__(
        self,
        decide_callback: Callable[[InboundMessage, Sequence[ChatMessage]], Awaitable[GateDecision | bool] | GateDecision | bool]
        | None = None,
        *,
        require_mention_in_group: bool = True,
        allow_replies: bool = False,
    ) -> None:
        self._decide_callback = decide_callback
        self.require_mention_in_group = require_mention_in_group
        self.allow_replies = allow_replies

    async def decide(self, message: InboundMessage, history: Sequence[ChatMessage]) -> GateDecision:
        if self._decide_callback is not None:
            result = self._decide_callback(message, history)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, GateDecision):
                return result
            return GateDecision(bool(result), reason="injected_callback")
        if message.conversation.kind == "thread":
            return GateDecision(False, reason="thread_not_supported")
        if message.reply_to is not None and not self.allow_replies:
            return GateDecision(False, reason="reply_not_supported")
        if message.conversation.kind == "direct":
            return GateDecision(True, reason="direct_message")
        if message.conversation.kind == "group" and self.require_mention_in_group:
            return GateDecision(
                message.mentions_agent,
                reason="mentioned_agent" if message.mentions_agent else "group_requires_mention",
            )
        return GateDecision(True, reason="chat_policy")


class FeishuToolProvider:
    """P4 intentionally exposes no Feishu-specific platform tools."""

    def __init__(self, tools: Sequence[object] = ()) -> None:
        self._tools = tuple(tools)

    def tools(self, capabilities: frozenset[str]) -> Sequence[object]:
        if not any(capability == "feishu" or capability.startswith("feishu:") for capability in capabilities):
            return ()
        return self._tools


class _EventDeduper:
    """Bounded synchronous event-id cache for webhook retries."""

    def __init__(self, max_entries: int) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._seen: OrderedDict[str, None] = OrderedDict()

    def claim(self, event_id: str | None) -> bool:
        if not event_id:
            return True
        if event_id in self._seen:
            return False
        self._seen[event_id] = None
        self._seen.move_to_end(event_id)
        while len(self._seen) > self._max_entries:
            self._seen.popitem(last=False)
        return True

    def release(self, event_id: str | None) -> None:
        if event_id:
            self._seen.pop(event_id, None)


class FeishuTextGateway:
    """Run the SDK-free Feishu text MVP through the shared orchestrator.

    A real webhook or long-connection plugin owns signature verification and
    passes the decoded event here.  The gateway deliberately has no global
    NoneBot registration, network client, or Feishu SDK dependency.
    """

    def __init__(
        self,
        *,
        core: object,
        history: object,
        delivery: object,
        account_id: str,
        bot_open_id: str | None = None,
        policy: FeishuReplyPolicy | None = None,
        tools: object | None = None,
        execution_profile: str = "medium",
        allow_silent_reply: bool = False,
        max_seen_events: int = 2048,
    ) -> None:
        self.adapter = FeishuMessageAdapter(account_id)
        self._orchestrator = ConversationOrchestrator(core)
        self._history = history
        self._delivery = delivery
        self._bot_open_id = bot_open_id
        self._policy = policy or FeishuReplyPolicy()
        self._tools = tools if tools is not None else FeishuToolProvider()
        self._execution_profile = execution_profile
        self._allow_silent_reply = allow_silent_reply
        self._deduper = _EventDeduper(max_seen_events)

    async def handle_event(self, event: Mapping[str, object]) -> TurnOutcome | None:
        """Normalize and execute one event; return ``None`` for a retry."""

        event_id = self.adapter.event_id(event)
        message = self.adapter.from_event(event, bot_open_id=self._bot_open_id)
        dedupe_key = event_id or message.message_id
        if not self._deduper.claim(dedupe_key):
            return None
        outcome = await self._orchestrator.handle(
            message,
            policy=self._policy,
            history=self._history,
            delivery=self._delivery,
            tools=self._tools,
            workspace_key=workspace_key_for(message.conversation),
            capabilities=FEISHU_TEXT_CAPABILITIES,
            execution_profile=self._execution_profile,
            allow_silent_reply=self._allow_silent_reply,
        )
        # A transient history/gate failure happened before Agent Core started;
        # permit the connector to retry the same event.  Once Core has run,
        # keep the claim to prevent duplicate tool side effects or delivery.
        if outcome.status.value in {"history_failed", "gate_failed"}:
            self._deduper.release(dedupe_key)
        return outcome


__all__ = [
    "FEISHU_PLATFORM",
    "FEISHU_TEXT_CAPABILITIES",
    "FeishuDelivery",
    "FeishuHistoryStore",
    "FeishuMessageAdapter",
    "FeishuReplyPolicy",
    "FeishuTextGateway",
    "FeishuToolProvider",
]
