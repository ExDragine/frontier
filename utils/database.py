import asyncio
import hashlib
import json
import logging
import os
import posixpath
import shutil
import threading
import time
from contextlib import contextmanager, suppress
from functools import lru_cache

from sqlalchemy import Engine, UniqueConstraint, event, inspect, text
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
        deduplicate_message_attachments(engine)
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


def ensure_message_schema(engine: Engine) -> None:
    if "message" not in set(inspect(engine).get_table_names()):
        return
    columns = {column["name"] for column in inspect(engine).get_columns("message")}
    column_migrations = [
        ("raw_segments_json", "ALTER TABLE message ADD COLUMN raw_segments_json TEXT"),
        ("normalized_version", "ALTER TABLE message ADD COLUMN normalized_version INTEGER NOT NULL DEFAULT 0"),
        ("normalized_status", "ALTER TABLE message ADD COLUMN normalized_status TEXT NOT NULL DEFAULT 'legacy'"),
        ("source_type", "ALTER TABLE message ADD COLUMN source_type TEXT NOT NULL DEFAULT 'message'"),
        ("parent_msg_id", "ALTER TABLE message ADD COLUMN parent_msg_id INTEGER"),
        ("parent_msg_time", "ALTER TABLE message ADD COLUMN parent_msg_time INTEGER"),
        ("parent_forward_id", "ALTER TABLE message ADD COLUMN parent_forward_id TEXT"),
        ("user_nickname", "ALTER TABLE message ADD COLUMN user_nickname TEXT"),
        ("user_card", "ALTER TABLE message ADD COLUMN user_card TEXT"),
        ("reply_context_json", "ALTER TABLE message ADD COLUMN reply_context_json TEXT"),
        ("model_content", "ALTER TABLE message ADD COLUMN model_content TEXT"),
        ("sender_user_id", "ALTER TABLE message ADD COLUMN sender_user_id INTEGER"),
        ("bot_user_id", "ALTER TABLE message ADD COLUMN bot_user_id INTEGER"),
        (
            "directly_mentions_bot",
            "ALTER TABLE message ADD COLUMN directly_mentions_bot INTEGER NOT NULL DEFAULT 0",
        ),
    ]
    statements = [statement for column, statement in column_migrations if column not in columns]
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
        if "sender_user_id" not in columns:
            # Existing private assistant rows overloaded user_id with the peer
            # scope, so only unambiguous legacy authors can be backfilled.
            conn.execute(
                text(
                    "UPDATE message SET sender_user_id = user_id "
                    "WHERE group_id IS NOT NULL OR role != 'assistant'"
                )
            )


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
                    content_rowid='time',
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
                    VALUES (new.time, new.content, new.group_id, new.user_id, new.role, new.user_name, new.msg_id);
                END
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS message_ad_fts AFTER DELETE ON message BEGIN
                    INSERT INTO message_fts(message_fts, rowid, content, group_id, user_id, role, user_name, msg_id)
                    VALUES ('delete', old.time, old.content, old.group_id, old.user_id, old.role, old.user_name, old.msg_id);
                END
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS message_au_fts AFTER UPDATE ON message BEGIN
                    INSERT INTO message_fts(message_fts, rowid, content, group_id, user_id, role, user_name, msg_id)
                    VALUES ('delete', old.time, old.content, old.group_id, old.user_id, old.role, old.user_name, old.msg_id);
                    INSERT INTO message_fts(rowid, content, group_id, user_id, role, user_name, msg_id)
                    VALUES (new.time, new.content, new.group_id, new.user_id, new.role, new.user_name, new.msg_id);
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
    time: int = Field(primary_key=True)
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


def _refresh_message_model_state(
    session: Session,
    msg_time: int,
    *,
    reply_context_json: str | None | object = _REPLY_CONTEXT_UNSET,
) -> None:
    """Rebuild all attachment-derived message fields inside one transaction."""
    message = session.get(Message, msg_time)
    if message is None:
        return
    if reply_context_json is not _REPLY_CONTEXT_UNSET:
        message.reply_context_json = reply_context_json  # type: ignore[assignment]
    attachments = session.exec(
        select(MessageAttachment)
        .where(MessageAttachment.msg_time == msg_time)
        .order_by(col(MessageAttachment.file_name))
    ).all()
    model_content = content_for_persisted_images(
        message.content,
        sum(attachment.kind == "image" for attachment in attachments),
    )
    message.model_content = None if model_content == message.content else model_content
    session.add(message)


def _refresh_message_model_states(session: Session, msg_times: set[int]) -> None:
    for msg_time in sorted(msg_times):
        _refresh_message_model_state(session, msg_time)


class TimeStamp(SQLModel, table=True):
    name: str = Field(primary_key=True, index=True)
    id: str | None


class MessageAttachment(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("physical_path", "msg_time", name="uq_messageattachment_path_msg_time"),
    )

    id: int | None = Field(default=None, primary_key=True)
    msg_time: int = Field(index=True)
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


def deduplicate_message_attachments(engine: Engine) -> int:
    """Collapse legacy/concurrent duplicate rows before enforcing uniqueness."""
    removed = 0
    affected_message_times: set[int] = set()
    with Session(engine) as session:
        duplicate_keys = session.exec(
            select(MessageAttachment.physical_path, MessageAttachment.msg_time)
            .group_by(MessageAttachment.physical_path, MessageAttachment.msg_time)
            .having(func.count() > 1)
        ).all()
        for physical_path, msg_time in duplicate_keys:
            records = session.exec(
                select(MessageAttachment)
                .where(MessageAttachment.physical_path == physical_path)
                .where(MessageAttachment.msg_time == msg_time)
                .order_by(col(MessageAttachment.id))
            ).all()
            keeper, *duplicates = records
            keeper.expires_at = max(record.expires_at for record in records)
            session.add(keeper)
            for record in duplicates:
                session.delete(record)
                removed += 1
            affected_message_times.add(msg_time)
        if removed:
            session.flush()
            _refresh_message_model_states(session, affected_message_times)
            session.commit()
    if removed:
        logger.warning("已合并 %s 条重复消息附件索引", removed)
    return removed


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


def _legacy_attachment_target(
    record: MessageAttachment,
) -> tuple[str, str, str] | None:
    target_workspace_key = _message_workspace_key(record.user_id, record.group_id)
    legacy_workspace_key = str(record.group_id if record.group_id is not None else record.user_id)
    if record.workspace_key != legacy_workspace_key:
        # Only the former numeric Frontier layout is safe to rewrite; custom or
        # foreign workspace keys retain their own contract.
        return None

    legacy_root = os.path.normpath(os.path.join("cache", "sandbox", "memory", legacy_workspace_key))
    source_path = os.path.normpath(record.physical_path)
    relative_path = os.path.relpath(source_path, legacy_root)
    if relative_path == os.pardir or relative_path.startswith(os.pardir + os.sep):
        logger.warning("跳过不在旧 workspace 根目录内的附件迁移: attachment_id=%s", record.id)
        return None
    target_root = os.path.join("cache", "sandbox", "memory", target_workspace_key)
    return target_workspace_key, source_path, os.path.join(target_root, relative_path)


def _atomic_copy2(source_path: str, target_path: str) -> None:
    """Copy through a same-directory temporary file before atomic publication."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    temp_path = os.path.join(
        os.path.dirname(target_path),
        f".{os.path.basename(target_path)}.frontier-migrate-{os.getpid()}-{time.time_ns()}",
    )
    try:
        shutil.copy2(source_path, temp_path)
        with open(temp_path, "rb") as copied_file:
            os.fsync(copied_file.fileno())
        os.replace(temp_path, target_path)
    finally:
        with suppress(FileNotFoundError):
            os.remove(temp_path)


def _copy_legacy_attachment(record: MessageAttachment, source_path: str, target_path: str) -> str | None:
    source_full_path = os.path.join(os.getcwd(), source_path)
    target_full_path = os.path.join(os.getcwd(), target_path)
    if not os.path.isfile(source_full_path):
        return target_path
    try:
        if not os.path.exists(target_full_path):
            _atomic_copy2(source_full_path, target_full_path)
            return target_path
        if os.path.isfile(target_full_path) and (
            _sha256_file(source_full_path) == _sha256_file(target_full_path)
        ):
            return target_path
        stem, suffix = os.path.splitext(target_path)
        source_digest = _sha256_file(source_full_path)
        conflict_stem = f"{stem}-legacy-{record.id}-{source_digest[:10]}"
        conflict_path = f"{conflict_stem}{suffix}"
        counter = 2
        while os.path.exists(conflict_full_path := os.path.join(os.getcwd(), conflict_path)):
            if _sha256_file(conflict_full_path) == source_digest:
                return conflict_path
            conflict_path = f"{conflict_stem}-{counter}{suffix}"
            counter += 1
        _atomic_copy2(source_full_path, conflict_full_path)
        return conflict_path
    except OSError as exc:
        logger.warning(
            "旧附件 workspace 迁移失败，保留原记录: attachment_id=%s error=%s",
            record.id,
            exc,
        )
        return None


def migrate_legacy_attachment_workspaces(engine: Engine) -> int:
    """Copy indexed legacy attachments into typed group/private workspaces.

    Unindexed files such as SOUL.md remain available for the separate scope
    migration; successfully re-indexed media no longer needs a legacy copy.
    """
    migrated = 0
    migrated_source_paths: set[str] = set()
    with Session(engine) as session:
        records = session.exec(
            select(MessageAttachment).where(
                ~col(MessageAttachment.workspace_key).like("group-%"),
                ~col(MessageAttachment.workspace_key).like("dm-%"),
            )
        ).all()
        affected_message_times: set[int] = set()
        for record in records:
            target = _legacy_attachment_target(record)
            if target is None:
                continue
            target_workspace_key, source_path, requested_target_path = target
            target_path = _copy_legacy_attachment(record, source_path, requested_target_path)
            if target_path is None:
                continue

            existing_target = session.exec(
                select(MessageAttachment)
                .where(MessageAttachment.physical_path == target_path)
                .where(MessageAttachment.msg_time == record.msg_time)
                .where(MessageAttachment.id != record.id)
                .limit(1)
            ).first()
            if existing_target is not None:
                existing_target.expires_at = max(existing_target.expires_at, record.expires_at)
                existing_target.created_at = min(existing_target.created_at, record.created_at)
                session.add(existing_target)
                session.delete(record)
                affected_message_times.add(record.msg_time)
                migrated_source_paths.add(source_path)
                migrated += 1
                continue

            target_root = os.path.join("cache", "sandbox", "memory", target_workspace_key)
            relative_virtual_path = os.path.relpath(target_path, target_root).replace(os.sep, "/")
            record.workspace_key = target_workspace_key
            record.file_name = os.path.basename(target_path)
            record.physical_path = target_path
            record.virtual_path = posixpath.join("/memory", target_workspace_key, relative_virtual_path)
            session.add(record)
            affected_message_times.add(record.msg_time)
            migrated_source_paths.add(source_path)
            migrated += 1

        if migrated:
            session.flush()
            _refresh_message_model_states(session, affected_message_times)
            session.commit()
    with Session(engine) as session:
        still_referenced = set(
            session.exec(
                select(MessageAttachment.physical_path).where(
                    col(MessageAttachment.physical_path).in_(migrated_source_paths)
                )
            ).all()
        )
    for source_path in migrated_source_paths - still_referenced:
        source_full_path = os.path.join(os.getcwd(), source_path)
        try:
            os.remove(source_full_path)
            _prune_empty_attachment_dirs(source_full_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            logger.warning("旧附件迁移完成但源文件清理失败 %s: %s", source_path, exc)
    if migrated:
        logger.info("已迁移 %s 个旧版未分 scope 的消息附件索引", migrated)
    return migrated


def _legacy_scope_types(engine: Engine, legacy_ids: set[str]) -> dict[str, set[str]]:
    scope_types: dict[str, set[str]] = {legacy_id: set() for legacy_id in legacy_ids}
    numeric_ids = [int(legacy_id) for legacy_id in legacy_ids]

    def remember(scope_id: object, scope_type: str) -> None:
        if scope_id is not None:
            scope_types.setdefault(str(scope_id), set()).add(scope_type)

    with Session(engine) as session:
        for group_id in session.exec(
            select(Message.group_id)
            .where(col(Message.group_id).in_(numeric_ids))
            .distinct()
        ).all():
            remember(group_id, "group")
        for user_id in session.exec(
            select(Message.user_id)
            .where(Message.group_id.is_(None))
            .where(col(Message.user_id).in_(numeric_ids))
            .distinct()
        ).all():
            remember(user_id, "private")
        for group_id in session.exec(
            select(MessageAttachment.group_id)
            .where(col(MessageAttachment.group_id).in_(numeric_ids))
            .distinct()
        ).all():
            remember(group_id, "group")
        for user_id in session.exec(
            select(MessageAttachment.user_id)
            .where(MessageAttachment.group_id.is_(None))
            .where(col(MessageAttachment.user_id).in_(numeric_ids))
            .distinct()
        ).all():
            remember(user_id, "private")
    return scope_types


def _legacy_conflict_path(target_path: str, source_path: str) -> str:
    digest = _sha256_file(source_path)[:10]
    stem, suffix = os.path.splitext(target_path)
    return f"{stem}.legacy-{digest}{suffix}"


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _merge_legacy_file(source_path: str, target_path: str) -> None:
    if os.path.exists(target_path):
        source_size = os.path.getsize(source_path)
        target_size = os.path.getsize(target_path)
        if not source_size or (source_size == target_size and _sha256_file(source_path) == _sha256_file(target_path)):
            os.remove(source_path)
            return
        if not target_size:
            _atomic_copy2(source_path, target_path)
        else:
            conflict_path = _legacy_conflict_path(target_path, source_path)
            if (
                not os.path.exists(conflict_path)
                or os.path.getsize(source_path) != os.path.getsize(conflict_path)
                or _sha256_file(source_path) != _sha256_file(conflict_path)
            ):
                _atomic_copy2(source_path, conflict_path)
    else:
        _atomic_copy2(source_path, target_path)
    os.remove(source_path)


def _merge_legacy_directory(
    source_dir: str,
    target_dir: str,
    *,
    protected_source_paths: set[str] | None = None,
) -> bool:
    """Merge one unambiguous legacy tree without overwriting newer files."""
    if not os.path.isdir(source_dir):
        return False
    os.makedirs(target_dir, exist_ok=True)
    incomplete_migration = False
    protected_source_paths = protected_source_paths or set()
    for current_root, dir_names, file_names in os.walk(source_dir, topdown=True):
        safe_dirs = []
        for name in dir_names:
            source_child = os.path.join(current_root, name)
            if os.path.islink(source_child):
                incomplete_migration = True
                logger.warning("跳过旧 workspace 中的符号链接: %s", source_child)
            else:
                safe_dirs.append(name)
        dir_names[:] = safe_dirs
        relative_root = os.path.relpath(current_root, source_dir)
        target_root = target_dir if relative_root == "." else os.path.join(target_dir, relative_root)
        os.makedirs(target_root, exist_ok=True)
        for name in file_names:
            source_path = os.path.join(current_root, name)
            if os.path.abspath(source_path) in protected_source_paths:
                incomplete_migration = True
                continue
            if os.path.islink(source_path):
                incomplete_migration = True
                logger.warning("跳过旧 workspace 中的符号链接: %s", source_path)
                continue
            target_path = os.path.join(target_root, name)
            _merge_legacy_file(source_path, target_path)

    if incomplete_migration:
        return False
    shutil.rmtree(source_dir)
    return True


def migrate_legacy_scope_directories(
    engine: Engine,
    *,
    working_dir: str | None = None,
) -> tuple[int, int]:
    """Move untyped SOUL/workspace trees when SQL proves one unique scope."""
    working_dir = working_dir or os.path.join(os.getcwd(), "cache", "sandbox")
    legacy_ids: set[str] = set()
    for area in ("memory", "workspaces"):
        root = os.path.join(working_dir, area)
        try:
            entries = os.scandir(root)
        except FileNotFoundError:
            continue
        except OSError as exc:
            logger.warning("无法扫描旧 workspace 目录 %s: %s", root, exc)
            continue
        with entries:
            legacy_ids.update(
                entry.name
                for entry in entries
                if entry.is_dir(follow_symlinks=False)
                and entry.name.isascii()
                and entry.name.isdecimal()
            )
    if not legacy_ids:
        return 0, 0

    migrated = 0
    ambiguous = 0
    for legacy_id, scope_types in _legacy_scope_types(engine, legacy_ids).items():
        if len(scope_types) != 1:
            ambiguous += 1
            reason = "同时匹配群聊和私聊" if scope_types else "缺少可判定 scope 的 SQL 记录"
            logger.warning("旧 workspace %s %s，保留原目录等待人工合并", legacy_id, reason)
            continue
        scope_type = next(iter(scope_types))
        target_key = f"group-{legacy_id}" if scope_type == "group" else f"dm-{legacy_id}"
        legacy_memory_prefix = os.path.join("cache", "sandbox", "memory", legacy_id) + os.sep
        with Session(engine) as session:
            protected_memory_paths = {
                os.path.abspath(os.path.join(os.getcwd(), physical_path))
                for physical_path in session.exec(
                    select(MessageAttachment.physical_path).where(
                        col(MessageAttachment.physical_path).like(f"{legacy_memory_prefix}%")
                    )
                ).all()
            }
        moved_any = False
        for area in ("memory", "workspaces"):
            try:
                moved = _merge_legacy_directory(
                    os.path.join(working_dir, area, legacy_id),
                    os.path.join(working_dir, area, target_key),
                    protected_source_paths=protected_memory_paths if area == "memory" else None,
                )
            except OSError as exc:
                logger.warning("旧 workspace 自动迁移失败 %s/%s: %s", area, legacy_id, exc)
                continue
            moved_any = moved or moved_any
        migrated += int(moved_any)
    if migrated:
        logger.info("已自动迁移 %s 个可唯一判定 scope 的旧 SOUL/workspace", migrated)
    return migrated, ambiguous


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
    ) -> MessageAttachment:
        def _do():
            workspace_key = _message_workspace_key(user_id, group_id)
            now_ms = int(time.time() * 1000)
            with Session(self.engine, expire_on_commit=False) as session:
                attachment = session.exec(
                    select(MessageAttachment).where(MessageAttachment.physical_path == physical_path).limit(1)
                ).first()
                affected_message_times = {msg_time}
                if attachment is None:
                    attachment = MessageAttachment(
                        msg_time=msg_time,
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

    async def insert_images(self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes]) -> list[str]:
        attachments = await self.insert_media(
            msg_time=msg_time,
            msg_id=None,
            user_id=user_id,
            group_id=group_id,
            media=[resolve_media(image, "image") for image in images],
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
                    affected_message_times = {msg_time}
                    for index, item in enumerate(media):
                        file_name = f"{msg_time}_{index}{item.extension}"
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

    async def select_by_msg_time(self, msg_time: int) -> list[MessageAttachment]:
        def _do():
            with Session(self.engine) as session:
                statement = (
                    select(MessageAttachment)
                    .where(MessageAttachment.msg_time == msg_time)
                    .order_by(col(MessageAttachment.id))
                )
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

    async def repair_legacy_media_attachments(self, limit: int = 200) -> tuple[int, int]:
        """Gradually repair legacy image rows whose `.jpg` suffix did not match their bytes.

        Returns ``(verified, corrected)``. A marker in ``metadata_json`` keeps later
        startups from reopening files that have already been checked.
        """

        def _do():
            verified = 0
            corrected = 0
            with Session(self.engine) as session:
                affected_message_times: set[int] = set()
                records = session.exec(
                    select(MessageAttachment)
                    .where(MessageAttachment.kind == "image")
                    .order_by(col(MessageAttachment.id))
                ).all()
                for record in records:
                    try:
                        metadata = json.loads(record.metadata_json or "{}")
                    except TypeError, ValueError:
                        metadata = {}
                    if metadata.get("media_type_verified") is True:
                        continue
                    if verified >= limit:
                        break

                    full_path = os.path.join(os.getcwd(), record.physical_path)
                    if os.path.isfile(full_path):
                        with open(full_path, "rb") as file:
                            resolved = resolve_media(file.read(), "image", file_name=record.file_name)
                        target_name = f"{os.path.splitext(record.file_name)[0]}{resolved.extension}"
                        target_full_path = os.path.join(os.path.dirname(full_path), target_name)
                        if os.path.abspath(target_full_path) != os.path.abspath(full_path):
                            if os.path.exists(target_full_path):
                                stem, suffix = os.path.splitext(target_name)
                                target_name = f"{stem}-{record.id}{suffix}"
                                target_full_path = os.path.join(os.path.dirname(full_path), target_name)
                            os.replace(full_path, target_full_path)
                            record.file_name = target_name
                            record.physical_path = os.path.join(
                                os.path.dirname(record.physical_path),
                                target_name,
                            )
                            record.virtual_path = posixpath.join(
                                posixpath.dirname(record.virtual_path),
                                target_name,
                            )
                            corrected += 1
                        if record.mime_type != resolved.mime_type:
                            record.mime_type = resolved.mime_type
                            corrected += 1

                    metadata["media_type_verified"] = True
                    record.metadata_json = json.dumps(metadata, ensure_ascii=False)
                    session.add(record)
                    affected_message_times.add(record.msg_time)
                    verified += 1
                session.flush()
                _refresh_message_model_states(session, affected_message_times)
                session.commit()
            return verified, corrected

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
        self._attachments = _MessageAttachmentManager(self.engine)
        Message.metadata.create_all(self.engine)
        ensure_message_schema(self.engine)
        MessageAttachment.metadata.create_all(self.engine)
        migrate_legacy_attachment_workspaces(self.engine)
        migrate_legacy_scope_directories(self.engine)
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
    ):
        def _do():
            with Session(self.engine) as session:
                resolved_sender_user_id = sender_user_id
                if resolved_sender_user_id is None and (group_id is not None or role != "assistant"):
                    resolved_sender_user_id = user_id
                message = Message(
                    time=time,
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
                session.commit()

        await _run_database(self.engine, _do)

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
                statement = statement.order_by(desc(Message.time)).limit(query_numbers)
                results = session.exec(statement)
                return results.all()

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
                statement = statement.order_by(desc(Message.time)).limit(1)
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
    ) -> None:
        def _do():
            with Session(self.engine) as session:
                message = session.get(Message, time)
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
                _refresh_message_model_state(session, time)
                session.commit()

        await _run_database(self.engine, _do)

    async def finalize_message_context(
        self,
        *,
        time: int,
        reply_context_json: str | None | object = _REPLY_CONTEXT_UNSET,
    ) -> None:
        """Rebuild the model-facing view after lazy attachments resolve."""

        def _do():
            with Session(self.engine) as session:
                _refresh_message_model_state(
                    session,
                    time,
                    reply_context_json=reply_context_json,
                )
                session.commit()

        await _run_database(self.engine, _do)

    @staticmethod
    def _derived_message_time(parent_msg_time: int, ordinal: int) -> int:
        return -(abs(parent_msg_time) * 1000 + ordinal + 1)

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
    ) -> None:
        def _do():
            with Session(self.engine) as session:
                existing = session.exec(
                    select(Message)
                    .where(Message.parent_msg_time == parent_msg_time)
                    .where(Message.source_type != MESSAGE_SOURCE_TYPE_NORMAL)
                ).all()
                for message in existing:
                    session.delete(message)

                for ordinal, item in enumerate(derived_messages):
                    message = Message(
                        time=self._derived_message_time(parent_msg_time, ordinal),
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
                        parent_forward_id=getattr(item, "forward_id", None),
                    )
                    session.add(message)
                session.commit()

        await _run_database(self.engine, _do)

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
        messages = sorted(messages, key=lambda message: message.time)
        messages_seq: list[dict[str, object]] = []

        all_msg_times = [m.time for m in messages]

        self._attachments.engine = self.engine
        attachments_by_time = await self._attachments.select_by_msg_times(all_msg_times)

        for message in messages:
            msg_attachments = attachments_by_time.get(message.time, [])
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

    async def insert_images(self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes]) -> list[str]:
        self._attachments.engine = self.engine
        return await self._attachments.insert_images(msg_time, user_id, group_id, images)

    async def insert_media(self, **kwargs) -> list[MessageAttachment]:
        self._attachments.engine = self.engine
        return await self._attachments.insert_media(**kwargs)

    async def insert_attachment(self, **kwargs) -> MessageAttachment:
        self._attachments.engine = self.engine
        return await self._attachments.insert_attachment(**kwargs)

    async def select_image_attachments_by_msg_time(self, msg_time: int) -> list[MessageAttachment]:
        self._attachments.engine = self.engine
        attachments = await self._attachments.select_by_msg_time(msg_time)
        return [attachment for attachment in attachments if attachment.kind == "image"]

    def load_attachment_files(self, records: list[MessageAttachment]) -> tuple[list[bytes], int]:
        return self._attachments.load_files(records)

    async def cleanup_expired_attachments(self, now_ms: int | None = None) -> int:
        self._attachments.engine = self.engine
        return await self._attachments.cleanup_expired_attachments(now_ms=now_ms)

    async def repair_legacy_media_attachments(self, limit: int = 200) -> tuple[int, int]:
        self._attachments.engine = self.engine
        return await self._attachments.repair_legacy_media_attachments(limit=limit)

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
                    .order_by(desc(Message.time))
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
            SELECT m.time
            FROM message_fts
            JOIN message AS m ON m.time = message_fts.rowid
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
            ORDER BY bm25(message_fts), m.time DESC
            LIMIT :limit
            OFFSET :offset
                """
            )
        else:
            query = text(
                """
            SELECT m.time
            FROM message_fts
            JOIN message AS m ON m.time = message_fts.rowid
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
            ORDER BY m.time DESC
            LIMIT :limit
            OFFSET :offset
                """
            )

        rows = session.connection().execute(query, params).all()
        ids = [int(row[0]) for row in rows]
        if not ids:
            return []

        messages = session.exec(select(Message).where(col(Message.time).in_(ids))).all()
        messages_by_id = {message.time: message for message in messages}
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
                    statement.order_by(desc(Message.time))
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
