# ruff: noqa: S101

from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, select

from utils import database as db_module
from utils.database import Message, MessageAttachment, MessageDatabase


def test_get_engine_configures_sqlite_for_concurrent_bot_workload(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'frontier-test.db'}"

    engine = db_module.get_engine(db_url)

    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "wal"
        assert conn.exec_driver_sql("PRAGMA synchronous").scalar() == 1
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert conn.exec_driver_sql("PRAGMA busy_timeout").scalar() >= 5000


def test_message_database_creates_query_shaped_indexes(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")

    database = MessageDatabase()

    index_names = {index["name"] for index in inspect(database.engine).get_indexes("message")}
    attachment_index_names = {index["name"] for index in inspect(database.engine).get_indexes("messageattachment")}

    assert "ix_message_group_time" in index_names
    assert "ix_message_user_group_time" in index_names
    assert "ix_message_group_role_time" in index_names
    assert "ix_message_group_msg_id_time" in index_names
    assert "ix_message_source_parent" in index_names
    assert "ix_message_private_user_time" in index_names
    assert "ix_messageattachment_msg_time" in attachment_index_names
    assert "ix_messageattachment_expires_at" in attachment_index_names
    assert "ix_messageattachment_scope" in attachment_index_names


@pytest.mark.asyncio
async def test_select_treats_zero_group_id_as_valid_scope(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    await database.insert(1000, 1, 10, 0, "Zero", "user", "zero group")
    await database.insert(2000, 2, 10, None, "Private", "user", "private")

    messages = await database.select(user_id=10, group_id=0)

    assert messages is not None
    assert [message.content for message in messages] == ["zero group"]


def test_recent_group_query_avoids_temp_sort(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    SQLModel.metadata.create_all(database.engine)
    with Session(database.engine) as session:
        session.add_all(
            [
                Message(time=i, msg_id=i, user_id=i % 5, group_id=i % 3, user_name="u", role="user", content="x")
                for i in range(1, 300)
            ]
        )
        session.commit()

    with database.engine.connect() as conn:
        plan = "\n".join(
            row[3]
            for row in conn.execute(
                text(
                    "EXPLAIN QUERY PLAN "
                    "SELECT * FROM message "
                    "WHERE group_id = :group_id AND time < :before_time "
                    "ORDER BY time DESC LIMIT :limit"
                ),
                {"group_id": 1, "before_time": 250, "limit": 20},
            )
        )

    assert "SEARCH message USING INDEX" in plan
    assert "USE TEMP B-TREE" not in plan


def test_attachment_cleanup_query_uses_expires_at_index(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    with Session(database.engine) as session:
        session.add(
            MessageAttachment(
                msg_time=1,
                msg_id=1,
                user_id=1,
                group_id=None,
                workspace_key="1",
                kind="image",
                source_type="message",
                file_name="1_0.jpg",
                physical_path="cache/sandbox/memory/1/images/1_0.jpg",
                virtual_path="/memory/1/images/1_0.jpg",
                file_size=10,
                created_at=1,
                expires_at=10,
            )
        )
        session.commit()

    with database.engine.connect() as conn:
        plan = "\n".join(
            row[3]
            for row in conn.execute(
                text("EXPLAIN QUERY PLAN SELECT * FROM messageattachment WHERE expires_at < :now"),
                {"now": 100},
            )
        )

    assert "ix_messageattachment_expires_at" in plan


@pytest.mark.asyncio
async def test_insert_images_keeps_one_attachment_per_image_path(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()

    await database.insert_images(1, 1, None, [b"old"])
    await database.insert_images(1, 1, None, [b"new"])

    with Session(database.engine) as session:
        attachments = session.exec(select(MessageAttachment)).all()
    assert len(attachments) == 1
    assert attachments[0].file_size == len(b"new")


def test_message_database_creates_fts_table_and_triggers_when_supported(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")

    database = MessageDatabase()

    if not db_module.sqlite_supports_fts5(database.engine):
        pytest.skip("SQLite runtime does not support FTS5")

    with database.engine.connect() as conn:
        tables = {row[0] for row in conn.exec_driver_sql("SELECT name FROM sqlite_schema WHERE type='table'")}
        triggers = {row[0] for row in conn.exec_driver_sql("SELECT name FROM sqlite_schema WHERE type='trigger'")}

    assert "message_fts" in tables
    assert "message_ai_fts" in triggers
    assert "message_ad_fts" in triggers
    assert "message_au_fts" in triggers


@pytest.mark.asyncio
async def test_search_messages_uses_fts_for_content_query_and_preserves_scope(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    if not db_module.sqlite_supports_fts5(database.engine):
        pytest.skip("SQLite runtime does not support FTS5")

    await database.insert(1000, 10, 1, 123, "Alice", "user", "今天讨论 Python 搜索")
    await database.insert(2000, 11, 2, 123, "Bob", "user", "Python 在同群不同人")
    await database.insert(3000, 12, 1, 999, "Alice", "user", "Python 但在其他群")
    await database.insert(4000, 13, 1, None, "Alice", "user", "private Python")

    group_results = await database.search_messages(group_id=123, user_id=1, content_query="Python", limit=10)
    private_results = await database.search_messages(group_id=None, user_id=1, content_query="Python", limit=10)

    assert [message.msg_id for message in group_results] == [11, 10]
    assert [message.msg_id for message in private_results] == [13]


@pytest.mark.asyncio
async def test_search_messages_keeps_like_fallback_for_short_cjk_query(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    await database.insert(1000, 10, 1, 123, "Alice", "user", "讨论数据库性能")

    results = await database.search_messages(group_id=123, user_id=1, content_query="讨论", limit=10)

    assert [message.msg_id for message in results] == [10]


def test_database_diagnostics_reports_pragmas_counts_indexes_and_fts(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    diagnostics = db_module.get_database_diagnostics(database.engine)

    assert diagnostics["sqlite_version"]
    assert diagnostics["fts5_supported"] is True
    assert diagnostics["pragmas"]["busy_timeout"] >= 5000
    assert diagnostics["tables"]["message"]["row_count"] == 0
    assert "ix_message_group_time" in diagnostics["tables"]["message"]["indexes"]
    assert diagnostics["fts"]["message_fts"]["exists"] is True


def test_run_database_maintenance_reports_optimize_and_checkpoint(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    result = db_module.run_database_maintenance(database.engine, checkpoint=True)

    assert result["optimized"] is True
    assert "wal_checkpoint" in result


def test_message_fts_initialization_logs_rebuild(tmp_path: Path, monkeypatch, caplog):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    caplog.set_level("INFO", logger="utils.database")

    MessageDatabase()

    messages = [record.getMessage() for record in caplog.records]
    assert any("FTS5 message index rebuild started" in message for message in messages)
    assert any("FTS5 message index rebuild finished" in message for message in messages)


@pytest.mark.asyncio
async def test_search_messages_can_sort_fts_results_by_relevance(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    database = MessageDatabase()

    if not db_module.sqlite_supports_fts5(database.engine):
        pytest.skip("SQLite runtime does not support FTS5")

    await database.insert(1000, 10, 1, 123, "Alice", "user", "Python Python Python")
    await database.insert(
        2000,
        11,
        1,
        123,
        "Alice",
        "user",
        "Python " + " ".join(f"unrelated{i}" for i in range(40)),
    )

    by_time = await database.search_messages(group_id=123, user_id=1, content_query="Python", limit=10)
    by_relevance = await database.search_messages(
        group_id=123,
        user_id=1,
        content_query="Python",
        limit=10,
        sort="relevance",
    )

    assert [message.msg_id for message in by_time] == [11, 10]
    assert by_relevance[0].msg_id == 10


def test_cleanup_task_execution_history_applies_day_and_per_job_retention(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'frontier-test.db'}")
    engine = db_module.get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE taskexecutionhistory (
                    id INTEGER PRIMARY KEY,
                    job_id VARCHAR NOT NULL,
                    execution_time INTEGER NOT NULL,
                    status VARCHAR NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO taskexecutionhistory(id, job_id, execution_time, status)
                VALUES
                    (1, 'job-a', 1000, 'success'),
                    (2, 'job-a', 2000, 'success'),
                    (3, 'job-a', 3000, 'success'),
                    (4, 'job-b', 1000, 'success'),
                    (5, 'job-b', 4000, 'success')
                """
            )
        )

    deleted = db_module.cleanup_task_execution_history(engine, older_than=1500, keep_per_job=1)

    with engine.connect() as conn:
        remaining = (
            conn.execute(text("SELECT id FROM taskexecutionhistory ORDER BY job_id, execution_time")).scalars().all()
        )
    assert deleted == 3
    assert remaining == [3, 5]
