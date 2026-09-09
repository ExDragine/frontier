# ruff: noqa: S101

import asyncio
import json
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlmodel import Session, select

from utils import database as db_module
from utils import storage_migrations
from utils.database import Message, MessageAttachment, MessageDatabase
from utils.message_normalizer import DerivedMessage


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'identity-test.db'}")
    return MessageDatabase()


def _legacy_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    engine = db_module.get_engine(f"sqlite:///{tmp_path / 'legacy-test.db'}")
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE message (
                time INTEGER NOT NULL PRIMARY KEY, msg_id INTEGER, user_id INTEGER NOT NULL,
                group_id INTEGER, user_name TEXT, role TEXT NOT NULL, content TEXT NOT NULL,
                custom_retained TEXT UNIQUE CHECK(custom_retained != '')
            )
        """)
        conn.exec_driver_sql("CREATE INDEX custom_retained_index ON message(custom_retained)")
        conn.exec_driver_sql("""
            INSERT INTO message VALUES
            (1000, 7, 10, 123, 'Alice', 'user', 'searchable parent', 'retain me'),
            (2000, 7, 10, 123, 'Alice', 'user', 'historical duplicate', NULL),
            (-1000001, NULL, 10, 123, 'Bob', 'user', 'forward child', NULL)
        """)
    db_module.ensure_message_schema(engine)
    MessageAttachment.__table__.create(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP INDEX ix_messageattachment_message_id")
        conn.exec_driver_sql("ALTER TABLE messageattachment DROP COLUMN message_id")
        conn.exec_driver_sql("""
            UPDATE message SET parent_msg_time=1000, parent_msg_id=7, source_type='forward_node'
            WHERE time=-1000001
        """)
        conn.execute(text("UPDATE message SET reply_context_json=:reply WHERE time=1000"), {
            "reply": json.dumps({"content": "quoted"}),
        })
        conn.exec_driver_sql("""
            INSERT INTO messageattachment (msg_time,msg_id,user_id,group_id,workspace_key,kind,source_type,
                file_name,physical_path,virtual_path,created_at,expires_at,metadata_json)
            VALUES (1000,7,10,123,'group-123','image','message','picture.png',
                'picture.png','/memory/group-123/picture.png',1000,9999,'{}')
        """)
        conn.exec_driver_sql("""
            CREATE VIRTUAL TABLE message_fts USING fts5(content, content='message', content_rowid='time')
        """)
        conn.exec_driver_sql("INSERT INTO message_fts(message_fts) VALUES ('rebuild')")
    return engine


def test_identity_migration_preserves_rows_links_fts_and_extra_columns(tmp_path, monkeypatch):
    engine = _legacy_database(tmp_path, monkeypatch)
    migrated = storage_migrations.migrate_message_identity(engine, rebuild_fts=db_module._ensure_message_fts_connection)

    assert migrated is True
    assert inspect(engine).get_pk_constraint("message")["constrained_columns"] == ["id"]
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM message").scalar() == 3
        assert conn.exec_driver_sql("SELECT id, time, custom_retained FROM message WHERE time=1000").one() == (
            1000, 1000, "retain me",
        )
        assert conn.exec_driver_sql("SELECT parent_message_id FROM message WHERE time=-1000001").scalar() == 1000
        assert conn.exec_driver_sql("SELECT message_id FROM messageattachment").scalar() == 1000
        assert conn.exec_driver_sql("SELECT rowid FROM message_fts WHERE message_fts MATCH 'searchable'").scalar() == 1000
        assert conn.exec_driver_sql("SELECT count(platform_key) FROM message").scalar() == 1
        assert conn.exec_driver_sql("SELECT platform_key FROM message WHERE time=2000").scalar() == "milky:0:group:123:7"
        assert conn.exec_driver_sql("SELECT custom_retained FROM message WHERE time=1000").scalar() == "retain me"
        assert json.loads(conn.exec_driver_sql("SELECT reply_context_json FROM message WHERE time=1000").scalar()) == {
            "content": "quoted",
        }
        assert conn.exec_driver_sql("PRAGMA integrity_check").scalar() == "ok"
    assert "custom_retained_index" in {index["name"] for index in inspect(engine).get_indexes("message")}
    assert [item["column_names"] for item in inspect(engine).get_unique_constraints("message")] == [["custom_retained"]]
    assert inspect(engine).get_check_constraints("message")

    def unexpected_rebuild(_conn):
        pytest.fail("Repeated migrations must not rebuild FTS")

    assert storage_migrations.migrate_message_identity(engine, rebuild_fts=unexpected_rebuild) is False


def test_failed_identity_migration_rolls_back_ddl_rows_links_and_version(tmp_path, monkeypatch):
    engine = _legacy_database(tmp_path, monkeypatch)

    def fail_after_rebuild(_conn):
        raise RuntimeError("injected migration failure")

    with pytest.raises(RuntimeError, match="injected migration failure"):
        storage_migrations.migrate_message_identity(engine, rebuild_fts=fail_after_rebuild)

    assert inspect(engine).get_pk_constraint("message")["constrained_columns"] == ["time"]
    assert "frontier_schema_version" not in inspect(engine).get_table_names()
    assert "message_identity_new" not in inspect(engine).get_table_names()
    assert "message_id" not in {column["name"] for column in inspect(engine).get_columns("messageattachment")}
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM message").scalar() == 3
        assert conn.exec_driver_sql("SELECT rowid FROM message_fts WHERE message_fts MATCH 'searchable'").scalar() == 1000
    assert storage_migrations.migrate_message_identity(engine, rebuild_fts=db_module._ensure_message_fts_connection)


def test_custom_foreign_keys_stop_unsafe_automatic_rebuild(tmp_path, monkeypatch):
    engine = _legacy_database(tmp_path, monkeypatch)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE custom_reference (message_time INTEGER REFERENCES message(time) ON DELETE CASCADE)")
        conn.exec_driver_sql("INSERT INTO custom_reference VALUES (1000)")
    with pytest.raises(RuntimeError, match="foreign keys"):
        storage_migrations.migrate_message_identity(engine, rebuild_fts=db_module._ensure_message_fts_connection)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT message_time FROM custom_reference").scalar() == 1000
        assert conn.exec_driver_sql("SELECT count(*) FROM message").scalar() == 3
        assert conn.exec_driver_sql("SELECT rowid FROM message_fts WHERE message_fts MATCH 'searchable'").scalar() == 1000


@pytest.mark.asyncio
async def test_application_startup_migrates_legacy_database_and_accepts_equal_time(tmp_path, monkeypatch):
    engine = _legacy_database(tmp_path, monkeypatch)
    monkeypatch.setattr(db_module, "DATABASE_FILE", str(engine.url))
    database = MessageDatabase()
    inserted = await database.insert(1000, 8, 10, 123, "Alice", "user", "another searchable event")
    assert inserted.inserted
    assert inserted.message_id not in (1000, 2000, -1000001)
    assert inserted.time == 1000
    found = await database.search_messages(group_id=123, user_id=None, content_query="searchable")
    assert {message.id for message in found} == {1000, inserted.message_id}


@pytest.mark.asyncio
async def test_platform_duplicates_are_atomic_and_scoped(isolated_database):
    database = isolated_database
    results = await asyncio.gather(*[
        database.insert(1000 + index, 7, 10, 123, "Alice", "user", "same event", bot_user_id=99)
        for index in range(8)
    ])
    assert sum(result.inserted for result in results) == 1
    assert len({result.message_id for result in results}) == 1
    assert len({result.time for result in results}) == 1
    for peer, group, bot in [(10, 124, 99), (10, None, 99), (11, None, 99), (10, 123, 100)]:
        result = await database.insert(1000, 7, peer, group, "Alice", "user", "distinct event", bot_user_id=bot)
        assert result.inserted
    with Session(database.engine) as session:
        assert len(session.exec(select(Message)).all()) == 5


@pytest.mark.asyncio
async def test_equal_timestamps_keep_media_context_and_fts_separate(isolated_database):
    database = isolated_database
    first = await database.insert(1000, 7, 10, 123, "Alice", "user", "searchable first [图片]")
    second = await database.insert(1000, 8, 20, 123, "Bob", "user", "searchable second [图片]")
    other_group = await database.insert(1000, 7, 10, 456, "Alice", "user", "searchable foreign [图片]")
    assert len({first.message_id, second.message_id, other_group.message_id}) == 3
    first_paths = await database.insert_images(1000, 10, 123, [b"alice"], message_id=first.message_id)
    second_paths = await database.insert_images(1000, 20, 123, [b"bob"], message_id=second.message_id)
    await database.insert_images(1000, 10, 456, [b"foreign"], message_id=other_group.message_id)
    assert first_paths != second_paths
    assert Path(first_paths[0]).read_bytes() == b"alice"
    assert Path(second_paths[0]).read_bytes() == b"bob"
    with pytest.raises(ValueError, match="Ambiguous"):
        await database.finalize_message_context(time=1000)
    await database.finalize_message_context(time=1000, message_id=second.message_id)
    records = await database.search_messages(group_id=123, user_id=None, content_query="searchable")
    assert [record.id for record in records] == [second.message_id, first.message_id]
    payloads = [json.loads(message["content"]) for message in await database.prepare_message_records(records)]
    assert payloads[0]["attachments"][0]["path"] != payloads[1]["attachments"][0]["path"]
    await database.update_message_normalization(
        time=1000, message_id=first.message_id, content="changed only Alice", raw_segments_json=None,
        normalized_version=2, normalized_status="complete",
    )
    remaining = await database.search_messages(group_id=123, user_id=None, content_query="searchable")
    assert [message.id for message in remaining] == [second.message_id]
    with Session(database.engine) as session:
        session.delete(session.get(Message, second.message_id))
        session.commit()
    assert await database.search_messages(group_id=123, user_id=None, content_query="searchable") == []


@pytest.mark.asyncio
async def test_explicit_identity_rejects_media_from_another_scope(isolated_database):
    database = isolated_database
    stored = await database.insert(1000, 7, 10, 123, "Alice", "user", "[图片]")
    with pytest.raises(ValueError, match="conversation"):
        await database.insert_images(1000, 10, 456, [b"wrong group"], message_id=stored.message_id)
    with Session(database.engine) as session:
        assert session.exec(select(MessageAttachment)).all() == []


def test_newer_identity_version_fails_without_downgrading(isolated_database):
    engine = isolated_database.engine
    with engine.begin() as conn:
        conn.exec_driver_sql("UPDATE frontier_schema_version SET version=999 WHERE component='message_identity'")
    with pytest.raises(RuntimeError, match="newer"):
        storage_migrations.migrate_message_identity(engine, rebuild_fts=db_module._ensure_message_fts_connection)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT version FROM frontier_schema_version").scalar() == 999


@pytest.mark.asyncio
async def test_derived_replacement_targets_parent_identity(isolated_database):
    database = isolated_database
    first = await database.insert(1000, 7, 10, 123, "Alice", "user", "forward A")
    second = await database.insert(1000, 8, 20, 123, "Bob", "user", "forward B")
    for parent, peer, seq, content in [(first, 10, 7, "child A"), (second, 20, 8, "child B")]:
        await database.replace_derived_messages(
            parent_msg_time=1000, parent_message_id=parent.message_id, parent_msg_id=seq,
            user_id=peer, group_id=123, role="user", normalized_version=2,
            derived_messages=[DerivedMessage(sender_name="Forward", content=content, raw_segments_json="[]", forward_id="f")],
        )
    await database.replace_derived_messages(
        parent_msg_time=1000, parent_message_id=first.message_id, parent_msg_id=7,
        user_id=10, group_id=123, role="user", normalized_version=2, derived_messages=[],
    )
    with Session(database.engine) as session:
        children = session.exec(select(Message).where(Message.source_type == "forward_node")).all()
    assert [(child.content, child.parent_message_id) for child in children] == [("child B", second.message_id)]
