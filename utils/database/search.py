"""Full-text and LIKE message search over the persisted message table."""

import logging

from sqlalchemy import Engine, text
from sqlmodel import Session, col, desc, select

from .engine import _run_database
from .fts import MESSAGE_FTS_MIN_QUERY_LENGTH, _fts_query
from .models import MESSAGE_SOURCE_TYPE_NORMAL, Message, MessageSearchResult

logger = logging.getLogger(__name__)


class _MessageSearchMixin:
    """Search methods mixed into :class:`MessageDatabase`."""

    engine: Engine

    @staticmethod
    def _like_pattern(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped}%"

    def _can_use_fts(self, content_query: str | None) -> bool:
        if not content_query or len(content_query.strip()) < MESSAGE_FTS_MIN_QUERY_LENGTH:
            return False
        with self.engine.connect() as conn:
            return (
                conn.execute(
                    text("SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'message_fts' LIMIT 1")
                ).first()
                is not None
            )

    def _search_messages_fts_details(
        self,
        session: Session,
        *,
        group_id: int | None,
        user_id: int | None,
        content_query: str,
        target_user_id: int | None,
        target_user_name: str | None,
        msg_id: int | None,
        start_time: int | None,
        end_time: int | None,
        role: str | None,
        limit: int,
        offset: int,
        sort: str,
    ) -> list[MessageSearchResult]:
        params: dict[str, object] = {
            "fts_query": _fts_query(content_query),
            "limit": max(1, min(limit, 500)),
            "scope": "private" if group_id is None else "group",
            "group_id": group_id,
            "user_id": user_id,
            "target_user_id_enabled": 0,
            "target_user_id": target_user_id,
            "target_user_name": self._like_pattern(target_user_name) if target_user_name else None,
            "msg_id": msg_id,
            "start_time": start_time,
            "end_time": end_time,
            "role": role,
            "offset": max(0, min(offset, 5000)),
        }

        if group_id is None:
            if user_id is None:
                return []
            if target_user_id is not None and target_user_id != user_id:
                return []
        else:
            if target_user_id is not None:
                params["target_user_id_enabled"] = 1

        if sort == "relevance":
            query = text(
                """
            SELECT m.id, bm25(message_fts) AS score,
                   snippet(message_fts, 0, '[', ']', '…', 12) AS snippet
            FROM message_fts
            JOIN message AS m ON m.id = message_fts.rowid
            WHERE message_fts MATCH :fts_query
              AND (
                (:scope = 'group' AND m.group_id = :group_id)
                OR (:scope = 'private' AND m.user_id = :user_id AND m.group_id IS NULL)
              )
              AND m.source_type = 'message'
              AND (:target_user_id_enabled = 0 OR m.user_id = :target_user_id)
              AND (:target_user_name IS NULL OR m.user_name LIKE :target_user_name ESCAPE '\\')
              AND (:msg_id IS NULL OR m.msg_id = :msg_id)
              AND (:start_time IS NULL OR m.time >= :start_time)
              AND (:end_time IS NULL OR m.time <= :end_time)
              AND (:role IS NULL OR m.role = :role)
            ORDER BY score, m.time DESC, m.id DESC
            LIMIT :limit
            OFFSET :offset
                """
            )
        else:
            query = text(
                """
            SELECT m.id, bm25(message_fts) AS score,
                   snippet(message_fts, 0, '[', ']', '…', 12) AS snippet
            FROM message_fts
            JOIN message AS m ON m.id = message_fts.rowid
            WHERE message_fts MATCH :fts_query
              AND (
                (:scope = 'group' AND m.group_id = :group_id)
                OR (:scope = 'private' AND m.user_id = :user_id AND m.group_id IS NULL)
              )
              AND m.source_type = 'message'
              AND (:target_user_id_enabled = 0 OR m.user_id = :target_user_id)
              AND (:target_user_name IS NULL OR m.user_name LIKE :target_user_name ESCAPE '\\')
              AND (:msg_id IS NULL OR m.msg_id = :msg_id)
              AND (:start_time IS NULL OR m.time >= :start_time)
              AND (:end_time IS NULL OR m.time <= :end_time)
              AND (:role IS NULL OR m.role = :role)
            ORDER BY m.time DESC, m.id DESC
            LIMIT :limit
            OFFSET :offset
                """
            )

        rows = session.connection().execute(query, params).all()
        ids = [int(row[0]) for row in rows]
        if not ids:
            return []

        messages = session.exec(select(Message).where(col(Message.id).in_(ids))).all()
        messages_by_id = {message.id: message for message in messages}
        return [
            MessageSearchResult(
                message=messages_by_id[message_id],
                score=float(row[1]) if row[1] is not None else None,
                snippet=str(row[2]) if row[2] is not None else None,
            )
            for row, message_id in zip(rows, ids, strict=True)
            if message_id in messages_by_id
        ]

    def _search_messages_fts(self, session: Session, **kwargs) -> list[Message]:
        return [result.message for result in self._search_messages_fts_details(session, **kwargs)]

    async def search_messages(  # noqa: C901
        self,
        *,
        group_id: int | None,
        user_id: int | None,
        content_query: str | None = None,
        target_user_id: int | None = None,
        target_user_name: str | None = None,
        msg_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        role: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "time",
    ) -> list[Message]:
        def _do():  # noqa: C901
            with Session(self.engine) as session:
                if self._can_use_fts(content_query):
                    try:
                        return self._search_messages_fts(
                            session,
                            group_id=group_id,
                            user_id=user_id,
                            content_query=content_query or "",
                            target_user_id=target_user_id,
                            target_user_name=target_user_name,
                            msg_id=msg_id,
                            start_time=start_time,
                            end_time=end_time,
                            role=role,
                            limit=limit,
                            offset=offset,
                            sort=sort,
                        )
                    except Exception as exc:
                        logger.warning("FTS5 message search failed; falling back to LIKE: %s: %s", type(exc).__name__, exc)

                statement = select(Message).where(Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL)
                if group_id is None:
                    if user_id is None:
                        return []
                    statement = statement.where(Message.user_id == user_id).where(Message.group_id.is_(None))  # type: ignore
                    if target_user_id is not None and target_user_id != user_id:
                        return []
                else:
                    statement = statement.where(Message.group_id == group_id)
                    if target_user_id is not None:
                        statement = statement.where(Message.user_id == target_user_id)

                if content_query:
                    statement = statement.where(
                        col(Message.content).like(self._like_pattern(content_query), escape="\\")
                    )
                if target_user_name:
                    statement = statement.where(
                        col(Message.user_name).like(self._like_pattern(target_user_name), escape="\\")
                    )
                if msg_id is not None:
                    statement = statement.where(Message.msg_id == msg_id)
                if start_time is not None:
                    statement = statement.where(Message.time >= start_time)
                if end_time is not None:
                    statement = statement.where(Message.time <= end_time)
                if role is not None:
                    statement = statement.where(Message.role == role)

                statement = (
                    statement.order_by(desc(Message.time), desc(Message.id))
                    .limit(max(1, min(limit, 500)))
                    .offset(max(0, min(offset, 5000)))
                )
                return session.exec(statement).all()

        return await _run_database(self.engine, _do)

    async def search_message_details(  # noqa: C901
        self,
        *,
        group_id: int | None,
        user_id: int | None,
        content_query: str,
        target_user_id: int | None = None,
        target_user_name: str | None = None,
        msg_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        role: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "relevance",
    ) -> list[MessageSearchResult]:
        """Search messages while retaining FTS score and a display snippet.

        ``search_messages`` remains the compatibility API returning ``Message``
        objects. This method is for callers that need ranking metadata without
        exposing FTS implementation details in the regular message model.
        """
        cleaned_query = content_query.strip()
        if not cleaned_query:
            return []
        if group_id is None and user_id is None:
            return []
        if group_id is None and target_user_id is not None and target_user_id != user_id:
            return []

        def _do():
            with Session(self.engine) as session:
                if self._can_use_fts(cleaned_query):
                    try:
                        return self._search_messages_fts_details(
                            session,
                            group_id=group_id,
                            user_id=user_id,
                            content_query=cleaned_query,
                            target_user_id=target_user_id,
                            target_user_name=target_user_name,
                            msg_id=msg_id,
                            start_time=start_time,
                            end_time=end_time,
                            role=role,
                            limit=limit,
                            offset=offset,
                            sort=sort,
                        )
                    except Exception as exc:
                        logger.warning("FTS5 message detail search failed; falling back to LIKE: %s: %s", type(exc).__name__, exc)
                conditions = [Message.source_type == MESSAGE_SOURCE_TYPE_NORMAL]
                if group_id is None:
                    conditions.extend((Message.group_id.is_(None), Message.user_id == user_id))
                else:
                    conditions.append(Message.group_id == group_id)
                    if target_user_id is not None:
                        conditions.append(Message.user_id == target_user_id)
                conditions.append(col(Message.content).like(self._like_pattern(cleaned_query), escape="\\"))
                if target_user_name:
                    conditions.append(
                        col(Message.user_name).like(self._like_pattern(target_user_name), escape="\\")
                    )
                if msg_id is not None:
                    conditions.append(Message.msg_id == msg_id)
                if start_time is not None:
                    conditions.append(Message.time >= start_time)
                if end_time is not None:
                    conditions.append(Message.time <= end_time)
                if role is not None:
                    conditions.append(Message.role == role)
                messages = session.exec(
                    select(Message)
                    .where(*conditions)
                    .order_by(desc(Message.time), desc(Message.id))
                    .limit(max(1, min(limit, 500)))
                    .offset(max(0, min(offset, 5000)))
                ).all()
                return [
                    MessageSearchResult(message=message, snippet=message.content[:200])
                    for message in messages
                ]

        return await _run_database(self.engine, _do)
