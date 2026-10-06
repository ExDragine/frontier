"""Database diagnostics, PRAGMA maintenance and retention cleanup."""

import logging
import os

from sqlalchemy import Engine, inspect, text

from .engine import get_engine
from .fts import (
    MESSAGE_FTS_SCHEMA_VERSION,
    MESSAGE_FTS_TABLE,
    _ensure_message_fts_connection,
    _message_fts_integrity_check_connection,
    _message_fts_schema_matches,
    _message_fts_version,
    _rebuild_message_fts_connection,
    sqlite_supports_fts5,
)
from .schema import _safe_table_count, _table_exists

logger = logging.getLogger(__name__)


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

        for fts_table in [MESSAGE_FTS_TABLE]:
            integrity_ok, integrity_error = _message_fts_integrity_check_connection(conn)
            schema_version = _message_fts_version(conn)
            fts_diagnostics[fts_table] = {
                "exists": _table_exists(conn, fts_table),
                "row_count": _safe_table_count(conn, fts_table),
                "schema_version": schema_version,
                "schema_version_matches": schema_version == MESSAGE_FTS_SCHEMA_VERSION,
                "schema_matches": _message_fts_schema_matches(conn),
                "integrity_ok": integrity_ok,
                "integrity_error": integrity_error,
            }

        # The integrity check is an FTS control write even though it changes no
        # application rows. End that transaction before asking SQLite to
        # checkpoint the WAL below.
        conn.commit()

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
    result: dict[str, object]
    with engine.begin() as conn:
        conn.execute(text("PRAGMA optimize"))
        result = {
            "optimized": True,
            "fts_optimized": False,
            "fts_rebuilt": False,
            "fts_schema_matches": None,
            "fts_schema_version": None,
            "fts_integrity_ok": None,
        }
        if _table_exists(conn, "message") and not _table_exists(conn, MESSAGE_FTS_TABLE):
            _ensure_message_fts_connection(conn, force_rebuild=True)
            result["fts_optimized"] = True
            result["fts_rebuilt"] = True
            result["fts_schema_matches"] = True
            result["fts_schema_version"] = MESSAGE_FTS_SCHEMA_VERSION
            result["fts_integrity_ok"] = True
        elif _table_exists(conn, MESSAGE_FTS_TABLE):
            try:
                conn.execute(  # noqa: S608
                    text(f"INSERT INTO {MESSAGE_FTS_TABLE}({MESSAGE_FTS_TABLE}) VALUES ('optimize')")  # noqa: S608
                )
                result["fts_optimized"] = True
            except Exception as exc:
                logger.warning("FTS5 message index optimize failed: %s: %s", type(exc).__name__, exc)
                result["fts_optimized"] = False
                result["fts_optimize_error"] = type(exc).__name__
            schema_matches = _message_fts_schema_matches(conn)
            schema_version = _message_fts_version(conn)
            if schema_version != MESSAGE_FTS_SCHEMA_VERSION:
                schema_matches = False
            integrity_ok, integrity_error = _message_fts_integrity_check_connection(conn)
            if not schema_matches:
                integrity_ok = False
                integrity_error = "schema_version_mismatch" if schema_version is not None else "schema_mismatch"
            result["fts_schema_matches"] = schema_matches
            result["fts_schema_version"] = schema_version
            result["fts_integrity_ok"] = integrity_ok
            if not integrity_ok:
                _rebuild_message_fts_connection(conn)
                result["fts_rebuilt"] = True
                result["fts_integrity_ok"] = True
                result["fts_integrity_error"] = integrity_error
            else:
                result["fts_rebuilt"] = False
    if checkpoint:
        with engine.connect() as conn:
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
