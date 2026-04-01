# ruff: noqa: S101

import datetime
import json
import sys
import time
import types
import zoneinfo
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_clockwork_task_manager_stub():
    mgr = MagicMock()
    mgr.register_task = AsyncMock(return_value=MagicMock())
    return mgr


@pytest.fixture
def future_time() -> str:
    tz = zoneinfo.ZoneInfo("Asia/Shanghai")
    dt = datetime.datetime.now(tz=tz) + datetime.timedelta(hours=1)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


@pytest.fixture
def reminder_mod(load_tool_module, monkeypatch):
    """Load reminder module with clockwork task_manager stubbed out."""
    # Stub plugins.clockwork as a module with a mock task_manager attribute
    clockwork_stub = types.ModuleType("plugins.clockwork")
    mock_tm = _make_clockwork_task_manager_stub()
    clockwork_stub.task_manager = mock_tm
    monkeypatch.setitem(sys.modules, "plugins.clockwork", clockwork_stub)

    # Also need plugins package
    if "plugins" not in sys.modules:
        plugins_stub = types.ModuleType("plugins")
        monkeypatch.setitem(sys.modules, "plugins", plugins_stub)

    mod = load_tool_module("reminder")
    mod._mock_tm = mock_tm  # convenience reference
    return mod


@pytest.mark.asyncio
async def test_create_reminder_group_context(reminder_mod, future_time):
    """群聊上下文：正常创建提醒，group_ids 包含 group_id。"""
    result = await reminder_mod.create_reminder(
        reminder_text="开会",
        remind_time=future_time,
        private=False,
        user_id="12345",
        group_id=100,
    )

    assert "开会" in result
    reminder_mod._mock_tm.register_task.assert_awaited_once()
    kwargs = reminder_mod._mock_tm.register_task.call_args.kwargs
    assert kwargs["trigger_type"] == "date"
    assert kwargs["group_ids"] == [100]
    assert kwargs["handler_module"] == "plugins.clockwork.reminder_handler"
    assert kwargs["handler_function"] == "fire_reminder"
    payload = json.loads(kwargs["description"])
    assert payload["text"] == "开会"
    assert payload["user_id"] == "12345"
    assert payload["group_id"] == 100
    assert payload["private"] is False


@pytest.mark.asyncio
async def test_create_reminder_dm_context(reminder_mod, future_time):
    """私聊上下文：group_id=None，group_ids 应为空列表。"""
    result = await reminder_mod.create_reminder(
        reminder_text="取快递",
        remind_time=future_time,
        private=False,
        user_id="99999",
        group_id=None,
    )

    assert "取快递" in result
    kwargs = reminder_mod._mock_tm.register_task.call_args.kwargs
    assert kwargs["group_ids"] == []
    payload = json.loads(kwargs["description"])
    assert payload["group_id"] is None


@pytest.mark.asyncio
async def test_create_reminder_past_time_rejected(reminder_mod):
    """过去时间应返回错误消息，不调用 register_task。"""
    result = await reminder_mod.create_reminder(
        reminder_text="做梦",
        remind_time="2020-01-01 00:00:00",
        user_id="1",
        group_id=None,
    )

    assert "将来" in result or "错误" in result
    reminder_mod._mock_tm.register_task.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_reminder_invalid_format(reminder_mod):
    """非法时间格式应返回格式错误消息。"""
    result = await reminder_mod.create_reminder(
        reminder_text="测试",
        remind_time="明天下午三点",
        user_id="1",
        group_id=None,
    )

    assert "格式" in result
    reminder_mod._mock_tm.register_task.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_reminder_job_id_format(reminder_mod, future_time):
    """job_id 格式应为 reminder_{user_id}_{timestamp_ms}。"""
    before_ms = int(time.time() * 1000)
    await reminder_mod.create_reminder(
        reminder_text="喝水",
        remind_time=future_time,
        user_id="42",
        group_id=None,
    )
    after_ms = int(time.time() * 1000)

    job_id: str = reminder_mod._mock_tm.register_task.call_args.kwargs["job_id"]
    assert job_id.startswith("reminder_42_")
    ts = int(job_id.split("_")[-1])
    assert before_ms <= ts <= after_ms
