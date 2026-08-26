"""Provider-neutral model-facing message envelopes.

This module intentionally depends only on the standard library so message
serialization can be shared by database, QQ and scheduled-task adapters
without importing an LLM provider.
"""

from __future__ import annotations

import datetime
import json
import zoneinfo
from typing import NotRequired, TypedDict

AGENT_MESSAGE_SCHEMA = "frontier.qq_message.v1"
AGENT_MESSAGE_REF_SCHEMA = "frontier.qq_message_ref.v1"
CONVERSATION_SUMMARY_SCHEMA = "frontier.conversation_summary.v1"
DIRECT_MENTION_CONTEXT_MARKER = "[你被主动@了，这条消息是明确对你说的]"
EMPTY_MESSAGE_CONTEXT_MARKER = "[用户叫了你一声]"
ATTACHMENT_ONLY_CONTEXT_MARKER = "[消息内容见附件]"
REPLY_ONLY_CONTEXT_MARKER = "[消息仅包含引用]"
_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")


class AgentSender(TypedDict):
    display_name: str
    role: str
    user_id: NotRequired[str]
    nickname: NotRequired[str]


class AgentChat(TypedDict):
    type: str
    group_id: NotRequired[str]


class AgentAttachment(TypedDict):
    kind: str
    file_name: str
    path: str
    mime_type: NotRequired[str]


class AgentMessagePayload(TypedDict):
    schema: str
    time: str
    chat: AgentChat
    sender: AgentSender
    content: str
    message_id: NotRequired[str]
    reply_to: NotRequired[dict[str, object]]
    attachments: NotRequired[list[AgentAttachment]]
    bot_context: NotRequired[dict[str, object]]


def serialize_agent_payload(payload: dict[str, object]) -> str:
    """Serialize one model-facing envelope as compact, readable UTF-8 JSON."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def count_image_placeholders(content: str) -> int:
    """Count standalone markers emitted for structured image segments."""
    return sum(
        marker == "[图片]" or (marker.startswith("[图片:") and marker.endswith("]"))
        for line in content.splitlines()
        if (marker := line.strip())
    )


def content_for_persisted_images(content: str, persisted_image_count: int) -> str:
    """Remove only image markers backed by durable workspace attachments.

    The canonical database text remains untouched. Deriving the model-facing
    view from surviving attachments preserves the marker when persistence
    fails or an attachment expires.
    """
    if persisted_image_count <= 0 or not content:
        return content

    marker_count = count_image_placeholders(content)
    # A failed download does not retain a segment identity in the legacy media
    # pipeline. In a partial-success batch, keeping all markers may duplicate a
    # successful image description, but it never attributes the wrong marker to
    # an attachment or erases the failed image's only textual representation.
    if marker_count == 0 or persisted_image_count < marker_count:
        return content

    lines: list[str] = []
    for line in content.splitlines():
        marker = line.strip()
        is_image_marker = marker == "[图片]" or (marker.startswith("[图片:") and marker.endswith("]"))
        if is_image_marker:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _clean(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def build_agent_sender_payload(
    *,
    user_id: int | str | None,
    display_name: str | None,
    role: str,
    nickname: str | None = None,
    card: str | None = None,
) -> AgentSender:
    """Build one sender object without duplicate aliases or null fields."""
    normalized_user_id = _clean(user_id)
    normalized_nickname = _clean(nickname)
    normalized_card = _clean(card)
    normalized_display_name = (
        normalized_card or _clean(display_name) or normalized_nickname or normalized_user_id or "未知"
    )
    sender: AgentSender = {
        "display_name": normalized_display_name,
        "role": "assistant" if role == "assistant" else "user",
    }
    if normalized_user_id is not None:
        sender["user_id"] = normalized_user_id
    if normalized_nickname and normalized_nickname != normalized_display_name:
        sender["nickname"] = normalized_nickname
    # display_name already carries the effective group card. Repeating the same
    # value under `card` costs context without adding identity information.
    return sender


def build_agent_attachment_payload(
    *,
    kind: object,
    mime_type: object | None,
    file_name: object,
    path: object,
) -> AgentAttachment:
    """Build the stable workspace reference shared by current and historical turns."""
    attachment: AgentAttachment = {
        "kind": str(kind),
        "file_name": str(file_name),
        "path": str(path),
    }
    if normalized_mime_type := _clean(mime_type):
        attachment["mime_type"] = normalized_mime_type
    return attachment


def _message_content(
    content: str,
    *,
    attachments: list[dict[str, object]] | None,
    reply_to: dict[str, object] | None,
) -> str:
    if content.strip():
        return content
    if attachments:
        return ATTACHMENT_ONLY_CONTEXT_MARKER
    if reply_to:
        return REPLY_ONLY_CONTEXT_MARKER
    return EMPTY_MESSAGE_CONTEXT_MARKER


def build_agent_message_payload(
    *,
    timestamp_ms: int,
    user_id: int | str | None,
    group_id: int | None,
    user_name: str | None,
    role: str,
    content: str,
    msg_id: int | None = None,
    user_nickname: str | None = None,
    user_card: str | None = None,
    attachments: list[dict[str, object]] | None = None,
    reply_to: dict[str, object] | None = None,
    bot_user_id: int | str | None = None,
    directly_mentions_bot: bool = False,
) -> dict[str, object]:
    """Build the provider-neutral boundary for one original platform message."""
    chat: AgentChat = {"type": "group" if group_id is not None else "private"}
    if group_id is not None:
        chat["group_id"] = str(group_id)

    normalized_content = _message_content(content, attachments=attachments, reply_to=reply_to)
    payload: AgentMessagePayload = {
        "schema": AGENT_MESSAGE_SCHEMA,
        "time": datetime.datetime.fromtimestamp(int(timestamp_ms / 1000), tz=_SHANGHAI)
        .strftime("%Y-%m-%d %H:%M:%S"),
        "chat": chat,
        "sender": build_agent_sender_payload(
            user_id=user_id,
            display_name=user_name,
            nickname=user_nickname,
            card=user_card,
            role=role,
        ),
        "content": normalized_content,
    }
    if msg_id is not None:
        payload["message_id"] = str(msg_id)
    if directly_mentions_bot and not normalized_content.startswith(DIRECT_MENTION_CONTEXT_MARKER):
        payload["content"] = f"{DIRECT_MENTION_CONTEXT_MARKER}\n{normalized_content}"
    if reply_to:
        payload["reply_to"] = reply_to
    if attachments:
        payload["attachments"] = sorted(
            attachments,
            key=lambda attachment: (
                str(attachment.get("file_name", "")),
                str(attachment.get("kind", "")),
                str(attachment.get("path", "")),
            ),
        )
    if bot_user_id is not None:
        bot_context: dict[str, object] = {"user_id": str(bot_user_id)}
        if directly_mentions_bot:
            bot_context["directly_mentioned"] = True
        payload["bot_context"] = bot_context
    return dict(payload)


def build_agent_message_ref_payload(
    *,
    message_id: int | str | None,
    role: str,
    user_id: int | str | None,
    display_name: str | None,
    nickname: str | None,
    card: str | None,
    content: str,
    image_count: int = 0,
    missing_image_count: int = 0,
    attachments: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build the nested immutable snapshot used by a message reply."""
    payload: dict[str, object] = {
        "schema": AGENT_MESSAGE_REF_SCHEMA,
        "sender": build_agent_sender_payload(
            user_id=user_id,
            display_name=display_name,
            nickname=nickname,
            card=card,
            role=role,
        ),
        "content": content,
    }
    if message_id is not None:
        payload["message_id"] = str(message_id)
    if image_count or missing_image_count:
        media: dict[str, object] = {}
        if image_count:
            media["image_count"] = image_count
        if missing_image_count:
            media["missing_image_count"] = missing_image_count
        payload["media"] = media
    if attachments:
        payload["attachments"] = sorted(
            attachments,
            key=lambda attachment: (
                str(attachment.get("file_name", "")),
                str(attachment.get("kind", "")),
                str(attachment.get("path", "")),
            ),
        )
    return payload


__all__ = [
    "AGENT_MESSAGE_REF_SCHEMA",
    "AGENT_MESSAGE_SCHEMA",
    "ATTACHMENT_ONLY_CONTEXT_MARKER",
    "CONVERSATION_SUMMARY_SCHEMA",
    "DIRECT_MENTION_CONTEXT_MARKER",
    "EMPTY_MESSAGE_CONTEXT_MARKER",
    "REPLY_ONLY_CONTEXT_MARKER",
    "build_agent_attachment_payload",
    "build_agent_message_payload",
    "build_agent_message_ref_payload",
    "build_agent_sender_payload",
    "count_image_placeholders",
    "content_for_persisted_images",
    "serialize_agent_payload",
]
