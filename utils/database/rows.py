"""Message row helpers shared by the store, attachment and search areas.

These helpers translate persisted rows into the model-facing payload envelope and
rebuild the derived ``model_content`` field once attachments have resolved.
"""

import json
import logging

from sqlmodel import Session, col, select

from utils.agents.message_envelope import (
    build_agent_attachment_payload,
    build_agent_message_payload,
    content_for_persisted_images,
)

from .models import MESSAGE_SOURCE_TYPE_NORMAL, Message, MessageAttachment, resolve_message_sender_user_id

logger = logging.getLogger(__name__)


def _message_reply_payload(message: Message) -> dict[str, object] | None:
    if not message.reply_context_json:
        return None
    try:
        parsed_reply = json.loads(message.reply_context_json)
    except json.JSONDecodeError:
        logger.warning("忽略损坏的引用消息上下文: msg_time=%s", message.time)
        return None
    return parsed_reply if isinstance(parsed_reply, dict) else None


def _message_agent_payload(
    message: Message,
    *,
    content: str | None = None,
    attachments: list[dict[str, object]] | None = None,
    include_reply_to: bool = True,
) -> dict[str, object]:
    stored_model_content = getattr(message, "model_content", None)
    resolved_content = stored_model_content if stored_model_content is not None else message.content
    return build_agent_message_payload(
        timestamp_ms=message.time,
        msg_id=message.msg_id,
        user_id=resolve_message_sender_user_id(message),
        group_id=message.group_id,
        user_name=message.user_name,
        user_nickname=message.user_nickname,
        user_card=message.user_card,
        role=message.role,
        content=resolved_content if content is None else content,
        attachments=attachments,
        reply_to=_message_reply_payload(message) if include_reply_to else None,
        bot_user_id=message.bot_user_id,
        directly_mentions_bot=message.directly_mentions_bot,
    )


def _attachment_agent_payload(attachment: MessageAttachment) -> dict[str, object]:
    return dict(
        build_agent_attachment_payload(
            kind=attachment.kind,
            mime_type=attachment.mime_type,
            file_name=attachment.file_name,
            path=attachment.virtual_path,
        )
    )


_REPLY_CONTEXT_UNSET = object()


def _find_message(
    session: Session,
    msg_time: int,
    *,
    message_id: int | None = None,
    scope: tuple[int, int | None] | None = None,
    msg_id: int | None = None,
) -> Message | None:
    statement = select(Message).where(
        Message.time == msg_time, Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL,
    )
    if message_id is not None:
        statement = statement.where(Message.id == message_id)
    if scope is not None:
        user_id, group_id = scope
        statement = statement.where(Message.group_id == group_id, Message.user_id == user_id)
    if msg_id is not None:
        statement = statement.where(Message.msg_id == msg_id)
    candidates = session.exec(statement.limit(2)).all()
    if len(candidates) > 1:
        raise ValueError("Ambiguous message timestamp; provide message_id")
    if not candidates and message_id is not None:
        raise ValueError("message_id does not match the supplied timestamp or conversation")
    return candidates[0] if candidates else None


def _attachments_for_message(session: Session, message: Message) -> list[MessageAttachment]:
    statement = select(MessageAttachment).where(
        (MessageAttachment.message_id == message.id)
        | ((MessageAttachment.message_id.is_(None)) & (MessageAttachment.msg_time == message.time))
    ).where(MessageAttachment.group_id == message.group_id)
    if message.group_id is None:
        statement = statement.where(MessageAttachment.user_id == message.user_id)
    records = session.exec(statement.order_by(col(MessageAttachment.file_name))).all()
    return [
        record for record in records
        if record.message_id is not None
        or (record.user_id == message.user_id and record.msg_id in (None, message.msg_id))
    ]


def _refresh_message_model_state(
    session: Session,
    msg_time: int,
    *,
    message_id: int | None = None,
    reply_context_json: str | None | object = _REPLY_CONTEXT_UNSET,
) -> None:
    """Rebuild all attachment-derived message fields inside one transaction."""
    message = _find_message(session, msg_time, message_id=message_id)
    if message is None:
        return
    if reply_context_json is not _REPLY_CONTEXT_UNSET:
        message.reply_context_json = reply_context_json  # type: ignore[assignment]
    attachments = _attachments_for_message(session, message)
    model_content = content_for_persisted_images(
        message.content,
        sum(attachment.kind == "image" for attachment in attachments),
    )
    message.model_content = None if model_content == message.content else model_content
    session.add(message)


def _refresh_message_model_states(session: Session, msg_times: set[int]) -> None:
    messages = session.exec(select(Message).where(
        col(Message.time).in_(msg_times), Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL,
    )).all()
    for message in messages:
        _refresh_message_model_state(session, message.time, message_id=message.id)
