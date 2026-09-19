# ruff: noqa: S101

import asyncio
import importlib
import sys
import types
from pathlib import Path
from typing import cast

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import create_engine

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "plugins"

plugins_pkg = types.ModuleType("plugins")
plugins_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("plugins", plugins_pkg)

clockwork_pkg = types.ModuleType("plugins.clockwork")
clockwork_pkg.__path__ = [str(PACKAGE_ROOT / "clockwork")]
sys.modules.setdefault("plugins.clockwork", clockwork_pkg)

task_manager_module = importlib.import_module("plugins.clockwork.task_manager")
task_models_module = importlib.import_module("plugins.clockwork.task_models")
agent_task_handler_module = importlib.import_module("plugins.clockwork.agent_task_handler")

TaskExecutor = task_manager_module.TaskExecutor
TaskManager = task_manager_module.TaskManager
TaskConfig = task_models_module.TaskConfig
TaskExecutionHistory = task_models_module.TaskExecutionHistory
TaskGroupMapping = task_models_module.TaskGroupMapping
ScheduledTaskMetadata = task_models_module.ScheduledTaskMetadata
TaskRunResult = task_models_module.TaskRunResult


def test_task_schema_rejects_missing_output_summary(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old-tasks.db'}")
    TaskExecutionHistory.__table__.create(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER TABLE taskexecutionhistory DROP COLUMN output_summary")
    manager = TaskManager(DummyScheduler(), engine)
    with pytest.raises(RuntimeError, match="缺少列 output_summary"):
        manager.ensure_schema()
    with engine.connect() as conn:
        columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(taskexecutionhistory)")}
    assert "output_summary" not in columns


def test_cenc_is_not_a_clockwork_task_anymore():
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")

    assert "eq_cenc" not in TaskManager.JOB_ID_TO_CONFIG_KEY
    assert not hasattr(task_handlers_module, "eq_cenc")


class DummyScheduler:
    def __init__(self):
        self.jobs = {}
        self.listeners = []

    def add_listener(self, func, *_args, **_kwargs):
        self.listeners.append(func)

    def add_job(self, func, trigger, id, args, misfire_grace_time, replace_existing, **trigger_args):
        self.jobs[id] = {
            "func": func,
            "trigger": trigger,
            "args": args,
            "misfire_grace_time": misfire_grace_time,
            "trigger_args": trigger_args,
        }

    def pause_job(self, job_id):
        self.jobs[job_id]["paused"] = True

    def resume_job(self, job_id):
        if job_id not in self.jobs:
            raise RuntimeError("missing job")
        self.jobs[job_id]["paused"] = False

    def reschedule_job(self, job_id, trigger, **trigger_args):
        if job_id not in self.jobs:
            raise RuntimeError("missing job")
        self.jobs[job_id]["trigger"] = trigger
        self.jobs[job_id]["trigger_args"] = trigger_args

    def remove_job(self, job_id):
        self.jobs.pop(job_id, None)

    def get_job(self, job_id):
        return types.SimpleNamespace(next_run_time=None)


@pytest.fixture
def task_manager(tmp_path):
    engine = create_engine("sqlite://")
    TaskConfig.metadata.create_all(engine)
    TaskGroupMapping.metadata.create_all(engine)
    TaskExecutionHistory.metadata.create_all(engine)
    ScheduledTaskMetadata.metadata.create_all(engine)
    scheduler = DummyScheduler()
    manager = TaskManager(cast(AsyncIOScheduler, scheduler), engine)
    manager.set_job_func(lambda job_id: None)
    return manager


@pytest.mark.asyncio
async def test_register_and_update_task(task_manager):
    task = await task_manager.register_task(
        job_id="job1",
        name="Task",
        handler_module="module",
        handler_function="func",
        trigger_type="interval",
        trigger_args={"minutes": 5},
        group_ids=[1, 1, 2],
    )
    assert task.job_id == "job1"
    assert "job1" in task_manager.scheduler.jobs

    duplicate = await task_manager.register_task(
        job_id="job1",
        name="Task",
        handler_module="module",
        handler_function="func",
        trigger_type="interval",
        trigger_args={"minutes": 5},
        group_ids=[1],
    )
    assert duplicate.job_id == "job1"

    assert await task_manager.update_task_trigger("job1", "cron", {"hour": "1"}) in {True, False}

    assert await task_manager.update_task_groups("job1", [3, 3]) in {True, False}
    groups = await task_manager.get_task_groups("job1")
    assert groups == [3]


@pytest.mark.asyncio
async def test_register_scheduled_task_metadata_and_permissions(task_manager):
    await task_manager.register_scheduled_task(
        job_id="scheduled_1",
        name="Auto",
        prompt="Say hi",
        trigger_type="interval",
        trigger_args={"minutes": 5},
        owner_user_id="123",
        target_type="group",
        target_id="456",
    )

    metadata = await task_manager.get_task_metadata("scheduled_1")
    assert metadata is not None
    assert metadata.owner_user_id == "123"
    assert metadata.target_type == "group"
    assert metadata.target_id == "456"
    assert await task_manager.user_can_manage_task("scheduled_1", "123")
    assert not await task_manager.user_can_manage_task("scheduled_1", "999")


@pytest.mark.asyncio
async def test_log_execution_updates_stats(task_manager):
    await task_manager.register_task(
        job_id="job2",
        name="Task",
        handler_module="module",
        handler_function="func",
        trigger_type="interval",
        trigger_args={"minutes": 1},
        group_ids=[],
    )
    await task_manager.log_execution(job_id="job2", status="success", execution_time=123)
    stats = await task_manager.get_task_statistics("job2")
    assert stats["success_runs"] == 1


@pytest.mark.asyncio
async def test_task_executor_execute_paths(monkeypatch, task_manager):
    handler_called = {"count": 0}

    async def handler(**kwargs):
        handler_called["count"] += 1
        return TaskRunResult(groups_sent=[9], messages_sent=2, output_summary="ok")

    await task_manager.register_task(
        job_id="job3",
        name="Task",
        handler_module="module",
        handler_function="func",
        trigger_type="interval",
        trigger_args={"minutes": 1},
        group_ids=[],
    )

    executor = TaskExecutor(task_manager)

    monkeypatch.setattr(executor, "_load_handler", lambda m, f: handler)
    await executor.execute("job3")
    assert handler_called["count"] == 1
    stats = await task_manager.get_task_statistics("job3")
    assert stats["recent_history"][0]["output_summary"] == "ok"

    async def failing_handler(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(executor, "_load_handler", lambda m, f: failing_handler)
    await executor.execute("job3")
    history = await task_manager.get_execution_history("job3")
    assert history[0].status in {"failed", "success"}
    failed_history = [record for record in history if record.status == "failed"]
    assert failed_history
    assert "RuntimeError: boom" in (failed_history[0].error_traceback or "")


@pytest.mark.asyncio
async def test_date_scheduled_task_archives_after_success(monkeypatch, task_manager):
    async def handler(**kwargs):
        return TaskRunResult(messages_sent=1, output_summary="done")

    await task_manager.register_scheduled_task(
        job_id="scheduled_date",
        name="One shot",
        prompt="Do once",
        trigger_type="date",
        trigger_args={"run_date": "2099-01-01T00:00:00+08:00"},
        owner_user_id="1",
        target_type="user",
        target_id="1",
    )

    executor = TaskExecutor(task_manager)
    monkeypatch.setattr(executor, "_load_handler", lambda m, f: handler)
    await executor.execute("scheduled_date")

    metadata = await task_manager.get_task_metadata("scheduled_date")
    task = await task_manager.get_task("scheduled_date")
    assert metadata is not None and metadata.archived is True
    assert task is not None and task.enabled is False
    assert "scheduled_date" not in task_manager.scheduler.jobs


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["failed", "timeout"])
async def test_agent_failure_is_not_delivered_or_archived(monkeypatch, task_manager, failure):
    await task_manager.register_scheduled_task(
        job_id="failed_date", name="One shot", prompt="Do once", trigger_type="date",
        trigger_args={"run_date": "2099-01-01T00:00:00+08:00"},
        owner_user_id="1", target_type="user", target_id="1",
    )

    class FailingCognitive:
        async def chat_agent(self, *_args, **_kwargs):
            return {"error": "ModelTimeoutError", "status": failure,
                    "response": {"messages": [types.SimpleNamespace(text="请求超时")]}}

    async def unexpected_delivery(*_args):
        pytest.fail("An unsuccessful task must not deliver a success response")

    monkeypatch.setattr(clockwork_pkg, "task_manager", task_manager, raising=False)
    monkeypatch.setattr(agent_task_handler_module, "FrontierCognitive", FailingCognitive)
    monkeypatch.setattr(agent_task_handler_module, "_send_final_text", unexpected_delivery)
    executor = TaskExecutor(task_manager)
    monkeypatch.setattr(executor, "_load_handler", lambda *_args: agent_task_handler_module.run_agent_task)
    await executor.execute("failed_date")
    metadata = await task_manager.get_task_metadata("failed_date")
    assert metadata is not None and not metadata.archived
    history = await task_manager.get_execution_history("failed_date")
    assert history[0].status == failure
    assert history[0].messages_sent == 0


@pytest.mark.asyncio
async def test_cancelled_task_is_recorded_and_cancellation_propagates(monkeypatch, task_manager):
    await task_manager.register_task(
        job_id="cancelled", name="Cancelable", handler_module="module", handler_function="func",
        trigger_type="interval", trigger_args={"minutes": 1}, group_ids=[],
    )

    async def cancelled(**kwargs):
        raise asyncio.CancelledError

    executor = TaskExecutor(task_manager)
    monkeypatch.setattr(executor, "_load_handler", lambda *_args: cancelled)
    with pytest.raises(asyncio.CancelledError):
        await executor.execute("cancelled")
    history = await task_manager.get_execution_history("cancelled")
    assert history[0].status == "cancelled"


def test_daily_news_legacy_handler_is_a_compatibility_wrapper():
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")

    assert callable(task_handlers_module.daily_news)


@pytest.mark.asyncio
async def test_clockwork_daily_news_delegates_to_news_plugin(monkeypatch):
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")
    scheduler_module = importlib.import_module("plugins.news.scheduler")
    expected = TaskRunResult(groups_sent=[202], messages_sent=1, output_summary="news ready")

    async def fake_news(**kwargs):
        assert kwargs == {"job_id": "daily_news"}
        return expected

    monkeypatch.setattr(scheduler_module, "daily_news", fake_news)

    result = await task_handlers_module.daily_news(job_id="daily_news")

    assert result is expected


@pytest.mark.asyncio
async def test_agent_task_final_group_delivery_mentions_owner(monkeypatch):
    calls = []
    agent_calls = []
    metadata = types.SimpleNamespace(
        target_type="group",
        target_id="123",
        owner_user_id="456",
        prompt="提醒我喝水",
        archived=False,
        delivery_mode="final",
    )

    class DummyTaskManager:
        async def get_task_metadata(self, job_id):
            assert job_id == "scheduled_1"
            return metadata

    class DummyCognitive:
        async def chat_agent(self, *_args, **kwargs):
            agent_calls.append(kwargs)
            return {
                "uni_messages": [],
                "response": {"messages": [types.SimpleNamespace(text="该喝水了")]},
            }

    class DummyBot:
        async def send_group_message(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(message_seq=77)

    monkeypatch.setattr(clockwork_pkg, "task_manager", DummyTaskManager(), raising=False)
    monkeypatch.setattr(agent_task_handler_module, "FrontierCognitive", lambda: DummyCognitive())
    monkeypatch.setattr(agent_task_handler_module, "get_bot", lambda: DummyBot(), raising=False)

    result = await agent_task_handler_module.run_agent_task("scheduled_1")

    assert result.messages_sent == 1
    assert result.groups_sent == [123]
    assert len(calls) == 1
    assert calls[0]["group_id"] == 123
    assert [segment.type for segment in calls[0]["message"]] == ["mention", "text"]
    assert calls[0]["message"][0].data == {"user_id": 456}
    assert calls[0]["message"][1].data == {"text": " 该喝水了"}
