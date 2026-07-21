# ruff: noqa: S101

import inspect
import types

import pytest

from utils.database import Message


def _message(*, content: str = "这里提到了 Python 搜索功能", role: str = "user") -> Message:
    return Message(
        time=1714521600000,
        msg_id=88,
        user_id=111,
        group_id=123,
        user_name="Alice",
        role=role,
        content=content,
    )


@pytest.mark.asyncio
async def test_search_messages_forwards_filters_and_uses_relevance_for_query(load_tool_module, monkeypatch):
    mod = load_tool_module("memory")
    captured = {}

    class DummyMessageDb:
        async def search_messages(self, **kwargs):
            captured.update(kwargs)
            return [_message()]

    monkeypatch.setattr(mod, "message_db", DummyMessageDb())
    result = await mod.search_messages(
        query="Python",
        config={"configurable": {"user_id": "456", "group_id": 123}},
        target_user_name="Ali",
        role="user",
        limit=20,
        offset=10,
        content_max_chars=600,
    )

    assert captured == {
        "group_id": 123,
        "user_id": 456,
        "content_query": "Python",
        "target_user_id": None,
        "target_user_name": "Ali",
        "msg_id": None,
        "start_time": None,
        "end_time": None,
        "role": "user",
        "limit": 20,
        "offset": 10,
        "sort": "relevance",
    }
    assert "找到 1 条聊天记录（相关度，offset=10）" in result
    assert "msg_id=88" in result
    assert "user_id=111" in result
    assert "用户(Alice)" in result


@pytest.mark.asyncio
async def test_search_messages_without_filters_returns_recent_current_scope(load_tool_module, monkeypatch):
    mod = load_tool_module("memory")
    captured = {}

    class DummyMessageDb:
        async def search_messages(self, **kwargs):
            captured.update(kwargs)
            return [_message(role="assistant")]

    monkeypatch.setattr(mod, "message_db", DummyMessageDb())
    result = await mod.search_messages(config={"configurable": {"user_id": "456", "group_id": 123}})

    assert captured["group_id"] == 123
    assert captured["user_id"] == 456
    assert captured["content_query"] is None
    assert captured["sort"] == "time"
    assert captured["offset"] == 0
    assert "助手(Alice)" in result


@pytest.mark.asyncio
async def test_search_messages_parses_iso_time_and_clamps_page_options(load_tool_module, monkeypatch):
    mod = load_tool_module("memory")
    captured = {}

    class DummyMessageDb:
        async def search_messages(self, **kwargs):
            captured.update(kwargs)
            return [_message(content="x" * 200)]

    monkeypatch.setattr(mod, "message_db", DummyMessageDb())
    result = await mod.search_messages(
        config={"configurable": {"user_id": "456", "group_id": 123}},
        start_date="2026-07-20T00:00:00+08:00",
        end_date="2026-07-20",
        limit=999,
        offset=-3,
        content_max_chars=5,
    )

    assert captured["limit"] == 200
    assert captured["offset"] == 0
    assert captured["start_time"] < captured["end_time"]
    assert "x" * 100 not in result
    assert "x" * 99 + "…" in result


@pytest.mark.asyncio
async def test_search_messages_rejects_invalid_options_and_read_cap(load_tool_module):
    mod = load_tool_module("memory")
    config = {"configurable": {"user_id": "456", "group_id": 123}}

    assert "需要提供 query" in await mod.search_messages(config=config, sort="relevance")
    assert "日期格式错误" in await mod.search_messages(config=config, start_date="not-a-date")
    assert "最多读取 1000 条" in await mod.search_messages(config=config, offset=1000)


@pytest.mark.asyncio
async def test_get_history_messages_is_locked_to_current_group_or_private_chat(load_tool_module, monkeypatch):
    mod = load_tool_module("memory")
    calls = []

    class DummyBot:
        async def get_history_messages(self, **kwargs):
            calls.append(kwargs)
            return [
                types.SimpleNamespace(
                    message_scene=kwargs["message_scene"],
                    peer_id=kwargs["peer_id"],
                    message_seq=1,
                    sender_id=456,
                    time=1714521600,
                    segments=[{"type": "text", "data": {"text": "old"}}],
                )
            ], 0

    monkeypatch.setattr(mod, "get_bot", lambda: DummyBot())
    group_result = await mod.get_history_messages(
        config={"configurable": {"user_id": "456", "group_id": 123}},
        limit=60,
    )
    private_result = await mod.get_history_messages(
        config={"configurable": {"user_id": "456", "group_id": None}},
        start_message_seq=9,
    )

    assert calls == [
        {"message_scene": "group", "peer_id": 123, "start_message_seq": None, "limit": 30},
        {"message_scene": "friend", "peer_id": 456, "start_message_seq": 9, "limit": 20},
    ]
    assert "next_message_seq=0" in group_result
    assert "old" in private_result


def test_history_tool_accepts_only_pagination_and_injected_config(load_tool_module):
    mod = load_tool_module("memory")

    history_fields = set(inspect.signature(mod.get_history_messages).parameters)

    assert history_fields == {"config", "start_message_seq", "limit"}
    assert {"message_scene", "peer_id"}.isdisjoint(history_fields)
