# ruff: noqa: S101

import json

import pytest
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import Message, MessageDatabase, MessageImage, TimeStamp


@pytest.fixture
def memory_engine(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    return engine


@pytest.mark.asyncio
async def test_message_database_select_and_prepare(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageImage.metadata.create_all(memory_engine)

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
    MessageImage.metadata.create_all(memory_engine)

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
async def test_prepare_message_before_time_excludes_current_and_later_group_messages(monkeypatch, memory_engine):
    database = MessageDatabase()
    database.engine = memory_engine
    Message.metadata.create_all(memory_engine)
    MessageImage.metadata.create_all(memory_engine)

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
    MessageImage.metadata.create_all(memory_engine)

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
