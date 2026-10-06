"""SQLite FTS5 message index: schema, triggers, integrity and query helpers."""

import logging
import time

from sqlalchemy import Engine, text

from .engine import get_engine
from .schema import _safe_table_count, _table_exists

MESSAGE_FTS_MIN_QUERY_LENGTH = 3
MESSAGE_FTS_SCHEMA_VERSION = 1
MESSAGE_FTS_TABLE = "message_fts"
MESSAGE_FTS_META_TABLE = "frontier_fts_metadata"

logger = logging.getLogger(__name__)


def _message_fts_schema_sql(conn) -> str | None:
    row = conn.execute(
        text("SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = :table_name LIMIT 1"),
        {"table_name": MESSAGE_FTS_TABLE},
    ).first()
    return str(row[0]) if row and row[0] else None


def _message_fts_schema_matches(conn) -> bool:
    sql = _message_fts_schema_sql(conn)
    if not sql:
        return False
    normalized = " ".join(sql.lower().split()).replace(" = ", "=")
    return all(
        marker in normalized
        for marker in (
            "using fts5",
            "content='message'",
            "content_rowid='id'",
            "tokenize='trigram'",
        )
    )


def _ensure_fts_metadata_table(conn) -> None:
    conn.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {MESSAGE_FTS_META_TABLE} (
                name TEXT PRIMARY KEY,
                version INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """  # noqa: S608
        )
    )


def _record_message_fts_version(conn) -> None:
    _ensure_fts_metadata_table(conn)
    conn.execute(
        text(
            f"""
            INSERT INTO {MESSAGE_FTS_META_TABLE}(name, version, updated_at)
            VALUES (:name, :version, :updated_at)
            ON CONFLICT(name) DO UPDATE SET
                version = excluded.version,
                updated_at = excluded.updated_at
            """  # noqa: S608
        ),
        {"name": MESSAGE_FTS_TABLE, "version": MESSAGE_FTS_SCHEMA_VERSION, "updated_at": int(time.time())},
    )


def _message_fts_version(conn) -> int | None:
    if not _table_exists(conn, MESSAGE_FTS_META_TABLE):
        return None
    row = conn.execute(
        text(
            f"SELECT version FROM {MESSAGE_FTS_META_TABLE} WHERE name = :name LIMIT 1"  # noqa: S608
        ),
        {"name": MESSAGE_FTS_TABLE},
    ).first()
    return int(row[0]) if row else None


def _message_fts_integrity_check_connection(conn) -> tuple[bool, str | None]:
    if not _table_exists(conn, MESSAGE_FTS_TABLE):
        return False, "missing"
    try:
        conn.execute(  # noqa: S608
            text(f"INSERT INTO {MESSAGE_FTS_TABLE}({MESSAGE_FTS_TABLE}) VALUES ('integrity-check')")  # noqa: S608
        )
    except Exception as exc:
        logger.warning("FTS5 message index integrity check failed: %s: %s", type(exc).__name__, exc)
        return False, type(exc).__name__
    return True, None


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


def check_message_fts(engine: Engine | None = None, *, repair: bool = False) -> dict[str, object]:
    """Check the message FTS schema and optionally rebuild it in one transaction."""
    engine = engine or get_engine()
    if not sqlite_supports_fts5(engine):
        return {
            "supported": False,
            "exists": False,
            "schema_matches": False,
            "integrity_ok": None,
            "repaired": False,
        }
    with engine.begin() as conn:
        exists = _table_exists(conn, MESSAGE_FTS_TABLE)
        schema_matches = _message_fts_schema_matches(conn) if exists else False
        schema_version = _message_fts_version(conn)
        schema_version_matches = schema_version == MESSAGE_FTS_SCHEMA_VERSION
        if not schema_version_matches:
            schema_matches = False
        integrity_ok, integrity_error = _message_fts_integrity_check_connection(conn) if schema_matches else (
            False,
            "schema_version_mismatch" if exists and schema_version is not None else ("schema_mismatch" if exists else "missing"),
        )
        repaired = False
        if repair and (not schema_matches or not integrity_ok):
            _rebuild_message_fts_connection(conn)
            repaired = True
            exists = True
            schema_matches = True
            schema_version = MESSAGE_FTS_SCHEMA_VERSION
            schema_version_matches = True
            integrity_ok, integrity_error = _message_fts_integrity_check_connection(conn)
        return {
            "supported": True,
            "exists": exists,
            "schema_matches": schema_matches,
            "schema_version": schema_version,
            "schema_version_matches": schema_version == MESSAGE_FTS_SCHEMA_VERSION,
            "integrity_ok": integrity_ok,
            "integrity_error": integrity_error,
            "repaired": repaired,
        }


def _drop_message_fts_connection(conn) -> None:
    for trigger in ("message_ai_fts", "message_ad_fts", "message_au_fts"):
        conn.execute(text(f"DROP TRIGGER IF EXISTS {trigger}"))
    conn.execute(text(f"DROP TABLE IF EXISTS {MESSAGE_FTS_TABLE}"))


def _rebuild_message_fts_connection(conn) -> None:
    """Recreate the external-content index and repopulate it from ``message``."""
    if not _table_exists(conn, "message"):
        return
    _drop_message_fts_connection(conn)
    _ensure_message_fts_connection(conn, force_rebuild=True)


def _ensure_message_fts_connection(conn, *, force_rebuild: bool = False) -> None:
    table_exists = _table_exists(conn, MESSAGE_FTS_TABLE)
    if table_exists and not _message_fts_schema_matches(conn):
        logger.warning("FTS5 message index schema changed; rebuilding external-content index")
        _drop_message_fts_connection(conn)
        table_exists = False
    conn.execute(
        text(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {MESSAGE_FTS_TABLE} USING fts5(
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
    if not table_exists or force_rebuild:
        message_count = _safe_table_count(conn, "message") or 0
        started_at = time.monotonic()
        logger.info("FTS5 message index rebuild started: rows=%s", message_count)
        conn.execute(  # noqa: S608
            text(f"INSERT INTO {MESSAGE_FTS_TABLE}({MESSAGE_FTS_TABLE}) VALUES ('rebuild')")  # noqa: S608
        )
        elapsed = time.monotonic() - started_at
        logger.info("FTS5 message index rebuild finished: rows=%s elapsed=%.2fs", message_count, elapsed)
    else:
        logger.info("FTS5 message index ready")
    _record_message_fts_version(conn)
    conn.execute(text("PRAGMA optimize"))


def _fts_query(value: str) -> str:
    escaped = value.replace('"', '""')
    return f'"{escaped}"'
