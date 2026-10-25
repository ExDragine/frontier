"""Normal QQ history respects bot ownership even without session caching."""

# ruff: noqa: S101

import json

import pytest
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import MessageDatabase


@pytest.fixture
def database(monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = create_engine("sqlite://")
    database._attachments.engine = database.engine
    db_module.Message.metadata.create_all(database.engine)
    return database


@pytest.mark.asyncio
@pytest.mark.parametrize("group_id", [None, 20])
async def test_normal_history_excludes_other_and_unknown_bot_ownership(database, group_id):
    for time, account, content in [
        (1000, 99, "first account"),
        (1001, 98, "second account"),
        (1002, None, "ambiguous owner"),
    ]:
        await database.insert(
            time, time, 10, group_id, "Alice", "user", content, bot_user_id=account,
        )

    rows = await database.select(user_id=10, group_id=group_id, bot_user_id=99)
    assert [row.content for row in rows] == ["first account"]
    history = await database.prepare_message(
        user_id=10, group_id=group_id, before_time=2000, bot_user_id=99,
    )
    assert [json.loads(message["content"])["content"] for message in history] == ["first account"]
    other_history = await database.prepare_message(
        user_id=10, group_id=group_id, before_time=2000, bot_user_id=98,
    )
    assert [json.loads(message["content"])["content"] for message in other_history] == ["second account"]


@pytest.mark.asyncio
async def test_history_without_account_filter_keeps_legacy_database_api(database):
    await database.insert(1000, 1, 10, None, "Alice", "user", "first", bot_user_id=99)
    await database.insert(1001, 2, 10, None, "Alice", "user", "second", bot_user_id=98)

    rows = await database.select(user_id=10)
    assert [row.content for row in rows] == ["second", "first"]
