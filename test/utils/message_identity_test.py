# ruff: noqa: S101

import asyncio
import json
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlmodel import Session, select

from plugins.agent.message_normalizer import DerivedMessage
from utils import database as db_module
from utils.database import Message, MessageAttachment, MessageDatabase


@pytest.mark.parametrize("table,definition", [
    ("message", "time INTEGER PRIMARY KEY, content TEXT"),
    ("messageattachment", "id INTEGER PRIMARY KEY, msg_time INTEGER"),
])
def test_startup_rejects_old_schema_without_altering_it(tmp_path, monkeypatch, table, definition):
    engine = db_module.get_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.exec_driver_sql(f"CREATE TABLE {table} ({definition})")
    monkeypatch.setattr(db_module, "DATABASE_FILE", str(engine.url))
    with engine.connect() as conn:
        before = conn.exec_driver_sql(f"PRAGMA table_info({table})").all()
    with pytest.raises(RuntimeError, match="结构过旧或不兼容"):
        MessageDatabase()
    with engine.connect() as conn:
        assert conn.exec_driver_sql(f"PRAGMA table_info({table})").all() == before
    assert inspect(engine).get_table_names() == [table]


def test_schema_validation_rejects_wrong_primary_key(tmp_path):
    engine = db_module.get_engine(f"sqlite:///{tmp_path / 'wrong-pk.db'}")
    Message.__table__.create(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE copied AS SELECT * FROM message")
        conn.exec_driver_sql("DROP TABLE message")
        conn.exec_driver_sql("ALTER TABLE copied RENAME TO message")
    with pytest.raises(RuntimeError, match="主键不匹配"):
        db_module.validate_database_schema(engine, Message)


@pytest.mark.asyncio
async def test_current_database_restart_preserves_data_and_old_directories(isolated_database):
    database = isolated_database
    inserted = await database.insert(1000, 1, 10, 123, "Alice", "user", "retained")
    old_path = Path("cache/sandbox/memory/123/SOUL.md")
    old_path.parent.mkdir(parents=True)
    old_path.write_text("retained file", encoding="utf-8")
    with database.engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE frontier_schema_version (component TEXT PRIMARY KEY, version INTEGER)")
        conn.exec_driver_sql("INSERT INTO frontier_schema_version VALUES ('message_identity', 1)")
    restarted = MessageDatabase()
    with Session(restarted.engine) as session:
        assert session.get(Message, inserted.message_id).content == "retained"
    assert old_path.read_text(encoding="utf-8") == "retained file"
    assert not Path("cache/sandbox/memory/group-123/SOUL.md").exists()
    with restarted.engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT version FROM frontier_schema_version").scalar_one() == 1


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(db_module, "DATABASE_FILE", f"sqlite:///{tmp_path / 'identity-test.db'}")
    return MessageDatabase()


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
