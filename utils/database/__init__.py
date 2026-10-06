"""SQLite/SQLModel persistence for messages, attachments and group settings.

This package replaces the former single-module ``utils.database``.  The
documented public API keeps its original import path through this facade, so
``from utils.database import MessageDatabase`` and friends behave exactly as
before; anything else is imported from the owning submodule directly.

``DATABASE_FILE`` is owned by this facade: callers and tests monkeypatch
``utils.database.DATABASE_FILE``, so :func:`get_engine` resolves the default at
call time instead of at import time.

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

from .engine import DATABASE_FILE as DATABASE_FILE
from .engine import get_engine as get_engine
from .events import EventDatabase as EventDatabase
from .fts import MESSAGE_FTS_SCHEMA_VERSION as MESSAGE_FTS_SCHEMA_VERSION
from .fts import check_message_fts as check_message_fts
from .fts import sqlite_supports_fts5 as sqlite_supports_fts5
from .maintenance import cleanup_task_execution_history as cleanup_task_execution_history
from .maintenance import get_database_diagnostics as get_database_diagnostics
from .maintenance import run_database_maintenance as run_database_maintenance
from .models import MESSAGE_SOURCE_TYPE_FORWARD_NODE as MESSAGE_SOURCE_TYPE_FORWARD_NODE
from .models import MESSAGE_SOURCE_TYPE_NORMAL as MESSAGE_SOURCE_TYPE_NORMAL
from .models import GroupSettings as GroupSettings
from .models import Message as Message
from .models import MessageAttachment as MessageAttachment
from .models import TimeStamp as TimeStamp
from .models import User as User
from .models import resolve_message_sender_user_id as resolve_message_sender_user_id
from .schema import ensure_database_performance_indexes as ensure_database_performance_indexes
from .schema import validate_database_schema as validate_database_schema
from .settings import GroupSettingsManager as GroupSettingsManager
from .store import MessageDatabase as MessageDatabase

__all__ = [
    "DATABASE_FILE",
    "EventDatabase",
    "GroupSettings",
    "GroupSettingsManager",
    "MESSAGE_FTS_SCHEMA_VERSION",
    "MESSAGE_SOURCE_TYPE_FORWARD_NODE",
    "MESSAGE_SOURCE_TYPE_NORMAL",
    "Message",
    "MessageAttachment",
    "MessageDatabase",
    "TimeStamp",
    "User",
    "check_message_fts",
    "cleanup_task_execution_history",
    "ensure_database_performance_indexes",
    "get_database_diagnostics",
    "get_engine",
    "resolve_message_sender_user_id",
    "run_database_maintenance",
    "sqlite_supports_fts5",
    "validate_database_schema",
]
