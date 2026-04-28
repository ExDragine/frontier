# ruff: noqa: S101

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
