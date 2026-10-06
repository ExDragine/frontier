"""``MessageDatabase``: message rows, rendered history and counters.

The class body keeps the order and text of the historical single-module
implementation.  Search lives in :mod:`utils.database.search` and the
attachment API in :mod:`utils.database.attachments`; both are mixed in so
``MessageDatabase`` keeps its previous public surface.
"""

import json
import os

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, desc, func, select

from utils.agents.message_envelope import content_for_persisted_images, serialize_agent_payload

from .attachments import _message_workspace_key, _MessageAttachmentFacadeMixin, _MessageAttachmentManager
from .engine import _run_database, get_engine
from .fts import ensure_message_fts
from .models import (
    MESSAGE_SOURCE_TYPE_FORWARD_NODE,
    MESSAGE_SOURCE_TYPE_NORMAL,
    GroupSettings,
    Message,
    MessageAttachment,
    MessageInsertResult,
)
from .rows import (
    _REPLY_CONTEXT_UNSET,
    _attachment_agent_payload,
    _find_message,
    _message_agent_payload,
    _refresh_message_model_state,
)
from .schema import ensure_database_performance_indexes, platform_message_key, validate_database_schema
from .search import _MessageSearchMixin


class MessageDatabase(_MessageAttachmentFacadeMixin, _MessageSearchMixin):
    def __init__(self):
        self.engine = get_engine()
        validate_database_schema(self.engine, Message, MessageAttachment)
        self._attachments = _MessageAttachmentManager(self.engine)
        Message.metadata.create_all(self.engine)
        MessageAttachment.metadata.create_all(self.engine)
        GroupSettings.metadata.create_all(self.engine)
        ensure_database_performance_indexes(self.engine)
        ensure_message_fts(self.engine)

    async def insert(
        self,
        time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        user_name: str | None,
        role: str,
        content: str,
        raw_segments_json: str | None = None,
        normalized_version: int = 0,
        normalized_status: str = "legacy",
        source_type: str = MESSAGE_SOURCE_TYPE_NORMAL,
        parent_msg_id: int | None = None,
        parent_msg_time: int | None = None,
        parent_forward_id: str | None = None,
        user_nickname: str | None = None,
        user_card: str | None = None,
        reply_context_json: str | None = None,
        sender_user_id: int | None = None,
        bot_user_id: int | None = None,
        directly_mentions_bot: bool = False,
    ) -> MessageInsertResult:
        def _do():
            with Session(self.engine, expire_on_commit=False) as session:
                resolved_sender_user_id = sender_user_id
                if resolved_sender_user_id is None and (group_id is not None or role != "assistant"):
                    resolved_sender_user_id = user_id
                message = Message(
                    time=time,
                    platform_key=platform_message_key(
                        msg_id=msg_id, user_id=user_id, group_id=group_id,
                        bot_user_id=bot_user_id, source_type=source_type,
                    ),
                    msg_id=msg_id,
                    user_id=user_id,
                    group_id=group_id,
                    user_name=user_name,
                    role=role,
                    content=content,
                    raw_segments_json=raw_segments_json,
                    normalized_version=normalized_version,
                    normalized_status=normalized_status,
                    source_type=source_type,
                    parent_msg_id=parent_msg_id,
                    parent_msg_time=parent_msg_time,
                    parent_forward_id=parent_forward_id,
                    user_nickname=user_nickname,
                    user_card=user_card,
                    reply_context_json=reply_context_json,
                    sender_user_id=resolved_sender_user_id,
                    bot_user_id=bot_user_id,
                    directly_mentions_bot=directly_mentions_bot,
                )
                session.add(message)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    if message.platform_key is None:
                        raise
                    existing = session.exec(
                        select(Message).where(Message.platform_key == message.platform_key)
                    ).first()
                    if existing is None:
                        raise
                    return MessageInsertResult(message_id=existing.id, time=existing.time, inserted=False)
                return MessageInsertResult(message_id=message.id, time=message.time, inserted=True)

        return await _run_database(self.engine, _do)

    async def select(
        self,
        user_id: int | None = None,
        group_id: int | None = None,
        query_numbers: int = 20,
        before_time: int | None = None,
    ):
        def _do():
            with Session(self.engine) as session:
                if group_id is not None:
                    statement = select(Message).where(Message.group_id == group_id)
                elif user_id:
                    statement = (
                        select(Message)
                        .where(Message.user_id == user_id)
                        .where(Message.group_id.is_(None))  # type: ignore
                    )
                else:
                    return None
                statement = statement.where(Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL)
                if before_time is not None:
                    statement = statement.where(Message.time < before_time)
                statement = statement.order_by(desc(Message.time), desc(Message.id)).limit(query_numbers)
                results = session.exec(statement)
                return results.all()

        return await _run_database(self.engine, _do)

    async def count_intervening_group_messages(
        self, *, group_id: int, bot_user_id: int, user_id: int,
        after_time: int, after_message_id: int | None, limit: int = 5,
    ) -> int:
        """Count other members' new messages, stopping at the reply threshold."""
        def read():
            conditions = [
                Message.group_id == group_id,
                Message.bot_user_id == bot_user_id,
                Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL,
                Message.role == "user",
                Message.user_id != user_id,
                Message.user_id != bot_user_id,
            ]
            if after_message_id is not None:
                conditions.append(Message.id > after_message_id)
            else:
                conditions.append(Message.time > after_time)
            with Session(self.engine) as session:
                return len(session.exec(select(Message.id).where(*conditions).limit(limit)).all())

        return await _run_database(self.engine, read)

    async def select_recent_media_message(
        self,
        *,
        user_id: int,
        group_id: int | None,
        before_time: int,
        after_time: int,
        limit: int = 20,
    ) -> Message | None:
        """Return the newest same-sender message carrying raw image/file segments.

        This deliberately uses the strict current QQ scope rather than the
        broader private-memory compatibility scope. Media paths and Milky file
        identifiers must never cross a group/private workspace boundary.
        """

        def _do():
            with Session(self.engine) as session:
                conditions = [
                    Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL,
                    Message.role == "user",
                    Message.time < before_time,
                    Message.time >= after_time,
                    Message.raw_segments_json.is_not(None),
                ]
                if group_id is None:
                    conditions.extend((Message.group_id.is_(None), Message.user_id == user_id))
                else:
                    conditions.extend((Message.group_id == group_id, Message.user_id == user_id))
                statement = (
                    select(Message)
                    .where(*conditions)
                    .order_by(desc(Message.time), desc(Message.id))
                    .limit(max(1, min(limit, 100)))
                )
                for message in session.exec(statement).all():
                    try:
                        segments = json.loads(message.raw_segments_json or "[]")
                    except json.JSONDecodeError:
                        continue
                    if isinstance(segments, list) and any(
                        isinstance(segment, dict) and segment.get("type") in {"image", "file"}
                        for segment in segments
                    ):
                        return message
                return None

        return await _run_database(self.engine, _do)

    async def select_by_msg_id(
        self,
        *,
        msg_id: int,
        group_id: int | None,
        peer_user_id: int | None = None,
    ) -> Message | None:
        if group_id is None and peer_user_id is None:
            raise ValueError("私聊消息查询必须提供 peer_user_id")

        def _do():
            with Session(self.engine) as session:
                statement = select(Message).where(Message.msg_id == msg_id)
                statement = statement.where(Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL)
                if group_id is None:
                    statement = statement.where(Message.group_id.is_(None))  # type: ignore
                    statement = statement.where(Message.user_id == peer_user_id)
                else:
                    statement = statement.where(Message.group_id == group_id)
                statement = statement.order_by(desc(Message.time), desc(Message.id)).limit(1)
                return session.exec(statement).first()

        return await _run_database(self.engine, _do)

    async def update_message_normalization(
        self,
        *,
        time: int,
        content: str,
        raw_segments_json: str | None,
        normalized_version: int,
        normalized_status: str,
        message_id: int | None = None,
    ) -> None:
        def _do():
            with Session(self.engine) as session:
                message = _find_message(session, time, message_id=message_id)
                if message is None:
                    return
                message.content = content
                message.model_content = None
                if raw_segments_json is not None:
                    message.raw_segments_json = raw_segments_json
                message.normalized_version = normalized_version
                message.normalized_status = normalized_status
                session.add(message)
                session.flush()
                _refresh_message_model_state(session, time, message_id=message.id)
                session.commit()

        await _run_database(self.engine, _do)

    async def finalize_message_context(
        self,
        *,
        time: int,
        message_id: int | None = None,
        reply_context_json: str | None | object = _REPLY_CONTEXT_UNSET,
    ) -> None:
        """Rebuild the model-facing view after lazy attachments resolve."""

        def _do():
            with Session(self.engine) as session:
                _refresh_message_model_state(
                    session,
                    time,
                    message_id=message_id,
                    reply_context_json=reply_context_json,
                )
                session.commit()

        await _run_database(self.engine, _do)

    async def replace_derived_messages(
        self,
        *,
        parent_msg_time: int,
        parent_msg_id: int | None,
        user_id: int,
        group_id: int | None,
        role: str,
        derived_messages: list,
        normalized_version: int,
        parent_message_id: int | None = None,
    ) -> None:
        def _do():
            with Session(self.engine) as session:
                parent = _find_message(
                    session, parent_msg_time, message_id=parent_message_id,
                    scope=(user_id, group_id), msg_id=parent_msg_id,
                )
                resolved_parent_id = parent.id if parent is not None else parent_message_id
                statement = select(Message).where(Message.source_type != MESSAGE_SOURCE_TYPE_NORMAL)
                if resolved_parent_id is not None:
                    statement = statement.where(Message.parent_message_id == resolved_parent_id)
                else:
                    statement = statement.where(
                        Message.parent_msg_time == parent_msg_time,
                        Message.parent_message_id.is_(None),
                        Message.group_id == group_id,
                    )
                    if group_id is None:
                        statement = statement.where(Message.user_id == user_id)
                existing = session.exec(statement).all()
                for message in existing:
                    session.delete(message)

                for item in derived_messages:
                    message = Message(
                        time=getattr(item, "time_ms", None) or parent_msg_time,
                        msg_id=None,
                        user_id=user_id,
                        group_id=group_id,
                        user_name=getattr(item, "sender_name", None),
                        role=role,
                        content=getattr(item, "content", ""),
                        raw_segments_json=getattr(item, "raw_segments_json", None),
                        normalized_version=normalized_version,
                        normalized_status="complete",
                        source_type=MESSAGE_SOURCE_TYPE_FORWARD_NODE,
                        parent_msg_id=parent_msg_id,
                        parent_msg_time=parent_msg_time,
                        parent_message_id=resolved_parent_id,
                        parent_forward_id=getattr(item, "forward_id", None),
                    )
                    session.add(message)
                session.commit()

        await _run_database(self.engine, _do)

    async def prepare_session_history(
        self, *, bot_user_id: int, user_id: int, group_id: int | None,
        before_time: int, before_message_id: int, query_numbers: int,
        after_message_id: int | None = None,
    ) -> list[dict[str, object]]:
        """Read only this bot's records visible when the triggering message arrived.

        The ID bound excludes later/backdated inserts; the time bound preserves
        the existing QQ snapshot contract. Null/ambiguous bot ownership is excluded.
        """
        def read():
            conditions = [
                Message.bot_user_id == bot_user_id,
                Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL,
                Message.time < before_time,
                Message.id < before_message_id,
            ]
            if group_id is None:
                conditions.extend([Message.group_id.is_(None), Message.user_id == user_id])
            else:
                conditions.append(Message.group_id == group_id)
            if after_message_id is not None:
                conditions.append(Message.id > after_message_id)
            with Session(self.engine) as session:
                return list(reversed(session.exec(
                    select(Message).where(*conditions).order_by(desc(Message.time), desc(Message.id)).limit(query_numbers)
                ).all()))

        records = await _run_database(self.engine, read)
        rendered = await self.prepare_message_records(
            records, accessible_workspace_key=_message_workspace_key(user_id, group_id),
        )
        return [
            {**message, "id": f"qq:{bot_user_id}:message:{record.id}"}
            for record, message in zip(records, rendered, strict=True)
        ]

    async def prepare_message(
        self,
        user_id: int | None = None,
        group_id: int | None = None,
        query_numbers: int = 20,
        before_time: int | None = None,
    ):
        messages = await self.select(
            user_id=user_id,
            group_id=group_id,
            query_numbers=query_numbers,
            before_time=before_time,
        )
        if not messages:
            return []
        messages = list(reversed(messages))
        workspace_user_id = user_id if user_id is not None else messages[-1].user_id
        if before_time is None:
            messages = messages[:-1]
        return await self.prepare_message_records(
            messages,
            accessible_workspace_key=_message_workspace_key(workspace_user_id, group_id),
        )

    async def prepare_message_records(
        self,
        messages: list[Message],
        *,
        accessible_workspace_key: str | None = None,
    ) -> list[dict[str, object]]:  # noqa: C901
        """Render already-selected records in chronological order for an LLM."""
        if not messages:
            return []
        messages = sorted(messages, key=lambda message: (message.time, message.id or 0))
        messages_seq: list[dict[str, object]] = []

        all_msg_times = [m.time for m in messages]

        self._attachments.engine = self.engine
        attachments_by_time = await self._attachments.select_by_msg_times(all_msg_times)

        for message in messages:
            msg_attachments = [
                attachment for attachment in attachments_by_time.get(message.time, [])
                if (
                    attachment.message_id == message.id
                    if attachment.message_id is not None
                    else attachment.group_id == message.group_id
                    and attachment.user_id == message.user_id
                    and attachment.msg_id in (None, message.msg_id)
                )
            ]
            attachment_refs = []
            missing_kinds: list[str] = []
            message_workspace_key = _message_workspace_key(message.user_id, message.group_id)
            same_workspace = (
                accessible_workspace_key is None
                or message_workspace_key == accessible_workspace_key
            )
            for attachment in msg_attachments:
                if (
                    accessible_workspace_key is not None
                    and attachment.workspace_key != accessible_workspace_key
                ):
                    # Private history intentionally includes this user's own
                    # group utterances, but not another workspace's files.
                    continue
                full_path = os.path.join(os.getcwd(), attachment.physical_path)
                if not os.path.exists(full_path):
                    missing_kinds.append(attachment.kind)
                    continue
                attachment_refs.append(_attachment_agent_payload(attachment))
            content_text = content_for_persisted_images(
                message.content,
                sum(attachment.get("kind") == "image" for attachment in attachment_refs),
            )
            if missing_kinds:
                content_text += "\n" + " ".join(f"[{kind}附件已过期]" for kind in missing_kinds)

            payload = _message_agent_payload(
                message,
                content=content_text,
                attachments=attachment_refs,
                # Private context may include the user's own group utterances,
                # but a quoted group participant is not part of that private
                # scope. Keep the utterance while dropping the foreign snapshot.
                include_reply_to=same_workspace,
            )
            # Keep every original platform message atomic and use the string
            # content form accepted by all supported provider protocols.
            messages_seq.append(
                {
                    "role": message.role,
                    "content": serialize_agent_payload(payload),
                }
            )

        return messages_seq

    async def count_group_messages_since(self, *, group_id: int, since_time: int) -> int:
        def _do():
            with Session(self.engine) as session:
                statement = (
                    select(func.count())
                    .select_from(Message)
                    .where(Message.group_id == group_id)
                    .where(Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL)
                    .where(Message.time >= since_time)
                )
                return int(session.exec(statement).one())

        return await _run_database(self.engine, _do)

    async def latest_group_role_message_time(self, *, group_id: int, role: str) -> int | None:
        def _do():
            with Session(self.engine) as session:
                statement = (
                    select(Message.time)
                    .where(Message.group_id == group_id)
                    .where(Message.role == role)
                    .where(Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL)
                    .order_by(desc(Message.time), desc(Message.id))
                    .limit(1)
                )
                return session.exec(statement).first()

        return await _run_database(self.engine, _do)

    async def select_message_timeline(
        self,
        message_id: int,
        *,
        window_ms: int = 5 * 60 * 1000,
        limit: int = 100,
    ) -> list[Message]:
        """Return the same conversation around a persisted message hit."""
        bounded_window = max(0, min(window_ms, 24 * 60 * 60 * 1000))
        bounded_limit = max(1, min(limit, 500))

        def _do():
            with Session(self.engine) as session:
                anchor = session.exec(
                    select(Message)
                    .where(Message.id == message_id)
                    .where(Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL)
                ).first()
                if anchor is None:
                    return []
                conditions = [
                    Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL,
                    Message.time >= anchor.time - bounded_window,
                    Message.time <= anchor.time + bounded_window,
                ]
                if anchor.group_id is None:
                    conditions.extend((Message.group_id.is_(None), Message.user_id == anchor.user_id))
                else:
                    conditions.append(Message.group_id == anchor.group_id)
                return session.exec(
                    select(Message)
                    .where(*conditions)
                    .order_by(Message.time, Message.id)
                    .limit(bounded_limit)
                ).all()

        return await _run_database(self.engine, _do)
