# ruff: noqa: S101

import json
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import (
    MESSAGE_SOURCE_TYPE_FORWARD_NODE,
    MESSAGE_SOURCE_TYPE_NORMAL,
    Message,
    MessageAttachment,
    MessageDatabase,
    TimeStamp,
)
from utils.message_normalizer import NORMALIZED_VERSION, DerivedMessage


@pytest.fixture
def memory_engine(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    return engine


def test_ensure_message_schema_adds_normalization_columns(memory_engine):
    with memory_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE message (
                    time INTEGER NOT NULL PRIMARY KEY,
                    msg_id INTEGER,
                    user_id INTEGER NOT NULL,
                    group_id INTEGER,
                    user_name VARCHAR,
                    role VARCHAR NOT NULL,
                    content VARCHAR NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO message (time, msg_id, user_id, group_id, user_name, role, content)
                VALUES (1000, 10, 1, 123, 'Alice', 'user', 'legacy')
                """
            )
        )

    db_module.ensure_message_schema(memory_engine)

    columns = {column["name"] for column in inspect(memory_engine).get_columns("message")}
    assert {
        "raw_segments_json",
        "normalized_version",
        "normalized_status",
        "source_type",
        "parent_msg_id",
        "parent_msg_time",
        "parent_forward_id",
    }.issubset(columns)
    with memory_engine.connect() as conn:
        row = conn.execute(
            text("SELECT normalized_version, normalized_status, source_type FROM message WHERE time = 1000")
        ).one()
    assert row == (0, "legacy", MESSAGE_SOURCE_TYPE_NORMAL)


@pytest.mark.asyncio
async def test_message_database_select_and_prepare(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1, 101, 1, None, "u1", "user", "hello")
    await database.insert(2, 102, 1, None, "u1", "user", "world")
    await database.insert(3, 103, 1, 5, "u1", "user", "group")

    user_messages = await database.select(user_id=1)
    assert len(user_messages) == 3

    group_messages = await database.select(group_id=5)
    assert len(group_messages) == 1

    assert await database.select() is None

    prepared = await database.prepare_message(user_id=1)
    assert prepared
    assert prepared[0]["role"] == "user"


@pytest.mark.asyncio
async def test_prepare_message_injects_all_available_images_without_window_limit(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    for msg_time in range(1, 13):
        await database.insert(msg_time, 100 + msg_time, 1, None, "u1", "user", f"history-{msg_time}")
        await database.insert_images(msg_time, 1, None, [f"image-{msg_time}".encode()])
    await database.insert(13, 113, 1, None, "u1", "user", "current")

    prepared = await database.prepare_message(user_id=1, query_numbers=20)

    image_parts = [
        part
        for message in prepared
        if isinstance(message["content"], list)
        for part in message["content"]
        if part.get("type") == "image_url"
    ]
    assert len(image_parts) == 12


@pytest.mark.asyncio
async def test_prepare_message_injects_images_from_message_attachments(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    image_path = Path("cache/sandbox/memory/1/files/images/1000_0.jpg")
    (tmp_path / image_path).parent.mkdir(parents=True)
    (tmp_path / image_path).write_bytes(b"attachment-image")
    await database.insert(1000, 101, 1, None, "u1", "user", "history")
    await database.insert_attachment(
        msg_time=1000,
        msg_id=101,
        user_id=1,
        group_id=None,
        kind="image",
        physical_path=str(image_path),
        virtual_path="/memory/1/files/images/1000_0.jpg",
        file_name="1000_0.jpg",
        file_size=len(b"attachment-image"),
        expires_at=9_999_999_999_999,
    )
    await database.insert(2000, 102, 1, None, "u1", "user", "current")

    prepared = await database.prepare_message(user_id=1, query_numbers=10, before_time=2000)

    assert isinstance(prepared[0]["content"], list)
    assert prepared[0]["content"][0]["type"] == "text"
    image_parts = [part for part in prepared[0]["content"] if part.get("type") == "image_url"]
    assert len(image_parts) == 1


@pytest.mark.asyncio
async def test_insert_images_records_memory_file_attachment(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageAttachment.metadata.create_all(memory_engine)

    paths = await database.insert_images(1000, 7, 123, [b"image-bytes"])

    expected_path = Path("cache/sandbox/memory/123/files/images/1000_0.jpg")
    assert paths == [str(expected_path)]
    assert (tmp_path / expected_path).read_bytes() == b"image-bytes"

    attachments = await database.select_attachments_by_msg_time(1000)
    assert len(attachments) == 1
    attachment = attachments[0]
    assert attachment.kind == "image"
    assert attachment.physical_path == str(expected_path)
    assert attachment.virtual_path == "/memory/123/files/images/1000_0.jpg"
    assert attachment.file_size == len(b"image-bytes")


@pytest.mark.asyncio
async def test_cleanup_expired_attachments_deletes_only_db_tracked_files(monkeypatch, memory_engine, tmp_path):
    monkeypatch.chdir(tmp_path)
    database = MessageDatabase()
    database.engine = memory_engine
    MessageAttachment.metadata.create_all(memory_engine)

    tracked = Path("cache/sandbox/memory/123/files/images/expired.jpg")
    untracked = Path("cache/sandbox/memory/123/files/images/keep.jpg")
    (tmp_path / tracked).parent.mkdir(parents=True)
    (tmp_path / tracked).write_bytes(b"old")
    (tmp_path / untracked).write_bytes(b"keep")

    await database.insert_attachment(
        msg_time=1000,
        msg_id=50,
        user_id=7,
        group_id=123,
        kind="image",
        physical_path=str(tracked),
        virtual_path="/memory/123/files/images/expired.jpg",
        file_name="expired.jpg",
        file_size=3,
        expires_at=1,
    )

    deleted = await database.cleanup_expired_attachments(now_ms=2)

    assert deleted == 1
    assert not (tmp_path / tracked).exists()
    assert (tmp_path / untracked).exists()
    assert await database.select_attachments_by_msg_time(1000) == []


@pytest.mark.asyncio
async def test_prepare_message_before_time_excludes_current_and_later_group_messages(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 201, 10, 123, "Old", "user", "old message")
    await database.insert(2000, 202, 10, 123, "Alice", "user", "alice current")
    await database.insert(2001, 203, 20, 123, "Bob", "user", "bob concurrent")

    prepared = await database.prepare_message(user_id=10, group_id=123, query_numbers=10, before_time=2000)

    content = prepared[0]["content"]
    assert "old message" in content
    assert "alice current" not in content
    assert "bob concurrent" not in content


@pytest.mark.asyncio
async def test_prepare_message_includes_chat_scope_metadata(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 201, 10, 123, "Alice", "user", "group old")
    await database.insert(2000, 202, 10, 123, "Alice", "user", "group current")
    await database.insert(3000, 301, 20, None, "Bob", "user", "private old")
    await database.insert(4000, 302, 20, None, "Bob", "user", "private current")

    group_prepared = await database.prepare_message(user_id=10, group_id=123, query_numbers=10, before_time=2000)
    group_payload = json.loads(group_prepared[0]["content"])
    assert group_payload["metadata"]["chat_type"] == "group"
    assert group_payload["metadata"]["group_id"] == 123
    assert group_payload["metadata"]["user_id"] == "10"

    private_prepared = await database.prepare_message(user_id=20, query_numbers=10, before_time=4000)
    private_payload = json.loads(private_prepared[0]["content"])
    assert private_payload["metadata"]["chat_type"] == "private"
    assert private_payload["metadata"]["group_id"] is None
    assert private_payload["metadata"]["user_id"] == "20"


@pytest.mark.asyncio
async def test_select_by_msg_id_returns_message_from_same_group(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1, 200, 1, 10, "Alice", "user", "wrong group")
    await database.insert(2, 200, 2, 20, "Bob", "user", "quoted message")

    result = await database.select_by_msg_id(msg_id=200, group_id=20)

    assert result is not None
    assert result.content == "quoted message"


@pytest.mark.asyncio
async def test_prepare_message_excludes_forward_node_derived_records(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(
        1000,
        10,
        1,
        123,
        "Alice",
        "user",
        "parent\n[合并转发]\nBob: derived content",
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    await database.replace_derived_messages(
        parent_msg_time=1000,
        parent_msg_id=10,
        user_id=1,
        group_id=123,
        role="user",
        derived_messages=[
            DerivedMessage(
                sender_name="Bob",
                content="derived content",
                raw_segments_json="[]",
                forward_id="fwd-1",
            )
        ],
        normalized_version=NORMALIZED_VERSION,
    )
    await database.insert(2000, 11, 1, 123, "Alice", "user", "current")

    selected = await database.select(group_id=123, query_numbers=10)
    prepared = await database.prepare_message(user_id=1, group_id=123, query_numbers=10, before_time=2000)
    search_results = await database.search_messages(group_id=123, user_id=1, content_query="derived content", limit=10)

    assert all(message.source_type != MESSAGE_SOURCE_TYPE_FORWARD_NODE for message in selected)
    assert all(message.source_type == MESSAGE_SOURCE_TYPE_NORMAL for message in search_results)
    assert [message.msg_id for message in search_results] == [10]
    assert len(prepared) == 1
    assert "derived content" in prepared[0]["content"]


@pytest.mark.asyncio
async def test_semantic_search_ignores_forward_node_derived_records(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(
        1000,
        10,
        1,
        123,
        "Alice",
        "user",
        "parent content with nested forward detail",
        normalized_version=NORMALIZED_VERSION,
        normalized_status="complete",
    )
    await database.replace_derived_messages(
        parent_msg_time=1000,
        parent_msg_id=10,
        user_id=1,
        group_id=123,
        role="user",
        derived_messages=[
            DerivedMessage(
                sender_name="Bob",
                content="nested forward detail",
                raw_segments_json="[]",
                forward_id="fwd-1",
            )
        ],
        normalized_version=NORMALIZED_VERSION,
    )

    class FakeVectorIndex:
        available = True

        def search(self, **_kwargs):
            return [(-1_000_001, 0.01), (1000, 0.2)]

    database._vector_index = FakeVectorIndex()

    results = await database.search_messages(
        group_id=123,
        user_id=1,
        content_query="nested detail",
        mode="semantic",
        limit=10,
    )

    assert [message.time for message in results] == [1000]


def test_add_message_to_vector_index_skips_forward_node_records(memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    indexed: list[int] = []

    class FakeVectorIndex:
        available = True

        def add_message(self, message):
            indexed.append(message.time)

    database._vector_index = FakeVectorIndex()

    database._add_message_to_vector_index(
        Message(
            time=-1,
            msg_id=None,
            user_id=1,
            group_id=123,
            user_name="Bob",
            role="user",
            content="derived",
            source_type=MESSAGE_SOURCE_TYPE_FORWARD_NODE,
        )
    )
    database._add_message_to_vector_index(
        Message(time=1000, msg_id=10, user_id=1, group_id=123, user_name="Alice", role="user", content="normal")
    )

    assert indexed == [1000]


@pytest.mark.asyncio
async def test_search_messages_filters_history_by_scope_name_id_and_content(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 10, 1, 123, "Alice", "user", "今天讨论 Python 搜索")
    await database.insert(2000, 11, 2, 123, "Bob", "user", "无关内容")
    await database.insert(3000, 12, 1, 123, "Alice", "user", "另一个 keyword")
    await database.insert(4000, 13, 3, 999, "Mallory", "user", "Python 但在其他群")
    await database.insert(5000, 14, 1, None, "Alice", "user", "private Python")

    group_content = await database.search_messages(group_id=123, user_id=1, content_query="Python", limit=10)
    assert [message.msg_id for message in group_content] == [10]

    alice_messages = await database.search_messages(group_id=123, user_id=1, target_user_name="Ali", limit=10)
    assert [message.msg_id for message in alice_messages] == [12, 10]

    exact_message = await database.search_messages(group_id=123, user_id=1, msg_id=11, limit=10)
    assert [message.user_name for message in exact_message] == ["Bob"]

    private_messages = await database.search_messages(group_id=None, user_id=1, content_query="Python", limit=10)
    assert [message.msg_id for message in private_messages] == [14]


@pytest.mark.asyncio
async def test_count_group_messages_since(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 10, 1, 123, "Alice", "user", "old")
    await database.insert(2000, 11, 2, 123, "Bob", "user", "recent")
    await database.insert(3000, 12, 3, 123, "Assistant", "assistant", "recent assistant")
    await database.insert(4000, 13, 4, 999, "Mallory", "user", "other group")

    count = await database.count_group_messages_since(group_id=123, since_time=1500)

    assert count == 2


@pytest.mark.asyncio
async def test_latest_group_role_message_time(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)

    await database.insert(1000, 10, 1, 123, "Assistant", "assistant", "old assistant")
    await database.insert(2000, 11, 2, 123, "Alice", "user", "user")
    await database.insert(3000, 12, 3, 123, "Assistant", "assistant", "latest assistant")
    await database.insert(4000, 13, 4, 999, "Assistant", "assistant", "other group")

    latest_time = await database.latest_group_role_message_time(group_id=123, role="assistant")

    assert latest_time == 3000


@pytest.mark.asyncio
async def test_event_database_ops(monkeypatch, memory_engine):
    database = db_module.EventDatabase()
    database.engine = memory_engine
    TimeStamp.metadata.create_all(memory_engine)

    await database.insert("event", "1")
    assert await database.select("event") == "1"
    await database.update("event", "2")
    assert await database.select("event") == "2"
    await database.delete("event")
    assert await database.select("event") is None
