# ruff: noqa: S101

import pytest

from utils.database import Message


@pytest.mark.asyncio
async def test_search_messages_tool_forwards_filters_and_formats_results(load_tool_module, monkeypatch):
    mod = load_tool_module("memory")
    captured = {}

    class DummyMessageDb:
        async def search_messages(self, **kwargs):
            captured.update(kwargs)
            return [
                Message(
                    time=1714521600000,
                    msg_id=88,
                    user_id=111,
                    group_id=123,
                    user_name="Alice",
                    role="user",
                    content="这里提到了 Python 搜索功能",
                )
            ]

    monkeypatch.setattr(mod, "message_db", DummyMessageDb())

    result = await mod.search_messages(
        query="Python",
        config={"configurable": {"user_id": "456", "group_id": 123}},
        target_user_name="Ali",
        limit=20,
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
        "limit": 20,
    }
    assert "找到 1 条聊天记录" in result
    assert "msg_id=88" in result
    assert "user_id=111" in result
    assert "用户(Alice)" in result
    assert "这里提到了 Python 搜索功能" in result


@pytest.mark.asyncio
async def test_search_messages_tool_requires_at_least_one_filter(load_tool_module):
    mod = load_tool_module("memory")

    result = await mod.search_messages(config={"configurable": {"user_id": "456", "group_id": 123}})

    assert "请至少提供" in result
