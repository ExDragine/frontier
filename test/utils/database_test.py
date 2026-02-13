# ruff: noqa: S101

import asyncio

import pytest
from sqlmodel import SQLModel, create_engine

from utils import database as db_module
from utils.database import Message, MessageDatabase, TimeStamp, User


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
async def test_event_database_ops(monkeypatch, memory_engine):
    database = db_module.EventDatabase()
    database.engine = memory_engine
    TimeStamp.metadata.create_all(memory_engine)

    await database.insert("event", "1")
    assert await database.select("event") == "1"
    await database.update("event", "2")
    assert await database.select("event") == "2"
    with pytest.raises(Exception):
        await database.delete("event")
