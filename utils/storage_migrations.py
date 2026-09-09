"""Transactional SQLite identity migration; never opens the application's DB itself."""

from sqlalchemy import CheckConstraint, Column, Integer, MetaData, Table, UniqueConstraint, inspect, text

MESSAGE_IDENTITY_VERSION = 1


def platform_message_key(*, msg_id, user_id, group_id, bot_user_id, source_type="message") -> str | None:
    if msg_id is None or source_type != "message":
        return None
    scope = f"group:{group_id}" if group_id is not None else f"dm:{user_id}"
    return f"milky:{bot_user_id or 0}:{scope}:{msg_id}"


def _rebuild_message_table(conn) -> None:
    """Retain legacy columns, constraints and indexes while replacing only the PK."""
    old = Table("message", MetaData(), autoload_with=conn)
    if list(old.primary_key.columns.keys()) != ["time"]:
        raise RuntimeError("Unsupported message primary key; refusing an unsafe identity migration")
    inspector = inspect(conn)
    for table_name in inspector.get_table_names():
        if any(key["referred_table"] == "message" for key in inspector.get_foreign_keys(table_name)):
            raise RuntimeError("Custom foreign keys reference message; migrate these relationships explicitly first")
    schema_objects = conn.execute(text(
        "SELECT sql FROM sqlite_schema WHERE type IN ('index','trigger') "
        "AND tbl_name='message' AND sql IS NOT NULL"
    )).scalars().all()
    columns = []
    for column in old.columns:
        copied = column._copy()
        copied.primary_key = False
        columns.append(copied)
    replacement = Table(
        "message_identity_new", MetaData(), Column("id", Integer, primary_key=True), *columns,
        sqlite_autoincrement=True,
    )
    for constraint in old.constraints:
        if isinstance(constraint, UniqueConstraint):
            replacement.append_constraint(UniqueConstraint(
                *(replacement.c[column.name] for column in constraint.columns), name=constraint.name,
            ))
        elif isinstance(constraint, CheckConstraint):
            replacement.append_constraint(CheckConstraint(constraint.sqltext, name=constraint.name))
    replacement.create(conn)
    preparer = conn.dialect.identifier_preparer
    names = ", ".join(preparer.quote(column.name) for column in old.columns)
    conn.exec_driver_sql(
        f"INSERT INTO message_identity_new (id, {names}) SELECT time, {names} FROM message"  # noqa: S608
    )
    conn.exec_driver_sql("DROP TABLE message")
    conn.exec_driver_sql("ALTER TABLE message_identity_new RENAME TO message")
    for statement in schema_objects:
        conn.exec_driver_sql(statement)


def _backfill_identity_links(conn) -> None:
    # Old timestamps were globally unique. Scope predicates also make repair of
    # manually imported data fail closed rather than attaching another chat's media.
    conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_message_time_id ON message (time, id)")
    conn.exec_driver_sql("""
        UPDATE message SET parent_message_id = (
            SELECT parent.id FROM message AS parent
            WHERE parent.time = message.parent_msg_time
              AND parent.source_type = 'message'
              AND parent.group_id IS message.group_id
              AND (message.group_id IS NOT NULL OR parent.user_id = message.user_id)
            ORDER BY parent.id LIMIT 1
        ) WHERE parent_msg_time IS NOT NULL AND parent_message_id IS NULL
    """)
    if "messageattachment" in inspect(conn).get_table_names():
        columns = {column["name"] for column in inspect(conn).get_columns("messageattachment")}
        if "message_id" not in columns:
            conn.exec_driver_sql("ALTER TABLE messageattachment ADD COLUMN message_id INTEGER")
        conn.exec_driver_sql("""
            UPDATE messageattachment SET message_id = (
                SELECT m.id FROM message AS m
                WHERE m.time = messageattachment.msg_time
                  AND m.group_id IS messageattachment.group_id
                  AND (m.group_id IS NOT NULL OR m.user_id = messageattachment.user_id)
                ORDER BY m.id LIMIT 1
            ) WHERE message_id IS NULL
        """)
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_messageattachment_message_id ON messageattachment (message_id)"
        )
    # Preserve historical duplicate rows; only one claims the deduplication key.
    conn.exec_driver_sql("""
        WITH identities AS (
            SELECT id, 'milky:' || coalesce(bot_user_id, 0) || ':' ||
                CASE WHEN group_id IS NULL THEN 'dm:' || user_id ELSE 'group:' || group_id END ||
                ':' || msg_id AS identity_key,
                row_number() OVER (
                    PARTITION BY coalesce(bot_user_id, 0), group_id,
                                 CASE WHEN group_id IS NULL THEN user_id ELSE 0 END, msg_id
                    ORDER BY time DESC, id DESC
                ) AS ordinal
            FROM message WHERE msg_id IS NOT NULL AND source_type = 'message'
        )
        UPDATE message SET platform_key = (
            SELECT identity_key FROM identities WHERE identities.id = message.id AND ordinal = 1
        ) WHERE platform_key IS NULL
    """)
    conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ux_message_platform_key ON message (platform_key)")
    conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_message_parent_message_id ON message (parent_message_id)")


def migrate_message_identity(engine, *, rebuild_fts) -> bool:
    """Apply schema version 1 atomically, including FTS. Safe to call repeatedly.

    The caller first adds the legacy optional columns and creates missing tables.
    Explicit BEGIN covers DDL even with sqlite3's legacy transaction mode.
    """
    if engine.dialect.name != "sqlite":
        raise ValueError("Message identity migration supports SQLite only")
    with engine.connect() as conn:
        conn.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            conn.exec_driver_sql(
                "CREATE TABLE IF NOT EXISTS frontier_schema_version "
                "(component TEXT PRIMARY KEY, version INTEGER NOT NULL)"
            )
            version = conn.execute(text(
                "SELECT version FROM frontier_schema_version WHERE component='message_identity'"
            )).scalar()
            if version is not None and version > MESSAGE_IDENTITY_VERSION:
                raise RuntimeError("Database message schema is newer than this application")
            if version == MESSAGE_IDENTITY_VERSION:
                conn.commit()
                return False
            columns = {column["name"] for column in inspect(conn).get_columns("message")}
            needs_rebuild = "id" not in columns
            if needs_rebuild:
                for name in ("message_ai_fts", "message_ad_fts", "message_au_fts"):
                    conn.exec_driver_sql(f"DROP TRIGGER IF EXISTS {name}")
                conn.exec_driver_sql("DROP TABLE IF EXISTS message_fts")
                _rebuild_message_table(conn)
            for name, kind in (("platform_key", "TEXT"), ("parent_message_id", "INTEGER")):
                if name not in columns:
                    conn.exec_driver_sql(f"ALTER TABLE message ADD COLUMN {name} {kind}")
            _backfill_identity_links(conn)
            if needs_rebuild:
                rebuild_fts(conn)
            conn.execute(text(
                "INSERT INTO frontier_schema_version(component, version) VALUES ('message_identity', :version) "
                "ON CONFLICT(component) DO UPDATE SET version=excluded.version"
            ), {"version": MESSAGE_IDENTITY_VERSION})
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    return True
