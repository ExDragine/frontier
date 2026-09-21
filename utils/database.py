import asyncio
import hashlib
import json
import logging
import os
import posixpath
import threading
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy import Engine, Index, UniqueConstraint, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, col, create_engine, desc, func, select

from utils.agents.message_envelope import (
    build_agent_attachment_payload,
    build_agent_message_payload,
    content_for_persisted_images,
    serialize_agent_payload,
)
from utils.agents.runtime import conversation_workspace_key
from utils.media import ResolvedMedia, resolve_media

DATABASE_FILE = "sqlite:///frontier.db"
SQLITE_BUSY_TIMEOUT_MS = 5000
SQLITE_CACHE_SIZE_KIB = 65536
SQLITE_MMAP_SIZE_BYTES = 256 * 1024 * 1024
MESSAGE_FTS_MIN_QUERY_LENGTH = 3
MESSAGE_SOURCE_TYPE_NORMAL = "message"
MESSAGE_SOURCE_TYPE_FORWARD_NODE = "forward_node"
_ATTACHMENT_KIND_DIRECTORIES = {
    "image": "images",
    "audio": "audio",
    "video": "videos",
    "file": "files",
}
logger = logging.getLogger(__name__)
_ATTACHMENT_WRITE_LOCKS = tuple(threading.Lock() for _ in range(64))


@contextmanager
def _lock_attachment_paths(paths: list[str]):
    indexes = sorted(
        {
            int.from_bytes(hashlib.sha256(os.path.abspath(path).encode("utf-8")).digest()[:2], "big")
            % len(_ATTACHMENT_WRITE_LOCKS)
            for path in paths
        }
    )
    locks = [_ATTACHMENT_WRITE_LOCKS[index] for index in indexes]
    for lock in locks:
        lock.acquire()
    try:
        yield
    finally:
        for lock in reversed(locks):
            lock.release()


async def _run_in_thread(func, *args, **kwargs):
    """将同步数据库操作放入线程池执行，避免阻塞 asyncio 事件循环。"""
    return await asyncio.to_thread(func, *args, **kwargs)


def _engine_uses_memory_database(engine: Engine) -> bool:
    return engine.url.get_backend_name() == "sqlite" and _is_memory_database(str(engine.url))


async def _run_database(engine: Engine, func, *args, **kwargs):
    if _engine_uses_memory_database(engine):
        return func(*args, **kwargs)
    return await _run_in_thread(func, *args, **kwargs)


def _is_memory_database(database_url: str) -> bool:
    return database_url in {"sqlite://", "sqlite:///:memory:"} or database_url.endswith(":memory:")


def _configure_sqlite_connection(dbapi_connection, _connection_record, *, memory_database: bool) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        if not memory_database:
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute(f"PRAGMA cache_size=-{SQLITE_CACHE_SIZE_KIB}")
        cursor.execute(f"PRAGMA mmap_size={SQLITE_MMAP_SIZE_BYTES}")
        cursor.execute("PRAGMA optimize=0x10002")
    finally:
        cursor.close()


@lru_cache(maxsize=8)
def _cached_engine(database_url: str) -> Engine:
    kwargs: dict[str, object] = {}
    memory_database = _is_memory_database(database_url)
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    if memory_database:
        kwargs["poolclass"] = StaticPool
    engine = create_engine(database_url, **kwargs)
    event.listen(
        engine,
        "connect",
        lambda dbapi_connection, connection_record: _configure_sqlite_connection(
            dbapi_connection,
            connection_record,
            memory_database=memory_database,
        ),
    )
    return engine


def get_engine(database_url: str | None = None) -> Engine:
    return _cached_engine(database_url or DATABASE_FILE)


def ensure_database_performance_indexes(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    statements: list[str] = []

    if "message" in table_names:
        statements.extend(
            [
                "CREATE INDEX IF NOT EXISTS ix_message_time_id ON message (time, id)",
                "CREATE INDEX IF NOT EXISTS ix_message_parent_message_id ON message (parent_message_id)",
                "CREATE INDEX IF NOT EXISTS ix_message_group_time ON message (group_id, time DESC)",
                "CREATE INDEX IF NOT EXISTS ix_message_user_group_time ON message (user_id, group_id, time DESC)",
                "CREATE INDEX IF NOT EXISTS ix_message_group_role_time ON message (group_id, role, time DESC)",
                "CREATE INDEX IF NOT EXISTS ix_message_group_msg_id_time ON message (group_id, msg_id, time DESC)",
                "CREATE INDEX IF NOT EXISTS ix_message_source_parent ON message (source_type, parent_msg_time)",
                (
                    "CREATE INDEX IF NOT EXISTS ix_message_private_user_time "
                    "ON message (user_id, time DESC) WHERE group_id IS NULL"
                ),
            ]
        )

    if "messageattachment" in table_names:
        statements.extend(
            [
                (
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_messageattachment_path_msg_time "
                    "ON messageattachment (physical_path, msg_time)"
                ),
                "CREATE INDEX IF NOT EXISTS ix_messageattachment_msg_time ON messageattachment (msg_time)",
                "CREATE INDEX IF NOT EXISTS ix_messageattachment_expires_at ON messageattachment (expires_at)",
                "CREATE INDEX IF NOT EXISTS ix_messageattachment_scope ON messageattachment (workspace_key, kind)",
            ]
        )

    if "taskexecutionhistory" in table_names:
        statements.extend(
            [
                (
                    "CREATE INDEX IF NOT EXISTS ix_taskhistory_job_time "
                    "ON taskexecutionhistory (job_id, execution_time DESC)"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS ix_taskhistory_status_time "
                    "ON taskexecutionhistory (status, execution_time DESC)"
                ),
            ]
        )

    if "group_settings" in table_names:
        statements.extend(
            [
                "CREATE INDEX IF NOT EXISTS ix_group_settings_group_key ON group_settings (group_id, key)",
            ]
        )

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
        conn.execute(text("PRAGMA optimize"))


def validate_database_schema(engine: Engine, *models: type[SQLModel]) -> None:
    """Reject incompatible existing tables without rewriting schema or user data."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    for model in models:
        table = model.__table__
        if table.name not in existing:
            continue  # create_all initializes new databases below.
        columns = {column["name"] for column in inspector.get_columns(table.name)}
        missing = set(table.columns.keys()) - columns
        primary_key = inspector.get_pk_constraint(table.name)["constrained_columns"]
        if missing or primary_key != list(table.primary_key.columns.keys()):
            detail = f"缺少列 {', '.join(sorted(missing))}" if missing else f"主键不匹配 {primary_key}"
            raise RuntimeError(
                f"数据库表 {table.name} 结构过旧或不兼容：{detail}。"
                "请先使用包含迁移工具的历史版本升级数据库。"
            )


def platform_message_key(*, msg_id, user_id, group_id, bot_user_id, source_type="message") -> str | None:
    """Build the live platform-event deduplication key independently of migrations."""
    if msg_id is None or source_type != "message":
        return None
    scope = f"group:{group_id}" if group_id is not None else f"dm:{user_id}"
    return f"milky:{bot_user_id or 0}:{scope}:{msg_id}"


def _table_exists(conn, table_name: str) -> bool:
    return (
        conn.execute(
            text("SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = :table_name LIMIT 1"),
            {"table_name": table_name},
        ).first()
        is not None
    )


def _safe_table_count(conn, table_name: str) -> int | None:
    if not _table_exists(conn, table_name):
        return None
    quoted = '"' + table_name.replace('"', '""') + '"'
    return int(conn.execute(text(f"SELECT count(*) FROM {quoted}")).scalar_one())  # noqa: S608


def get_database_diagnostics(engine: Engine | None = None) -> dict[str, object]:
    engine = engine or get_engine()
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    table_diagnostics: dict[str, dict[str, object]] = {}
    fts_diagnostics: dict[str, dict[str, object]] = {}

    with engine.connect() as conn:
        for table_name in sorted(table_names):
            table_diagnostics[table_name] = {
                "row_count": _safe_table_count(conn, table_name),
                "indexes": sorted(
                    index["name"] for index in inspector.get_indexes(table_name) if index["name"] is not None
                ),
            }

        for fts_table in ["message_fts"]:
            fts_diagnostics[fts_table] = {
                "exists": _table_exists(conn, fts_table),
                "row_count": _safe_table_count(conn, fts_table),
            }

        pragmas = {
            name: conn.exec_driver_sql(f"PRAGMA {name}").scalar()
            for name in ["journal_mode", "synchronous", "foreign_keys", "busy_timeout", "cache_size", "mmap_size"]
        }
        checkpoint = conn.exec_driver_sql("PRAGMA wal_checkpoint(PASSIVE)").first()

        db_path = getattr(engine.url, "database", None)
        db_size = os.path.getsize(db_path) if db_path and os.path.exists(db_path) else None
        wal_path = f"{db_path}-wal" if db_path else None
        wal_size = os.path.getsize(wal_path) if wal_path and os.path.exists(wal_path) else 0

        return {
            "sqlite_version": conn.exec_driver_sql("SELECT sqlite_version()").scalar(),
            "fts5_supported": sqlite_supports_fts5(engine),
            "database_path": db_path,
            "database_size_bytes": db_size,
            "wal_size_bytes": wal_size,
            "pragmas": pragmas,
            "wal_checkpoint": tuple(checkpoint) if checkpoint is not None else None,
            "tables": table_diagnostics,
            "fts": fts_diagnostics,
        }


def run_database_maintenance(engine: Engine | None = None, *, checkpoint: bool = False) -> dict[str, object]:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(text("PRAGMA optimize"))
        result: dict[str, object] = {"optimized": True}
        if checkpoint:
            row = conn.exec_driver_sql("PRAGMA wal_checkpoint(PASSIVE)").first()
            result["wal_checkpoint"] = tuple(row) if row is not None else None
        return result


def cleanup_task_execution_history(
    engine: Engine | None = None,
    *,
    older_than: int | None = None,
    keep_per_job: int | None = None,
) -> int:
    if older_than is None and keep_per_job is None:
        return 0

    engine = engine or get_engine()
    with engine.begin() as conn:
        if not _table_exists(conn, "taskexecutionhistory"):
            return 0

        params = {
            "older_than": older_than,
            "keep_per_job": max(0, keep_per_job) if keep_per_job is not None else None,
        }
        conn.execute(
            text(
                """
                WITH ranked_history AS (
                    SELECT
                        id,
                        row_number() OVER (
                            PARTITION BY job_id
                            ORDER BY execution_time DESC, id DESC
                        ) AS rn
                    FROM taskexecutionhistory
                ),
                candidates AS (
                    SELECT id FROM taskexecutionhistory
                    WHERE :older_than IS NOT NULL AND execution_time < :older_than
                    UNION
                    SELECT id FROM ranked_history
                    WHERE :keep_per_job IS NOT NULL AND rn > :keep_per_job
                )
                DELETE FROM taskexecutionhistory
                WHERE id IN (SELECT id FROM candidates)
                """
            ),
            params,
        )
        deleted = int(conn.execute(text("SELECT changes()")).scalar_one())
        conn.execute(text("PRAGMA optimize"))
        return deleted


def sqlite_supports_fts5(engine: Engine) -> bool:
    with engine.begin() as conn:
        try:
            conn.execute(text("CREATE VIRTUAL TABLE temp.frontier_fts5_probe USING fts5(content)"))
        except Exception as exc:
            logger.warning("FTS5 probe failed during CREATE: %s: %s", type(exc).__name__, exc)
            return False
        try:
            conn.execute(text("DROP TABLE temp.frontier_fts5_probe"))
        except Exception as exc:
            logger.warning("FTS5 probe succeeded CREATE but failed DROP: %s: %s", type(exc).__name__, exc)
    return True


def ensure_message_fts(engine: Engine) -> None:
    if not sqlite_supports_fts5(engine):
        logger.info("FTS5 unavailable; message full-text index skipped")
        return

    with engine.begin() as conn:
        _ensure_message_fts_connection(conn)


def _ensure_message_fts_connection(conn) -> None:
    table_exists = _table_exists(conn, "message_fts")
    conn.execute(
        text(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS message_fts USING fts5(
                content,
                group_id UNINDEXED,
                user_id UNINDEXED,
                role UNINDEXED,
                user_name UNINDEXED,
                msg_id UNINDEXED,
                content='message',
                content_rowid='id',
                tokenize='trigram'
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS message_ai_fts AFTER INSERT ON message BEGIN
                INSERT INTO message_fts(rowid, content, group_id, user_id, role, user_name, msg_id)
                VALUES (new.id, new.content, new.group_id, new.user_id, new.role, new.user_name, new.msg_id);
            END
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS message_ad_fts AFTER DELETE ON message BEGIN
                INSERT INTO message_fts(message_fts, rowid, content, group_id, user_id, role, user_name, msg_id)
                VALUES ('delete', old.id, old.content, old.group_id, old.user_id, old.role, old.user_name, old.msg_id);
            END
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TRIGGER IF NOT EXISTS message_au_fts AFTER UPDATE ON message BEGIN
                INSERT INTO message_fts(message_fts, rowid, content, group_id, user_id, role, user_name, msg_id)
                VALUES ('delete', old.id, old.content, old.group_id, old.user_id, old.role, old.user_name, old.msg_id);
                INSERT INTO message_fts(rowid, content, group_id, user_id, role, user_name, msg_id)
                VALUES (new.id, new.content, new.group_id, new.user_id, new.role, new.user_name, new.msg_id);
            END
            """
        )
    )
    if not table_exists:
        message_count = _safe_table_count(conn, "message") or 0
        started_at = time.monotonic()
        logger.info("FTS5 message index rebuild started: rows=%s", message_count)
        conn.execute(text("INSERT INTO message_fts(message_fts) VALUES ('rebuild')"))
        elapsed = time.monotonic() - started_at
        logger.info("FTS5 message index rebuild finished: rows=%s elapsed=%.2fs", message_count, elapsed)
    else:
        logger.info("FTS5 message index ready")
    conn.execute(text("PRAGMA optimize"))

def _fts_query(value: str) -> str:
    escaped = value.replace('"', '""')
    return f'"{escaped}"'


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    model: str


class Message(SQLModel, table=True):
    __table_args__ = (
        Index("ux_message_platform_key", "platform_key", unique=True),
        {"sqlite_autoincrement": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    time: int
    platform_key: str | None = None
    parent_message_id: int | None = None
    msg_id: int | None = Field(default=None)
    user_id: int = Field(index=True)
    group_id: int | None = Field(default=None, index=True)
    user_name: str | None
    role: str
    content: str
    model_content: str | None = None
    raw_segments_json: str | None = None
    normalized_version: int = 0
    normalized_status: str = "legacy"
    source_type: str = MESSAGE_SOURCE_TYPE_NORMAL
    parent_msg_id: int | None = None
    parent_msg_time: int | None = None
    parent_forward_id: str | None = None
    user_nickname: str | None = None
    user_card: str | None = None
    reply_context_json: str | None = None
    sender_user_id: int | None = None
    bot_user_id: int | None = None
    directly_mentions_bot: bool = False


def resolve_message_sender_user_id(message: Message) -> int | None:
    """Return the real author while safely handling legacy private assistants."""
    sender_user_id = getattr(message, "sender_user_id", None)
    if sender_user_id is not None:
        return int(sender_user_id)
    if getattr(message, "group_id", None) is None and getattr(message, "role", "user") == "assistant":
        # Legacy private assistant rows stored the peer in user_id to preserve
        # scope. Treat the author as unknown instead of impersonating that peer.
        return None
    return int(message.user_id)


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


@dataclass(frozen=True, slots=True)
class MessageInsertResult:
    message_id: int
    time: int
    inserted: bool


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


class TimeStamp(SQLModel, table=True):
    name: str = Field(primary_key=True, index=True)
    id: str | None


class MessageAttachment(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("physical_path", "msg_time", name="uq_messageattachment_path_msg_time"),
    )

    id: int | None = Field(default=None, primary_key=True)
    msg_time: int = Field(index=True)
    message_id: int | None = Field(default=None, index=True)
    msg_id: int | None = Field(default=None, index=True)
    user_id: int = Field(index=True)
    group_id: int | None = Field(default=None, index=True)
    workspace_key: str = Field(index=True)
    kind: str = Field(index=True)
    source_type: str = "message"
    file_name: str
    mime_type: str | None = None
    file_size: int | None = None
    sha256: str | None = None
    physical_path: str
    virtual_path: str
    created_at: int
    expires_at: int
    metadata_json: str = "{}"


class GroupSettings(SQLModel, table=True):
    __tablename__ = "group_settings"
    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    key: str = Field(index=True)
    value: str
    updated_at: int


def _message_workspace_key(user_id: int, group_id: int | None) -> str:
    return conversation_workspace_key(user_id, group_id)


def _attachment_paths(user_id: int, group_id: int | None, *parts: str) -> tuple[str, str]:
    workspace_key = _message_workspace_key(user_id, group_id)
    physical_path = os.path.join("cache", "sandbox", "memory", workspace_key, *parts)
    virtual_path = posixpath.join("/memory", workspace_key, *parts)
    return physical_path, virtual_path


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _prune_empty_attachment_dirs(path: str) -> None:
    root = os.path.abspath(os.path.join(os.getcwd(), "cache", "sandbox", "memory"))
    current = os.path.abspath(os.path.dirname(path))
    while current.startswith(root) and current != root:
        try:
            os.rmdir(current)
        except OSError:
            break
        current = os.path.dirname(current)


class _PendingFileWrite:
    """Stage one attachment write and make replacement rollback-capable."""

    def __init__(self, target_path: str, data: bytes):
        self.target_path = target_path
        suffix = f"{os.getpid()}-{time.time_ns()}"
        self.temp_path = f"{target_path}.frontier-pending-{suffix}"
        self.backup_path: str | None = None
        self.installed = False
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            with open(self.temp_path, "xb") as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
        except Exception:
            self._remove(self.temp_path)
            raise

    @staticmethod
    def _remove(path: str | None) -> None:
        if path is None:
            return
        with suppress(FileNotFoundError):
            os.remove(path)

    def install(self) -> None:
        if os.path.exists(self.target_path):
            self.backup_path = f"{self.target_path}.frontier-backup-{os.getpid()}-{time.time_ns()}"
            os.replace(self.target_path, self.backup_path)
        try:
            os.replace(self.temp_path, self.target_path)
            self.installed = True
        except Exception:
            if self.backup_path is not None:
                os.replace(self.backup_path, self.target_path)
                self.backup_path = None
            raise

    def rollback(self) -> None:
        if self.backup_path is not None and os.path.exists(self.backup_path):
            os.replace(self.backup_path, self.target_path)
            self.backup_path = None
        elif self.installed:
            self._remove(self.target_path)
        self._remove(self.temp_path)

    def finish(self) -> None:
        for path in (self.backup_path, self.temp_path):
            try:
                self._remove(path)
            except OSError as exc:
                logger.warning("附件原子写入临时文件清理失败 %s: %s", path, exc)


class _MessageAttachmentManager:
    """通用附件索引：记录、查询和按 DB 清理文件。"""

    def __init__(self, engine):
        self.engine = engine

    async def insert_attachment(
        self,
        *,
        msg_time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        kind: str,
        physical_path: str,
        virtual_path: str,
        file_name: str,
        file_size: int | None,
        expires_at: int,
        source_type: str = "message",
        mime_type: str | None = None,
        sha256: str | None = None,
        metadata_json: str = "{}",
        message_id: int | None = None,
    ) -> MessageAttachment:
        def _do():
            workspace_key = _message_workspace_key(user_id, group_id)
            now_ms = int(time.time() * 1000)
            with Session(self.engine, expire_on_commit=False) as session:
                message = _find_message(
                    session, msg_time, message_id=message_id, scope=(user_id, group_id), msg_id=msg_id,
                )
                resolved_id = message.id if message is not None else message_id
                attachment = session.exec(
                    select(MessageAttachment).where(MessageAttachment.physical_path == physical_path).limit(1)
                ).first()
                affected_message_times = {msg_time}
                if attachment is None:
                    attachment = MessageAttachment(
                        msg_time=msg_time,
                        message_id=resolved_id,
                        msg_id=msg_id,
                        user_id=user_id,
                        group_id=group_id,
                        workspace_key=workspace_key,
                        kind=kind,
                        source_type=source_type,
                        file_name=file_name,
                        mime_type=mime_type,
                        file_size=file_size,
                        sha256=sha256,
                        physical_path=physical_path,
                        virtual_path=virtual_path,
                        created_at=now_ms,
                        expires_at=expires_at,
                        metadata_json=metadata_json,
                    )
                else:
                    affected_message_times.add(attachment.msg_time)
                    attachment.msg_time = msg_time
                    attachment.message_id = resolved_id
                    attachment.msg_id = msg_id
                    attachment.user_id = user_id
                    attachment.group_id = group_id
                    attachment.workspace_key = workspace_key
                    attachment.kind = kind
                    attachment.source_type = source_type
                    attachment.file_name = file_name
                    attachment.mime_type = mime_type
                    attachment.file_size = file_size
                    attachment.sha256 = sha256
                    attachment.virtual_path = virtual_path
                    attachment.expires_at = expires_at
                    attachment.metadata_json = metadata_json
                session.add(attachment)
                session.flush()
                _refresh_message_model_states(session, affected_message_times)
                session.commit()
                return attachment

        def _locked_do():
            with _lock_attachment_paths([physical_path]):
                return _do()

        return await _run_database(self.engine, _locked_do)

    async def insert_images(
        self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes],
        *, message_id: int | None = None,
    ) -> list[str]:
        attachments = await self.insert_media(
            msg_time=msg_time,
            msg_id=None,
            user_id=user_id,
            group_id=group_id,
            media=[resolve_media(image, "image") for image in images],
            message_id=message_id,
        )
        return [attachment.physical_path for attachment in attachments]

    async def insert_media(
        self,
        *,
        msg_time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        media: list[ResolvedMedia],
        source_type: str = "message",
        message_id: int | None = None,
    ) -> list[MessageAttachment]:
        """Persist downloaded media and create attachment rows in one DB operation."""

        def _do():
            from utils.configs import EnvConfig

            now_ms = int(time.time() * 1000)
            expires_ms = now_ms + EnvConfig.MEDIA_TTL_DAYS * 86400 * 1000
            workspace_key = _message_workspace_key(user_id, group_id)
            inserted: list[MessageAttachment] = []
            pending_writes: list[_PendingFileWrite] = []
            try:
                with Session(self.engine, expire_on_commit=False) as session:
                    message = _find_message(
                        session, msg_time, message_id=message_id, scope=(user_id, group_id), msg_id=msg_id,
                    )
                    resolved_id = message.id if message is not None else message_id
                    affected_message_times = {msg_time}
                    for index, item in enumerate(media):
                        stem = f"{msg_time}-m{resolved_id}" if resolved_id is not None else str(msg_time)
                        file_name = f"{stem}_{index}{item.extension}"
                        file_path, virtual_path = _attachment_paths(
                            user_id,
                            group_id,
                            _ATTACHMENT_KIND_DIRECTORIES[item.kind],
                            file_name,
                        )
                        full_path = os.path.join(os.getcwd(), file_path)
                        pending_writes.append(_PendingFileWrite(full_path, item.data))

                        attachment = session.exec(
                            select(MessageAttachment).where(MessageAttachment.physical_path == file_path).limit(1)
                        ).first()
                        if attachment is None:
                            attachment = MessageAttachment(
                                msg_time=msg_time,
                                message_id=resolved_id,
                                msg_id=msg_id,
                                user_id=user_id,
                                group_id=group_id,
                                workspace_key=workspace_key,
                                kind=item.kind,
                                source_type=source_type,
                                file_name=file_name,
                                mime_type=item.mime_type,
                                file_size=len(item.data),
                                sha256=_sha256_bytes(item.data),
                                physical_path=file_path,
                                virtual_path=virtual_path,
                                created_at=now_ms,
                                expires_at=expires_ms,
                            )
                        else:
                            affected_message_times.add(attachment.msg_time)
                            attachment.msg_time = msg_time
                            attachment.message_id = resolved_id
                            attachment.msg_id = msg_id
                            attachment.user_id = user_id
                            attachment.group_id = group_id
                            attachment.workspace_key = workspace_key
                            attachment.kind = item.kind
                            attachment.source_type = source_type
                            attachment.file_name = file_name
                            attachment.mime_type = item.mime_type
                            attachment.file_size = len(item.data)
                            attachment.sha256 = _sha256_bytes(item.data)
                            attachment.virtual_path = virtual_path
                            attachment.expires_at = expires_ms
                        session.add(attachment)
                        inserted.append(attachment)
                    session.flush()
                    _refresh_message_model_states(session, affected_message_times)
                    for pending_write in pending_writes:
                        pending_write.install()
                    session.commit()
            except Exception:
                for pending_write in reversed(pending_writes):
                    try:
                        pending_write.rollback()
                    except OSError as exc:
                        logger.warning("回滚未提交媒体文件失败 %s: %s", pending_write.target_path, exc)
                raise
            for pending_write in pending_writes:
                pending_write.finish()
            return inserted

        def _locked_do():
            target_paths = [
                _attachment_paths(
                    user_id,
                    group_id,
                    _ATTACHMENT_KIND_DIRECTORIES[item.kind],
                    f"{msg_time}_{index}{item.extension}",
                )[0]
                for index, item in enumerate(media)
            ]
            with _lock_attachment_paths(target_paths):
                return _do()

        return await _run_database(self.engine, _locked_do)

    async def select_by_msg_time(
        self, msg_time: int, *, message_id: int | None = None,
    ) -> list[MessageAttachment]:
        def _do():
            with Session(self.engine) as session:
                message = _find_message(session, msg_time, message_id=message_id)
                if message is not None:
                    return _attachments_for_message(session, message)
                statement = (
                    select(MessageAttachment)
                    .where(MessageAttachment.msg_time == msg_time)
                    .order_by(col(MessageAttachment.id))
                )
                if message_id is not None:
                    statement = statement.where(MessageAttachment.message_id == message_id)
                return session.exec(statement).all()

        return await _run_database(self.engine, _do)

    async def select_by_msg_times(
        self, msg_times: list[int], *, kind: str | None = None
    ) -> dict[int, list[MessageAttachment]]:
        def _do():
            attachments_by_time: dict[int, list[MessageAttachment]] = {}
            if not msg_times:
                return attachments_by_time
            with Session(self.engine) as session:
                statement = select(MessageAttachment).where(col(MessageAttachment.msg_time).in_(msg_times))
                if kind is not None:
                    statement = statement.where(MessageAttachment.kind == kind)
                statement = statement.order_by(col(MessageAttachment.msg_time), col(MessageAttachment.file_name))
                for attachment in session.exec(statement).all():
                    attachments_by_time.setdefault(attachment.msg_time, []).append(attachment)
            return attachments_by_time

        return await _run_database(self.engine, _do)

    @staticmethod
    def load_files(records: list[MessageAttachment]) -> tuple[list[bytes], int]:
        files: list[bytes] = []
        missing = 0
        for record in sorted(records, key=lambda item: item.file_name):
            full_path = os.path.join(os.getcwd(), record.physical_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    files.append(f.read())
            else:
                missing += 1
        return files, missing

    async def cleanup_expired_attachments(self, now_ms: int | None = None) -> int:
        def _do():
            cutoff = int(time.time() * 1000) if now_ms is None else now_ms
            cleaned = 0
            with Session(self.engine) as session:
                expired = session.exec(select(MessageAttachment).where(MessageAttachment.expires_at < cutoff)).all()
                affected_message_times = {record.msg_time for record in expired}
                expired_paths = {record.physical_path for record in expired}
                for record in expired:
                    session.delete(record)
                    cleaned += 1
                session.flush()
                for physical_path in expired_paths:
                    remaining_references = session.exec(
                        select(func.count())
                        .select_from(MessageAttachment)
                        .where(MessageAttachment.physical_path == physical_path)
                    ).one()
                    if remaining_references:
                        continue
                    full_path = os.path.join(os.getcwd(), physical_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        _prune_empty_attachment_dirs(full_path)
                _refresh_message_model_states(session, affected_message_times)
                session.commit()
            return cleaned

        return await _run_database(self.engine, _do)

class GroupSettingsManager:
    """群级别 key-value 设置管理器。同一 key 允许多行（支持多唤醒词等）。"""

    def __init__(self, engine):
        self.engine = engine

    def get(self, group_id: int, key: str) -> list[str]:
        def _do():
            with Session(self.engine) as session:
                rows = session.exec(
                    select(GroupSettings).where(
                        GroupSettings.group_id == group_id,
                        GroupSettings.key == key,
                    ).order_by(col(GroupSettings.id))
                ).all()
                return [row.value for row in rows]

        return _do()

    def set(self, group_id: int, key: str, value: str) -> None:
        def _do():
            now_ms = int(time.time() * 1000)
            with Session(self.engine) as session:
                row = GroupSettings(
                    group_id=group_id,
                    key=key,
                    value=value,
                    updated_at=now_ms,
                )
                session.add(row)
                session.commit()

        _do()

    def remove(self, group_id: int, key: str, value: str) -> bool:
        def _do():
            with Session(self.engine) as session:
                row = session.exec(
                    select(GroupSettings).where(
                        GroupSettings.group_id == group_id,
                        GroupSettings.key == key,
                        GroupSettings.value == value,
                    )
                ).first()
                if row is None:
                    return False
                session.delete(row)
                session.commit()
                return True

        return _do()

    def clear(self, group_id: int, key: str) -> int:
        def _do():
            with Session(self.engine) as session:
                rows = session.exec(
                    select(GroupSettings).where(
                        GroupSettings.group_id == group_id,
                        GroupSettings.key == key,
                    )
                ).all()
                count = len(rows)
                for row in rows:
                    session.delete(row)
                session.commit()
                return count

        return _do()


class MessageDatabase:
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

    async def insert_images(
        self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes],
        *, message_id: int | None = None,
    ) -> list[str]:
        self._attachments.engine = self.engine
        return await self._attachments.insert_images(msg_time, user_id, group_id, images, message_id=message_id)

    async def insert_media(self, **kwargs) -> list[MessageAttachment]:
        self._attachments.engine = self.engine
        return await self._attachments.insert_media(**kwargs)

    async def insert_attachment(self, **kwargs) -> MessageAttachment:
        self._attachments.engine = self.engine
        return await self._attachments.insert_attachment(**kwargs)

    async def select_image_attachments_by_msg_time(
        self, msg_time: int, *, message_id: int | None = None,
    ) -> list[MessageAttachment]:
        attachments = await self.select_attachments_by_msg_time(msg_time, message_id=message_id)
        return [attachment for attachment in attachments if attachment.kind == "image"]

    async def select_attachments_by_msg_time(
        self, msg_time: int, *, message_id: int | None = None,
    ) -> list[MessageAttachment]:
        self._attachments.engine = self.engine
        return await self._attachments.select_by_msg_time(msg_time, message_id=message_id)

    def load_attachment_files(self, records: list[MessageAttachment]) -> tuple[list[bytes], int]:
        return self._attachments.load_files(records)

    async def cleanup_expired_attachments(self, now_ms: int | None = None) -> int:
        self._attachments.engine = self.engine
        return await self._attachments.cleanup_expired_attachments(now_ms=now_ms)

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

    def _search_messages_fts(
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
    ) -> list[Message]:
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
            SELECT m.id
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
            ORDER BY bm25(message_fts), m.time DESC, m.id DESC
            LIMIT :limit
            OFFSET :offset
                """
            )
        else:
            query = text(
                """
            SELECT m.id
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
        return [messages_by_id[message_id] for message_id in ids if message_id in messages_by_id]

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


class EventDatabase:
    def __init__(self):
        self.engine = get_engine()
        TimeStamp.metadata.create_all(self.engine)

    async def insert(self, name, id: str | None = None):
        def _do():
            with Session(self.engine) as session:
                target = TimeStamp(name=name, id=id)
                session.add(target)
                session.commit()

        await _run_database(self.engine, _do)

    async def delete(self, name):
        def _do():
            with Session(self.engine) as session:
                target = session.get(TimeStamp, name)
                if target:
                    session.delete(target)
                    session.commit()

        await _run_database(self.engine, _do)

    async def update(self, name, id):
        def _do():
            with Session(self.engine) as session:
                target = session.get(TimeStamp, name)
                if target:
                    target.id = id
                    session.add(target)
                    session.commit()

        await _run_database(self.engine, _do)

    async def select(self, name):
        def _do():
            with Session(self.engine) as session:
                target = session.get(TimeStamp, name)
                if target:
                    return target.id
                return None

        return await _run_database(self.engine, _do)
