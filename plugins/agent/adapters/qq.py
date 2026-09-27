"""Small QQ facades around the existing Milky implementations.

The facades deliberately accept injected callables and objects.  This keeps
the neutral Agent ports independent from NoneBot and lets tests (and future
platform entry points) exercise the boundary without constructing a Milky
event.  The default text sender and tool registry are resolved lazily, so
importing this module never registers a plugin or opens a database.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from utils.agent_protocol import (
    AgentArtifact,
    AgentResponse,
    AudioPart,
    ChatMessage,
    ConversationRef,
    DeliveryReceipt,
    DeliveryStatus,
    FilePart,
    GateDecision,
    HistoryQuery,
    ImagePart,
    InboundMessage,
    MessageRef,
    Participant,
    QuotePart,
    StoredMessage,
    TextPart,
    VideoPart,
)

QQ_PLATFORMS = frozenset({"qq", "milky"})
_SHANGHAI = ZoneInfo("Asia/Shanghai")
QQ_TOOL_MODULES = frozenset(
    {
        "adapter",
        "milky_file",
        "milky_friend",
        "milky_group",
        "milky_message",
        "milky_system",
    }
)
QQ_MODULE_CAPABILITIES = {
    "adapter": frozenset({"qq:message"}),
    "milky_file": frozenset({"qq:file"}),
    "milky_friend": frozenset({"qq:friend"}),
    "milky_group": frozenset({"qq:group"}),
    "milky_message": frozenset({"qq:message"}),
    "milky_system": frozenset({"qq:system"}),
}


class QqMessageAdapter:
    """Normalize the small identity/message subset needed by the Agent port.

    Native Milky event parsing remains in ``handlers.py`` for now.  This
    adapter owns the conversion after parsing, so the text canary can construct
    an :class:`InboundMessage` without importing handler internals.
    """

    def __init__(self, account_id: str | int) -> None:
        self.account_id = str(account_id)

    def conversation(
        self,
        *,
        group_id: str | int | None,
        user_id: str | int,
    ) -> ConversationRef:
        return ConversationRef(
            platform="qq",
            account_id=self.account_id,
            kind="group" if group_id is not None else "private",
            conversation_id=str(group_id if group_id is not None else user_id),
        )

    @staticmethod
    def participant(
        *,
        user_id: str | int,
        user_name: str,
        role: str | None = None,
    ) -> Participant:
        return Participant(id=str(user_id), display_name=user_name, role=role)

    def text_message(
        self,
        *,
        message_id: str | int,
        group_id: str | int | None,
        user_id: str | int,
        user_name: str,
        text: str,
        created_at: datetime,
        role: str | None = None,
        mentions_agent: bool = False,
        images: Sequence[bytes] = (),
        audio: Sequence[bytes] = (),
        videos: Sequence[bytes] = (),
        attachments: Sequence[Mapping[str, object]] = (),
        recent_images: Sequence[bytes] = (),
        recent_attachments: Sequence[Mapping[str, object]] = (),
        reply_to: MessageRef | None = None,
        quoted_payload: Mapping[str, object] | None = None,
        quoted_images: Sequence[bytes] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> InboundMessage:
        """Create a normalized QQ message from already downloaded payloads."""

        conversation = self.conversation(group_id=group_id, user_id=user_id)
        sender = self.participant(user_id=user_id, user_name=user_name, role=role)
        parts = [TextPart(text)]
        parts.extend(ImagePart(data=data) for data in images)
        parts.extend(AudioPart(data=data) for data in audio)
        parts.extend(VideoPart(data=data) for data in videos)
        parts.extend(self._file_parts(attachments))
        if recent_images or recent_attachments:
            parts.append(TextPart("[以下媒体来自用户刚才发送的历史消息]"))
            parts.extend(ImagePart(data=data) for data in recent_images)
            parts.extend(self._file_parts(recent_attachments))
        if quote := self.quote_part(
            quoted_payload,
            conversation=conversation,
            reply_to=reply_to,
            images=quoted_images,
        ):
            parts.append(quote)
        return InboundMessage(
            message_id=str(message_id),
            conversation=conversation,
            sender=sender,
            created_at=created_at,
            parts=tuple(parts),
            reply_to=reply_to,
            mentions_agent=mentions_agent,
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _file_parts(attachments: Sequence[Mapping[str, object]]) -> list[FilePart]:
        parts: list[FilePart] = []
        for item in attachments:
            if not isinstance(item, Mapping) or str(item.get("kind", "")).lower() != "file":
                continue
            path = item.get("path")
            name = item.get("file_name") or item.get("name")
            if path is None and name is None:
                continue
            parts.append(
                FilePart(
                    url=None if path is None else str(path),
                    name=None if name is None else str(name),
                    mime_type=str(item["mime_type"]) if item.get("mime_type") else None,
                )
            )
        return parts

    @staticmethod
    def quote_part(
        payload: Mapping[str, object] | None,
        *,
        conversation: ConversationRef,
        reply_to: MessageRef | None = None,
        images: Sequence[bytes] = (),
    ) -> QuotePart | None:
        """Convert the legacy reply snapshot into a neutral quote value."""

        payload = payload if isinstance(payload, Mapping) else {}
        message_id = payload.get("message_id")
        message_ref = reply_to
        if message_ref is None and message_id is not None:
            message_ref = MessageRef(
                platform="qq",
                conversation=conversation,
                message_id=str(message_id),
            )
        quote_parts = []
        content = payload.get("content")
        if isinstance(content, str) and content.strip():
            quote_parts.append(TextPart(content.strip()))
        quote_parts.extend(ImagePart(data=data) for data in images if data)
        attachments = payload.get("attachments")
        if isinstance(attachments, Sequence) and not isinstance(attachments, (str, bytes, bytearray)):
            for item in attachments:
                if not isinstance(item, Mapping):
                    continue
                path = item.get("path")
                name = item.get("file_name") or item.get("name")
                if path is None and name is None:
                    continue
                quote_parts.append(
                    FilePart(
                        url=None if path is None else str(path),
                        name=None if name is None else str(name),
                        mime_type=str(item["mime_type"]) if item.get("mime_type") else None,
                    )
                )
        if not quote_parts and message_ref is None:
            return None
        if not quote_parts:
            quote_parts.append(TextPart("[引用消息]"))
        return QuotePart(message_ref=message_ref, parts=tuple(quote_parts))

    def chat_message(
        self,
        item: object,
        *,
        conversation: ConversationRef | None = None,
    ) -> ChatMessage:
        """Convert one legacy QQ context/history row to a neutral message.

        ``MessageDatabase.prepare_message`` returns dictionaries whose
        ``content`` is a serialized ``frontier.qq_message.v1`` envelope.  We
        keep that serialized value as the message content so the existing
        model prompt remains byte-for-byte compatible, while exposing parsed
        identity and timestamp fields on the neutral object for new adapters.
        """

        return _as_chat_message(item, conversation)

    def chat_messages(
        self,
        items: Sequence[object],
        *,
        conversation: ConversationRef | None = None,
    ) -> tuple[ChatMessage, ...]:
        """Convert a history snapshot without importing database classes."""

        return tuple(self.chat_message(item, conversation=conversation) for item in items)


def _qq_conversation(conversation: ConversationRef) -> tuple[int | None, int]:
    """Convert the opaque QQ conversation ID at the adapter boundary."""
    if conversation.platform.lower() not in QQ_PLATFORMS:
        raise ValueError(f"QQ facade cannot handle platform {conversation.platform!r}")
    try:
        conversation_id = int(conversation.conversation_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("QQ conversation IDs must be numeric") from exc
    kind = conversation.kind.lower()
    if kind in {"group", "guild_group"}:
        return conversation_id, conversation_id
    if kind in {"direct", "private", "user"}:
        return None, conversation_id
    raise ValueError(f"unsupported QQ conversation kind {conversation.kind!r}")


def _qq_account_id(conversation: ConversationRef) -> int | None:
    try:
        return int(conversation.account_id)
    except (TypeError, ValueError):
        return None


def _content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, tuple):
        return "".join(part.text if isinstance(part, TextPart) else f"[{type(part).__name__}]" for part in content)
    return str(content or "")


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        # QQ/database timestamps are milliseconds; accept seconds for callers
        # that already normalized their history snapshot.
        timestamp = float(value)
        if abs(timestamp) > 10_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str) and value.strip():
        candidate = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=_SHANGHAI)
    return None


def _json_mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, str) or not value.lstrip().startswith("{"):
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def _as_sender(value: object, *, role: str) -> Participant | None:
    if not isinstance(value, Mapping):
        return None
    user_id = value.get("user_id", value.get("id"))
    display_name = value.get("display_name", value.get("name", value.get("nickname")))
    if user_id is None and display_name is None:
        return None
    return Participant(
        id=str(user_id or ""),
        display_name=str(display_name or user_id or "Unknown"),
        role=str(value.get("role") or role),
    )


def _normalize_role(value: object) -> str:
    role = str(value or "user").lower()
    return {"human": "user", "ai": "assistant", "bot": "assistant"}.get(role, role)


def _as_chat_message(item: object, conversation: ConversationRef | None = None) -> ChatMessage:
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
    if isinstance(item, Mapping):
        role = _normalize_role(item.get("role", item.get("type", "user")))
        content = item.get("content", "")
        message_id = item.get("message_id", item.get("id"))
        metadata = item.get("metadata", {})
        created_at = item.get("created_at", item.get("time"))
        sender_value = item.get("sender")
    else:
        role = _normalize_role(getattr(item, "role", getattr(item, "type", "user")))
        content = getattr(item, "content", "")
        message_id = getattr(item, "message_id", getattr(item, "id", None))
        metadata = getattr(item, "metadata", {})
        created_at = getattr(item, "created_at", getattr(item, "time", None))
        sender_value = getattr(item, "sender", None)

    # Database history stores the complete envelope as JSON.  Use it as a
    # source of neutral metadata while retaining the original content string.
    payload = _json_mapping(content)
    if payload is not None:
        role = _normalize_role(payload.get("role", role))
        message_id = payload.get("message_id", message_id)
        created_at = payload.get("time", created_at)
        sender_value = payload.get("sender", sender_value)
        if isinstance(metadata, Mapping):
            metadata = {**metadata, "qq_payload": dict(payload)}
    if not isinstance(content, (str, tuple)):
        content = _content_text(content)
    if not isinstance(metadata, Mapping):
        metadata = {}
    return ChatMessage(
        role=role,
        content=content,
        message_id=None if message_id is None else str(message_id),
        conversation=conversation,
        sender=_as_sender(sender_value, role=role),
        created_at=_coerce_datetime(created_at),
        metadata=metadata,
    )


class QqHistoryStore:
    """Adapt the existing ``MessageDatabase`` to :class:`HistoryStore`.

    ``database`` only needs ``prepare_message`` and ``insert``.  Supplying
    ``loader``/``appender`` is supported for isolated tests and for staged
    migrations where the database implementation is not yet available.
    """

    def __init__(
        self,
        database: object | None = None,
        *,
        loader: Callable[[HistoryQuery], Awaitable[Sequence[object]] | Sequence[object]] | None = None,
        appender: Callable[[StoredMessage], Awaitable[object] | object] | None = None,
    ) -> None:
        if database is None and loader is None and appender is None:
            raise ValueError("QqHistoryStore requires database or injected callbacks")
        self.database = database
        self._loader = loader
        self._appender = appender

    async def load(self, query: HistoryQuery) -> list[ChatMessage]:
        if query.limit <= 0:
            return []
        group_id, user_id = _qq_conversation(query.conversation)
        if self._loader is not None:
            records = self._loader(query)
            if inspect.isawaitable(records):
                records = await records
        else:
            prepare = getattr(self.database, "prepare_message", None)
            if not callable(prepare):
                raise TypeError("QqHistoryStore database must provide prepare_message")
            before_time = int(query.before.timestamp() * 1000) if query.before else None
            records = await prepare(
                user_id=user_id if group_id is None else None,
                group_id=group_id,
                query_numbers=query.limit,
                before_time=before_time,
            )
        messages = [_as_chat_message(record, query.conversation) for record in records]
        if query.before is not None:
            messages = [
                message
                for message in messages
                if message.created_at is None or message.created_at < query.before
            ]
        if query.after is not None:
            messages = [
                message
                for message in messages
                if message.created_at is None or message.created_at >= query.after
            ]
        return messages[: query.limit]

    async def append(self, message: StoredMessage) -> None:
        if self._appender is not None:
            result = self._appender(message)
            if inspect.isawaitable(result):
                await result
            return
        if message.conversation is None:
            raise ValueError("QQ history messages require a conversation")
        insert = getattr(self.database, "insert", None)
        if not callable(insert):
            raise TypeError("QqHistoryStore database must provide insert")
        group_id, user_id = _qq_conversation(message.conversation)
        account_id = _qq_account_id(message.conversation)
        sender = message.sender
        sender_id = sender.id if sender is not None else (
            str(account_id) if account_id is not None else message.conversation.conversation_id
        )
        try:
            db_user_id = int(sender_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("QQ message senders must have numeric IDs") from exc
        if message.role == "assistant":
            if group_id is not None and account_id is not None:
                db_user_id = account_id
            elif group_id is None:
                # Private QQ history is scoped by the other participant; the
                # bot identity is kept separately in ``bot_user_id``.
                db_user_id = user_id
        try:
            msg_id = int(message.message_id) if message.message_id is not None else None
        except (TypeError, ValueError):
            msg_id = None
        await insert(
            time=int(message.created_at.timestamp() * 1000) if message.created_at else 0,
            msg_id=msg_id,
            user_id=db_user_id,
            group_id=group_id,
            user_name=sender.display_name if sender is not None else "Assistant",
            role=message.role,
            content=_content_text(message.content),
            bot_user_id=account_id,
            sender_user_id=account_id if message.role == "assistant" else db_user_id,
            normalized_status="complete",
        )


def _message_refs(target: ConversationRef, result: object) -> tuple[MessageRef, ...]:
    if isinstance(result, Mapping):
        refs = result.get("message_ids", result.get("messageIds", ()))
        if not refs:
            one = result.get("message_id", result.get("messageId"))
            refs = () if one is None else (one,)
    else:
        refs = getattr(result, "message_ids", ()) or ()
        if not refs:
            one = getattr(result, "message_id", None)
            refs = () if one is None else (one,)
    if isinstance(refs, (str, bytes, bytearray)):
        refs = (refs,)
    return tuple(MessageRef(platform="qq", conversation=target, message_id=str(item)) for item in refs)


def _legacy_receipt(target: ConversationRef, result: object) -> DeliveryReceipt:
    if isinstance(result, DeliveryReceipt):
        return result
    if isinstance(result, bool):
        return DeliveryReceipt(DeliveryStatus.DELIVERED if result else DeliveryStatus.FAILED)
    if isinstance(result, Mapping):
        status = str(result.get("status", result.get("delivery_status", ""))).lower()
        if status in {"delivered", "success", "sent"}:
            return DeliveryReceipt(DeliveryStatus.DELIVERED, _message_refs(target, result))
        successful = result.get("successful", result.get("success", result.get("ok")))
    else:
        successful = getattr(result, "successful", None)
    if successful is True:
        return DeliveryReceipt(DeliveryStatus.DELIVERED, _message_refs(target, result))
    raw_errors = result.get("errors", result.get("error", ())) if isinstance(result, Mapping) else getattr(result, "errors", ())
    if isinstance(raw_errors, (str, bytes, bytearray)):
        raw_errors = (raw_errors,)
    errors = tuple(str(error) for error in (raw_errors or ()))
    return DeliveryReceipt(DeliveryStatus.FAILED, _message_refs(target, result), errors or ("delivery_failed",))


class QqDelivery:
    """Deliver neutral responses through the existing QQ sender.

    ``text_sender`` receives ``(ConversationRef, text)``.  ``artifact_sender``
    is intentionally injected because the legacy ``send_artifacts`` accepts
    ``UniMessage`` objects; the canary supplies the QQ-specific conversion
    policy while the port remains neutral.
    """

    def __init__(
        self,
        *,
        text_sender: Callable[[ConversationRef, str], Awaitable[object]] | None = None,
        artifact_sender: Callable[[ConversationRef, Sequence[AgentArtifact]], Awaitable[object]] | None = None,
    ) -> None:
        self._text_sender = text_sender
        self._artifact_sender = artifact_sender

    async def _send_text(self, target: ConversationRef, text: str) -> DeliveryReceipt:
        sender = self._text_sender
        if sender is None:
            from utils.message import send_messages

            group_id, _ = _qq_conversation(target)
            result = await send_messages(group_id, None, {"messages": [text]})
        else:
            result = sender(target, text)
            if inspect.isawaitable(result):
                result = await result
        return _legacy_receipt(target, result)

    async def send(self, target: ConversationRef, response: AgentResponse) -> DeliveryReceipt:  # noqa: C901
        _qq_conversation(target)
        if not response.should_reply:
            return DeliveryReceipt(DeliveryStatus.DELIVERED)
        receipts: list[DeliveryReceipt] = []
        if response.artifacts:
            if self._artifact_sender is None:
                receipts.append(
                    DeliveryReceipt(DeliveryStatus.FAILED, errors=("artifact_sender_required",))
                )
            else:
                try:
                    result = self._artifact_sender(target, response.artifacts)
                    if inspect.isawaitable(result):
                        result = await result
                    receipts.append(_legacy_receipt(target, result))
                except Exception as exc:
                    receipts.append(DeliveryReceipt(DeliveryStatus.FAILED, errors=(type(exc).__name__,)))
        if response.text.strip():
            try:
                receipts.append(await self._send_text(target, response.text))
            except Exception as exc:
                receipts.append(DeliveryReceipt(DeliveryStatus.FAILED, errors=(type(exc).__name__,)))
        if not receipts:
            return DeliveryReceipt(DeliveryStatus.DELIVERED)
        status = DeliveryStatus.DELIVERED
        if any(receipt.status == DeliveryStatus.UNKNOWN for receipt in receipts):
            status = DeliveryStatus.UNKNOWN
        if any(receipt.status == DeliveryStatus.FAILED for receipt in receipts):
            status = DeliveryStatus.FAILED
        return DeliveryReceipt(
            status=status,
            message_refs=tuple(ref for receipt in receipts for ref in receipt.message_refs),
            errors=tuple(error for receipt in receipts for error in receipt.errors),
        )


class QqReplyPolicy:
    """Wrap a QQ gate callback while keeping the Agent side platform-neutral."""

    def __init__(
        self,
        decide_callback: Callable[[InboundMessage, Sequence[ChatMessage]], Awaitable[GateDecision | bool]] | None = None,
    ) -> None:
        self._decide_callback = decide_callback

    async def decide(self, message: InboundMessage, history: Sequence[ChatMessage]) -> GateDecision:
        if self._decide_callback is not None:
            result = await self._decide_callback(message, history)
            if isinstance(result, GateDecision):
                return result
            return GateDecision(bool(result), reason="injected_callback")
        # The inbound adapter maps QQ's is_tome/to_me/wake-word decision to
        # mentions_agent.  This fallback is deliberately conservative until the
        # legacy event gateway is injected into the QQ entry point.
        return GateDecision(message.mentions_agent, reason="mentions_agent" if message.mentions_agent else "not_mentioned")


def _tool_module(tool: object, metadata: Mapping[str, object]) -> str:
    name = str(getattr(tool, "name", ""))
    item = metadata.get(name)
    if isinstance(item, Mapping) and item.get("module"):
        return str(item["module"])
    module = str(getattr(tool, "__module__", "")).rsplit(".", 1)[-1]
    if module in QQ_TOOL_MODULES:
        return module
    if name.startswith("milky_"):
        return name.split("_", 2)[0] + "_" + name.split("_", 2)[1]
    return ""


class QqToolProvider:
    """Select only QQ platform tools from the existing lazy tool registry."""

    def __init__(self, registry: object | None = None, *, allowed_modules: frozenset[str] = QQ_TOOL_MODULES) -> None:
        self._registry = registry
        self._allowed_modules = allowed_modules

    @staticmethod
    def _default_registry() -> object:
        from tools import agent_tools

        return agent_tools

    def tools(self, capabilities: frozenset[str]) -> Sequence[object]:
        broad_qq_capability = bool({"qq", "platform:qq", "qq:tools"} & capabilities)
        has_qq_capability = broad_qq_capability or any(
            capability.startswith("qq:") for capability in capabilities
        )
        if not has_qq_capability:
            return ()
        registry = self._registry or self._default_registry()
        raw_tools = getattr(registry, "main_tools", None)
        if raw_tools is None:
            groups = getattr(registry, "subagent_tools", {})
            raw_tools = groups.get("main", ()) if isinstance(groups, Mapping) else ()
        metadata = getattr(registry, "tool_metadata", {})
        selected = []
        for tool in raw_tools:
            module = _tool_module(tool, metadata if isinstance(metadata, Mapping) else {})
            if module not in self._allowed_modules:
                continue
            required = QQ_MODULE_CAPABILITIES.get(module, frozenset())
            if required and not broad_qq_capability and not (required & capabilities):
                continue
            selected.append(tool)
        return tuple(selected)


__all__ = [
    "QqDelivery",
    "QqHistoryStore",
    "QqMessageAdapter",
    "QqReplyPolicy",
    "QqToolProvider",
]
