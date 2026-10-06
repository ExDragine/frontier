# ruff: noqa: F401 -- this module is a pure re-export facade.
"""SQLite/SQLModel persistence for messages, attachments and group settings.

This package replaces the former single-module ``utils.database``.  The public
namespace is deliberately unchanged: every name that used to live in that module
is re-exported here, so ``import utils.database`` and ``from utils.database import
X`` keep working for existing callers.  ``F401`` is disabled file-wide because
every import in this module is intentionally a re-export.

``DATABASE_FILE`` is re-exported from :mod:`utils.database.engine` and owned by
this facade: callers and tests monkeypatch ``utils.database.DATABASE_FILE``, so
``get_engine`` resolves the default at call time rather than at import time.

Module layout:

* ``engine`` - engine creation, SQLite pragmas and the single async/thread boundary
* ``models`` - SQLModel tables and the plain result types
* ``schema`` - table helpers, query indexes, schema validation, dedup keys
* ``fts`` - FTS5 message index maintenance and query helpers
* ``maintenance`` - diagnostics, PRAGMA maintenance and retention cleanup
* ``rows`` - message row -> model-facing payload helpers
* ``attachments`` - attachment file staging, indexing and cleanup
* ``search`` - full-text and LIKE search (mixed into ``MessageDatabase``)
* ``store`` - ``MessageDatabase`` itself
* ``settings`` - ``GroupSettingsManager``
* ``events`` - ``EventDatabase``
"""

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

from .attachments import (
    _ATTACHMENT_KIND_DIRECTORIES,
    _ATTACHMENT_WRITE_LOCKS,
    _attachment_paths,
    _lock_attachment_paths,
    _message_workspace_key,
    _MessageAttachmentManager,
    _PendingFileWrite,
    _prune_empty_attachment_dirs,
    _sha256_bytes,
)
from .engine import (
    DATABASE_FILE,
    SQLITE_BUSY_TIMEOUT_MS,
    SQLITE_CACHE_SIZE_KIB,
    SQLITE_MMAP_SIZE_BYTES,
    _cached_engine,
    _configure_sqlite_connection,
    _engine_uses_memory_database,
    _is_memory_database,
    _run_database,
    _run_in_thread,
    get_engine,
)
from .events import EventDatabase
from .fts import (
    MESSAGE_FTS_META_TABLE,
    MESSAGE_FTS_MIN_QUERY_LENGTH,
    MESSAGE_FTS_SCHEMA_VERSION,
    MESSAGE_FTS_TABLE,
    _drop_message_fts_connection,
    _ensure_fts_metadata_table,
    _ensure_message_fts_connection,
    _fts_query,
    _message_fts_integrity_check_connection,
    _message_fts_schema_matches,
    _message_fts_schema_sql,
    _message_fts_version,
    _rebuild_message_fts_connection,
    _record_message_fts_version,
    check_message_fts,
    ensure_message_fts,
    sqlite_supports_fts5,
)
from .maintenance import cleanup_task_execution_history, get_database_diagnostics, run_database_maintenance
from .models import (
    MESSAGE_SOURCE_TYPE_FORWARD_NODE,
    MESSAGE_SOURCE_TYPE_NORMAL,
    GroupSettings,
    Message,
    MessageAttachment,
    MessageInsertResult,
    MessageSearchResult,
    TimeStamp,
    User,
    resolve_message_sender_user_id,
)
from .rows import (
    _REPLY_CONTEXT_UNSET,
    _attachment_agent_payload,
    _attachments_for_message,
    _find_message,
    _message_agent_payload,
    _message_reply_payload,
    _refresh_message_model_state,
    _refresh_message_model_states,
)
from .schema import (
    _safe_table_count,
    _table_exists,
    ensure_database_performance_indexes,
    platform_message_key,
    validate_database_schema,
)
from .settings import GroupSettingsManager
from .store import MessageDatabase

# ``asyncio``/``json``/``os``/``select`` and the other implementation imports
# above were incidental module attributes of the historical single-module
# implementation.  They stay importable so no caller that reached through
# ``utils.database`` can break, and because this module declares no ``__all__``,
# ``from utils.database import *`` keeps exposing the same names as before.
logger = logging.getLogger(__name__)

def _install_attribute_forwarding() -> None:
    """Keep the historical module-level monkeypatching surface working.

    When ``utils.database`` was a single module, every internal helper shared one
    module namespace, so ``monkeypatch.setattr(utils.database, "_helper", fake)``
    replaced that helper for every call site at once.  The split moved the call
    sites into submodules that hold their own references, so assigning an
    attribute on this facade now also assigns it on every submodule that exposes
    the same name.  Reads are unchanged: the package itself keeps the value.
    """
    import sys
    import types

    owners: dict[str, list] = {}
    for module_name in (
        "attachments",
        "engine",
        "events",
        "fts",
        "maintenance",
        "models",
        "rows",
        "schema",
        "search",
        "settings",
        "store",
    ):
        module = sys.modules.get(f"{__name__}.{module_name}")
        if not isinstance(module, types.ModuleType):
            continue
        for attribute in vars(module):
            if attribute in globals():
                owners.setdefault(attribute, []).append(module)

    class _FacadeModule(types.ModuleType):
        """``utils.database`` package whose attribute writes reach the submodules."""

        def __setattr__(self, name: str, value: object) -> None:
            super().__setattr__(name, value)
            for owner in owners.get(name, ()):
                setattr(owner, name, value)

    sys.modules[__name__].__class__ = _FacadeModule


_install_attribute_forwarding()
del _install_attribute_forwarding
