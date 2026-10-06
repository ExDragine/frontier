"""SQLite engine construction and the single async/thread boundary.

The only ``_run_database`` implementation lives here; every other module in the
package imports it instead of defining its own copy, so the rule "sync database
work runs in a worker thread, except for in-memory databases" stays in one place.
"""

import asyncio
import sys
from functools import lru_cache

from sqlalchemy import Engine, event
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine

DATABASE_FILE = "sqlite:///frontier.db"
SQLITE_BUSY_TIMEOUT_MS = 5000
SQLITE_CACHE_SIZE_KIB = 65536
SQLITE_MMAP_SIZE_BYTES = 256 * 1024 * 1024


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


def _default_database_url() -> str:
    """Resolve the default database URL through the ``utils.database`` facade.

    ``DATABASE_FILE`` is owned by the package so that deployments and tests can
    monkeypatch ``utils.database.DATABASE_FILE`` exactly as they did when this
    code lived in a single module.  The value is therefore read at call time
    instead of being bound at import time.
    """
    facade = sys.modules.get(__package__ or "utils.database")
    configured = getattr(facade, "DATABASE_FILE", None) if facade is not None else None
    if isinstance(configured, str) and configured:
        return configured
    return DATABASE_FILE


def get_engine(database_url: str | None = None) -> Engine:
    return _cached_engine(database_url or _default_database_url())
