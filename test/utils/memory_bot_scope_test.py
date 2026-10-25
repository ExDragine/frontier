"""Memory tools and both SQL search paths isolate QQ bot accounts."""

# ruff: noqa: S101

import pytest
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import MessageDatabase
from utils.database.fts import ensure_message_fts


@pytest.fixture
def database(monkeypatch):
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = create_engine("sqlite://")
    database._attachments.engine = database.engine
    db_module.Message.metadata.create_all(database.engine)
    ensure_message_fts(database.engine)
    return database


async def _populate(database, group_id):
    for time, account, content in [
        (1000, 99, "needle visible"),
        (1001, 98, "needle other account"),
        (1002, None, "needle ambiguous owner"),
    ]:
        await database.insert(time, time, 10, group_id, "Alice", "user", content, bot_user_id=account)


@pytest.mark.asyncio
@pytest.mark.parametrize("group_id", [None, 20])
@pytest.mark.parametrize("sort", ["time", "relevance"])
@pytest.mark.parametrize("path", ["fts", "like", "fallback"])
async def test_database_search_and_details_filter_bot_before_pagination(database, monkeypatch, group_id, sort, path):
    await _populate(database, group_id)
    if path == "like":
        monkeypatch.setattr(database, "_can_use_fts", lambda _query: False)
    elif path == "fallback":
        def unavailable(*_args, **_kwargs):
            raise RuntimeError("synthetic FTS failure")

        monkeypatch.setattr(database, "_search_messages_fts", unavailable)
        monkeypatch.setattr(database, "_search_messages_fts_details", unavailable)

    kwargs = {
        "group_id": group_id,
        "user_id": 10,
        "content_query": "needle",
        "sort": sort,
        "bot_user_id": 99,
        "limit": 1,
    }
    messages = await database.search_messages(**kwargs)
    details = await database.search_message_details(**kwargs)

    assert [message.content for message in messages] == ["needle visible"]
    assert [result.message.content for result in details] == ["needle visible"]
    if path == "fts":
        assert details[0].score is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("group_id", [None, 20])
async def test_memory_tools_use_bound_bot_for_recent_and_search(database, load_tool_module, monkeypatch, group_id):
    await _populate(database, group_id)
    memory = load_tool_module("memory")
    monkeypatch.setattr(memory, "message_db", database)
    config = {"configurable": {"user_id": "10", "group_id": group_id, "bot_user_id": "99"}}

    recent = await memory.get_recent_conversation(config=config)
    search = await memory.search_messages(config=config, query="needle")

    for result in [recent, search]:
        assert "needle visible" in result
        assert "other account" not in result
        assert "ambiguous owner" not in result


@pytest.mark.asyncio
@pytest.mark.parametrize("bot_id", ["invalid", "", 0, True])
async def test_invalid_bound_bot_never_falls_back_to_unscoped_read(load_tool_module, monkeypatch, bot_id):
    memory = load_tool_module("memory")

    async def reject(**_kwargs):
        raise AssertionError("invalid bot identity must not query history")

    monkeypatch.setattr(memory.message_db, "search_messages", reject)
    config = {"configurable": {"user_id": "10", "bot_user_id": bot_id}}
    assert "机器人上下文错误" in await memory.get_recent_conversation(config=config)
    assert "机器人上下文错误" in await memory.search_messages(config=config, query="needle")


@pytest.mark.asyncio
async def test_platform_history_selects_bound_bot(load_tool_module, monkeypatch):
    memory = load_tool_module("memory")
    selected = []

    class Bot:
        async def get_history_messages(self, **_kwargs):
            return [], None

    def get_bot(account):
        selected.append(account)
        return Bot()

    monkeypatch.setattr(memory, "get_bot", get_bot)
    await memory.get_history_messages(config={"configurable": {"user_id": "10", "bot_user_id": "99"}})
    assert selected == ["99"]
