import asyncio
import base64
import datetime
import json
import logging
import os
import time
import zoneinfo
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy import Engine, event, inspect, text
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, col, create_engine, desc, func, select

DATABASE_FILE = "sqlite:///frontier.db"
SQLITE_BUSY_TIMEOUT_MS = 5000
SQLITE_CACHE_SIZE_KIB = 65536
SQLITE_MMAP_SIZE_BYTES = 256 * 1024 * 1024
MESSAGE_FTS_MIN_QUERY_LENGTH = 3
logger = logging.getLogger(__name__)


async def _run_in_thread(func, *args, **kwargs):
    """将同步数据库操作放入线程池执行，避免阻塞 asyncio 事件循环。"""
    return await asyncio.to_thread(func, *args, **kwargs)


@asynccontextmanager
async def async_session_scope(engine: Engine):
    """异步 Session 上下文管理器，自动处理线程调度和提交。

    用法:
        async with async_session_scope(engine) as session:
            result = session.exec(select(Model).where(...)).all()
    """
    session = Session(engine)

    async def _execute_sync(fn, *a, **kw):
        if _engine_uses_memory_database(engine):
            return fn(*a, **kw)
        return await _run_in_thread(fn, *a, **kw)

    yield session
    await _execute_sync(lambda: (session.commit(), None) if session.is_active else None)
    await _execute_sync(session.close)


def _engine_uses_memory_database(engine: Engine) -> bool:
    return engine.url.get_backend_name() == "sqlite" and _is_memory_database(str(engine.url))


async def _run_database(engine: Engine, func, *args, **kwargs):
    if _engine_uses_memory_database(engine):
        return func(*args, **kwargs)
    return await _run_in_thread(func, *args, **kwargs)


_MESSAGE_VECTOR_INDEX = None


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
                (
                    "CREATE INDEX IF NOT EXISTS ix_message_private_user_time "
                    "ON message (user_id, time DESC) WHERE group_id IS NULL"
                ),
            ]
        )

    if "messageimage" in table_names:
        statements.extend(
            [
                (
                    "DELETE FROM messageimage WHERE id NOT IN "
                    '(SELECT max(id) FROM messageimage GROUP BY msg_time, "index")'
                ),
                'CREATE UNIQUE INDEX IF NOT EXISTS ux_messageimage_msg_time_index ON messageimage (msg_time, "index")',
                'CREATE INDEX IF NOT EXISTS ix_messageimage_msg_time_index ON messageimage (msg_time, "index")',
                "CREATE INDEX IF NOT EXISTS ix_messageimage_expires_at ON messageimage (expires_at)",
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

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
        conn.execute(text("PRAGMA optimize"))


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


def build_message_metadata(
    *,
    timestamp_ms: int,
    user_id: int | str,
    group_id: int | None,
    user_name: str | None,
) -> dict[str, object]:
    return {
        "time": datetime.datetime.fromtimestamp(int(timestamp_ms / 1000))
        .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
        .strftime("%Y-%m-%d %H:%M:%S"),
        "user_name": user_name,
        "chat_type": "group" if group_id is not None else "private",
        "group_id": group_id,
        "user_id": str(user_id),
    }


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


class TimeStamp(SQLModel, table=True):
    name: str = Field(primary_key=True, index=True)
    id: str | None


class MessageImage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    msg_time: int = Field(index=True)
    user_id: int = Field(index=True)
    group_id: int | None = None
    index: int = 0
    file_path: str
    file_size: int | None = None
    created_at: int
    expires_at: int


class _MessageImageManager:
    """图片管理：存储、清理和加载消息图片。"""

    def __init__(self, engine):
        self.engine = engine

    async def insert_images(self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes]) -> list[str]:
        def _do():
            from utils.configs import EnvConfig

            now_ms = int(time.time() * 1000)
            expires_ms = now_ms + EnvConfig.IMAGE_TTL_DAYS * 86400 * 1000
            dir_path = os.path.join(os.getcwd(), "cache", "images", str(user_id))
            os.makedirs(dir_path, exist_ok=True)
            paths = []
            with Session(self.engine) as session:
                for i, image_bytes in enumerate(images):
                    file_path = os.path.join("cache", "images", str(user_id), f"{msg_time}_{i}.jpg")
                    with open(os.path.join(os.getcwd(), file_path), "wb") as f:
                        f.write(image_bytes)
                    record = session.exec(
                        select(MessageImage).where(MessageImage.msg_time == msg_time).where(MessageImage.index == i)
                    ).first()
                    if record:
                        record.file_path = file_path
                        record.file_size = len(image_bytes)
                        record.expires_at = expires_ms
                    else:
                        record = MessageImage(
                            msg_time=msg_time,
                            user_id=user_id,
                            group_id=group_id,
                            index=i,
                            file_path=file_path,
                            file_size=len(image_bytes),
                            created_at=now_ms,
                            expires_at=expires_ms,
                        )
                    session.add(record)
                    paths.append(file_path)
                session.commit()
            return paths

        return await _run_database(self.engine, _do)

    async def cleanup_expired_images(self) -> int:
        def _do():
            now_ms = int(time.time() * 1000)
            cleaned = 0
            with Session(self.engine) as session:
                expired = session.exec(select(MessageImage).where(MessageImage.expires_at < now_ms)).all()
                for record in expired:
                    full_path = os.path.join(os.getcwd(), record.file_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    session.delete(record)
                    cleaned += 1
                session.commit()
            return cleaned

        return await _run_database(self.engine, _do)

    @staticmethod
    def load_image_files(image_records: list[MessageImage]) -> tuple[list[bytes], int]:
        file_images: list[bytes] = []
        missing_images = 0
        for img in sorted(image_records, key=lambda x: x.index):
            full_path = os.path.join(os.getcwd(), img.file_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    file_images.append(f.read())
            else:
                missing_images += 1
        return file_images, missing_images


class MessageDatabase:
    def __init__(self):
        self.engine = get_engine()
        self._vector_index = None
        self._images = _MessageImageManager(self.engine)
        Message.metadata.create_all(self.engine)
        MessageImage.metadata.create_all(self.engine)
        ensure_database_performance_indexes(self.engine)
        ensure_message_fts(self.engine)
        self._preload_vector_index_if_configured()

    async def insert(
        self,
        time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        user_name: str | None,
        role: str,
        content: str,
    ):
        def _do():
            with Session(self.engine) as session:
                message = Message(
                    time=time,
                    msg_id=msg_id,
                    user_id=user_id,
                    group_id=group_id,
                    user_name=user_name,
                    role=role,
                    content=content,
                )
                session.add(message)
                session.commit()
                self._add_message_to_vector_index(message)

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
                    statement = select(Message).where(Message.user_id == user_id)
                else:
                    return None
                if before_time is not None:
                    statement = statement.where(Message.time < before_time)
                statement = statement.order_by(desc(Message.time)).limit(query_numbers)
                results = session.exec(statement)
                return results.all()

        return await _run_database(self.engine, _do)

    async def select_by_msg_id(self, *, msg_id: int, group_id: int | None) -> Message | None:
        def _do():
            with Session(self.engine) as session:
                statement = select(Message).where(Message.msg_id == msg_id)
                if group_id is None:
                    statement = statement.where(Message.group_id.is_(None))  # type: ignore
                else:
                    statement = statement.where(Message.group_id == group_id)
                statement = statement.order_by(desc(Message.time)).limit(1)
                return session.exec(statement).first()

        return await _run_database(self.engine, _do)

    async def select_images_by_msg_time(self, msg_time: int) -> list[MessageImage]:
        def _do():
            with Session(self.engine) as session:
                statement = (
                    select(MessageImage).where(MessageImage.msg_time == msg_time).order_by(col(MessageImage.index))
                )
                return session.exec(statement).all()

        return await _run_database(self.engine, _do)

    def load_image_files(self, image_records: list[MessageImage]) -> tuple[list[bytes], int]:
        return self._images.load_image_files(image_records)

    async def prepare_message(  # noqa: C901
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
        messages_seq = []
        messages = list(reversed(messages))
        if before_time is None:
            messages = messages[:-1]
        if not messages:
            return []

        all_msg_times = [m.time for m in messages]

        def _load_images():
            images_by_time: dict[int, list[MessageImage]] = {}
            with Session(self.engine) as session:
                stmt = select(MessageImage).where(col(MessageImage.msg_time).in_(all_msg_times))
                for img in session.exec(stmt).all():
                    images_by_time.setdefault(img.msg_time, []).append(img)
            return images_by_time

        images_by_time = await _run_database(self.engine, _load_images)

        for message in messages:
            msg_images = images_by_time.get(message.time, [])
            content_text = message.content
            file_images: list[bytes] = []

            if msg_images:
                file_images, missing_images = self._images.load_image_files(msg_images)
                if missing_images:
                    content_text += "\n" + " ".join("[图片]" for _ in range(missing_images))

            text_str = json.dumps(
                {
                    "metadata": build_message_metadata(
                        timestamp_ms=message.time,
                        user_id=message.user_id,
                        group_id=message.group_id,
                        user_name=message.user_name,
                    ),
                    "content": content_text,
                }
            )

            if file_images:
                content = [{"type": "text", "text": text_str}] + [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(b).decode()}"},
                    }
                    for b in file_images
                ]
            else:
                content = text_str

            if not messages_seq:
                messages_seq.append({"role": message.role, "content": content})
                continue

            last = messages_seq[-1]
            if message.role == last["role"] and isinstance(content, str) and isinstance(last["content"], str):
                last["content"] += f"\n{content}"
            else:
                messages_seq.append({"role": message.role, "content": content})

        return messages_seq

    async def insert_images(self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes]) -> list[str]:
        self._images.engine = self.engine
        return await self._images.insert_images(msg_time, user_id, group_id, images)

    async def cleanup_expired_images(self) -> int:
        self._images.engine = self.engine
        return await self._images.cleanup_expired_images()

    async def select_by_time_range(
        self,
        start_time: int,
        end_time: int,
        group_id: int | None = None,
        user_id: int | None = None,
        limit: int = 500,
    ) -> list[Message]:
        def _do():  # noqa: C901
            with Session(self.engine) as session:
                statement = select(Message).where(Message.time >= start_time).where(Message.time <= end_time)
                if group_id is not None:
                    statement = statement.where(Message.group_id == group_id)
                    if user_id is not None:
                        statement = statement.where(Message.user_id == user_id)
                elif user_id is not None:
                    statement = statement.where(Message.user_id == user_id).where(Message.group_id.is_(None))  # type: ignore
                statement = statement.order_by(col(Message.time)).limit(limit)
                return session.exec(statement).all()

        return await _run_database(self.engine, _do)

    async def count_group_messages_since(self, *, group_id: int, since_time: int) -> int:
        def _do():
            with Session(self.engine) as session:
                statement = (
                    select(func.count())
                    .select_from(Message)
                    .where(Message.group_id == group_id)
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
        limit: int,
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
              AND (:target_user_id_enabled = 0 OR m.user_id = :target_user_id)
              AND (:target_user_name IS NULL OR m.user_name LIKE :target_user_name ESCAPE '\\')
              AND (:msg_id IS NULL OR m.msg_id = :msg_id)
              AND (:start_time IS NULL OR m.time >= :start_time)
              AND (:end_time IS NULL OR m.time <= :end_time)
            ORDER BY bm25(message_fts), m.time DESC
            LIMIT :limit
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
              AND (:target_user_id_enabled = 0 OR m.user_id = :target_user_id)
              AND (:target_user_name IS NULL OR m.user_name LIKE :target_user_name ESCAPE '\\')
              AND (:msg_id IS NULL OR m.msg_id = :msg_id)
              AND (:start_time IS NULL OR m.time >= :start_time)
              AND (:end_time IS NULL OR m.time <= :end_time)
            ORDER BY m.time DESC
            LIMIT :limit
                """
            )

        rows = session.exec(query.bindparams(**params)).all()
        ids = [int(row[0]) for row in rows]
        if not ids:
            return []

        messages = session.exec(select(Message).where(col(Message.time).in_(ids))).all()
        messages_by_id = {message.time: message for message in messages}
        return [messages_by_id[message_id] for message_id in ids if message_id in messages_by_id]

    def get_vector_index(self):
        if self._vector_index is not None:
            return self._vector_index
        global _MESSAGE_VECTOR_INDEX
        if _MESSAGE_VECTOR_INDEX is not None:
            self._vector_index = _MESSAGE_VECTOR_INDEX
            return self._vector_index
        try:
            from utils.configs import EnvConfig
            from utils.message_vector_index import MessageVectorIndex, MessageVectorIndexConfig

            config = MessageVectorIndexConfig(
                enabled=EnvConfig.VECTOR_MEMORY_ENABLED,
                persist_path=EnvConfig.VECTOR_MEMORY_CHROMA_PATH,
                collection_name=EnvConfig.VECTOR_MEMORY_COLLECTION,
                embedding_model=EnvConfig.VECTOR_MEMORY_EMBEDDING_MODEL,
                top_k=EnvConfig.VECTOR_MEMORY_SEMANTIC_TOP_K,
                embedding_batch_size=EnvConfig.VECTOR_MEMORY_EMBEDDING_BATCH_SIZE,
                embedding_device=EnvConfig.VECTOR_MEMORY_EMBEDDING_DEVICE or None,
                preload_on_startup=EnvConfig.VECTOR_MEMORY_PRELOAD_ON_STARTUP,
            )
            _MESSAGE_VECTOR_INDEX = MessageVectorIndex(config)
            self._vector_index = _MESSAGE_VECTOR_INDEX
        except Exception as exc:
            logger.warning("Message vector index initialization failed: %s", exc)
            _MESSAGE_VECTOR_INDEX = False
            self._vector_index = _MESSAGE_VECTOR_INDEX
        return self._vector_index

    def _preload_vector_index_if_configured(self) -> None:
        try:
            from utils.configs import EnvConfig
        except Exception as exc:
            logger.debug("Vector index preload skipped: %s", exc)
            return
        if EnvConfig.VECTOR_MEMORY_ENABLED and EnvConfig.VECTOR_MEMORY_PRELOAD_ON_STARTUP:
            logger.info("Preloading message vector index")
            self.get_vector_index()

    def _add_message_to_vector_index(self, message: Message) -> None:
        snapshot = Message(
            time=message.time,
            msg_id=message.msg_id,
            user_id=message.user_id,
            group_id=message.group_id,
            user_name=message.user_name,
            role=message.role,
            content=message.content,
        )

        def index_message() -> None:
            vector_index = self.get_vector_index()
            if not vector_index or not getattr(vector_index, "available", False):
                return
            add_message = getattr(vector_index, "add_message", None)
            if not callable(add_message):
                return
            add_message(snapshot)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            index_message()
        else:
            loop.create_task(asyncio.to_thread(index_message))

    def _messages_by_ids(self, session: Session, ids: list[int]) -> list[Message]:
        if not ids:
            return []
        messages = session.exec(select(Message).where(col(Message.time).in_(ids))).all()
        messages_by_id = {message.time: message for message in messages}
        return [messages_by_id[message_id] for message_id in ids if message_id in messages_by_id]

    def _semantic_search_messages(
        self,
        session: Session,
        *,
        group_id: int | None,
        user_id: int | None,
        content_query: str | None,
        target_user_id: int | None,
        target_user_name: str | None,
        msg_id: int | None,
        start_time: int | None,
        end_time: int | None,
        limit: int,
    ) -> list[Message]:
        if not content_query:
            return []
        vector_index = self.get_vector_index()
        if not vector_index or not getattr(vector_index, "available", False):
            return []
        search_fn = getattr(vector_index, "search", None)
        if not callable(search_fn):
            return []
        vector_results = search_fn(
            query=content_query,
            group_id=group_id,
            user_id=user_id,
            target_user_id=target_user_id,
            limit=max(1, min(limit, 500)),
        )
        messages = self._messages_by_ids(session, [message_id for message_id, _distance in vector_results])
        filtered = []
        for message in messages:
            if target_user_name and target_user_name not in (message.user_name or ""):
                continue
            if msg_id is not None and message.msg_id != msg_id:
                continue
            if start_time is not None and message.time < start_time:
                continue
            if end_time is not None and message.time > end_time:
                continue
            filtered.append(message)
        return filtered[: max(1, min(limit, 500))]

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
        limit: int = 50,
        sort: str = "time",
        mode: str = "keyword",
    ) -> list[Message]:
        def _do():  # noqa: C901
            with Session(self.engine) as session:
                if mode == "semantic":
                    semantic_results = self._semantic_search_messages(
                        session,
                        group_id=group_id,
                        user_id=user_id,
                        content_query=content_query,
                        target_user_id=target_user_id,
                        target_user_name=target_user_name,
                        msg_id=msg_id,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                    )
                    if semantic_results:
                        return semantic_results

                if self._can_use_fts(content_query):
                    keyword_results = self._search_messages_fts(
                        session,
                        group_id=group_id,
                        user_id=user_id,
                        content_query=content_query or "",
                        target_user_id=target_user_id,
                        target_user_name=target_user_name,
                        msg_id=msg_id,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                        sort=sort,
                    )
                    if mode == "hybrid":
                        semantic_results = self._semantic_search_messages(
                            session,
                            group_id=group_id,
                            user_id=user_id,
                            content_query=content_query,
                            target_user_id=target_user_id,
                            target_user_name=target_user_name,
                            msg_id=msg_id,
                            start_time=start_time,
                            end_time=end_time,
                            limit=limit,
                        )
                        seen = {message.time for message in keyword_results}
                        return (keyword_results + [m for m in semantic_results if m.time not in seen])[
                            : max(1, min(limit, 500))
                        ]
                    return keyword_results

                statement = select(Message)
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

                statement = statement.order_by(desc(Message.time)).limit(max(1, min(limit, 500)))
                return session.exec(statement).all()

        return await _run_database(self.engine, _do)

    @staticmethod
    def format_for_llm(messages: list[Message]) -> str:
        """将 Message 列表格式化为 LLM 可读的纯文本。

        格式：[时间] 角色(显示名): 消息内容
        """
        tz = zoneinfo.ZoneInfo("Asia/Shanghai")
        lines = []
        for msg in messages:
            ts = datetime.datetime.fromtimestamp(msg.time / 1000, tz=tz).strftime("%Y-%m-%d %H:%M:%S")
            name = msg.user_name or ("助手" if msg.role == "assistant" else str(msg.user_id))
            role_label = "助手" if msg.role == "assistant" else "用户"
            lines.append(f"[{ts}] {role_label}({name}): {msg.content}")
        return "\n".join(lines)


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

        return await _run_database(self.engine, _do)
