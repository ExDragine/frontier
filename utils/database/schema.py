"""Table helpers, query indexes, schema validation and platform dedup keys."""

from sqlalchemy import Engine, inspect, text
from sqlmodel import SQLModel


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
