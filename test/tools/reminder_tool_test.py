# ruff: noqa: S101

import datetime
import sys
import time
import types
import zoneinfo
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_clockwork_task_manager_stub():
    mgr = MagicMock()
    mgr.register_scheduled_task = AsyncMock(return_value=MagicMock())
    return mgr


@pytest.fixture
def future_time() -> str:
    tz = zoneinfo.ZoneInfo("Asia/Shanghai")
    dt = datetime.datetime.now(tz=tz) + datetime.timedelta(hours=1)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


@pytest.fixture
def reminder_mod(load_tool_module, monkeypatch):
    """Load reminder module with clockwork task_manager stubbed out."""
    clockwork_stub = types.ModuleType("plugins.clockwork")
    mock_tm = _make_clockwork_task_manager_stub()
    clockwork_stub.task_manager = mock_tm
    monkeypatch.setitem(sys.modules, "plugins.clockwork", clockwork_stub)

    if "plugins" not in sys.modules:
        plugins_stub = types.ModuleType("plugins")
        monkeypatch.setitem(sys.modules, "plugins", plugins_stub)
    tools_stub = types.ModuleType("tools")
    tools_stub.__path__ = [str(Path(__file__).resolve().parents[2] / "tools")]
    monkeypatch.setitem(sys.modules, "tools", tools_stub)

    mod = load_tool_module("reminder")
    mod._mock_tm = mock_tm
    return mod


def _cfg(user_id: str, group_id=None) -> dict:
    return {"configurable": {"user_id": user_id, "group_id": group_id}}


@pytest.mark.asyncio
async def test_create_reminder_group_context(reminder_mod, future_time):
    """群聊上下文：正常创建提醒，group_ids 包含 group_id。"""
    result = await reminder_mod.create_reminder(
        reminder_text="开会",
        remind_time=future_time,
        private=False,
        config=_cfg("12345", 100),
    )

    assert "开会" in result
    reminder_mod._mock_tm.register_scheduled_task.assert_awaited_once()
    kwargs = reminder_mod._mock_tm.register_scheduled_task.call_args.kwargs
    assert kwargs["trigger_type"] == "date"
    assert kwargs["target_type"] == "group"
    assert kwargs["target_id"] == "100"
    assert kwargs["owner_user_id"] == "12345"
    assert "开会" in kwargs["prompt"]
    assert kwargs["created_from"] == "reminder_tool"


@pytest.mark.asyncio
async def test_create_reminder_dm_context(reminder_mod, future_time):
    """私聊上下文：group_id=None，group_ids 应为空列表。"""
    result = await reminder_mod.create_reminder(
        reminder_text="取快递",
        remind_time=future_time,
        private=False,
        config=_cfg("99999", None),
    )

    assert "取快递" in result
    kwargs = reminder_mod._mock_tm.register_scheduled_task.call_args.kwargs
    assert kwargs["target_type"] == "user"
    assert kwargs["target_id"] == "99999"
    assert kwargs["owner_user_id"] == "99999"


@pytest.mark.asyncio
async def test_create_reminder_past_time_rejected(reminder_mod):
    """过去时间应返回错误消息，不调用 register_task。"""
    result = await reminder_mod.create_reminder(
        reminder_text="做梦",
        remind_time="2020-01-01 00:00:00",
        config=_cfg("1"),
    )

    assert "将来" in result or "错误" in result
    reminder_mod._mock_tm.register_scheduled_task.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_reminder_invalid_format(reminder_mod):
    """非法时间格式应返回格式错误消息。"""
    result = await reminder_mod.create_reminder(
        reminder_text="测试",
        remind_time="明天下午三点",
        config=_cfg("1"),
    )

    assert "格式" in result
    reminder_mod._mock_tm.register_scheduled_task.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_reminder_job_id_format(reminder_mod, future_time):
    """job_id 格式应为 reminder_{user_id}_{timestamp_ms}。"""
    before_ms = int(time.time() * 1000)
    await reminder_mod.create_reminder(
        reminder_text="喝水",
        remind_time=future_time,
        config=_cfg("42"),
    )
    after_ms = int(time.time() * 1000)

    job_id: str = reminder_mod._mock_tm.register_scheduled_task.call_args.kwargs["job_id"]
    assert job_id.startswith("scheduled_42_")
    ts = int(job_id.split("_")[-1])
    assert before_ms <= ts <= after_ms
