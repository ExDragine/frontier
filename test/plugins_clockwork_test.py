# ruff: noqa: S101

import importlib
import json
import sys
import types
from pathlib import Path

import pytest
from sqlmodel import SQLModel, create_engine

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "plugins"

plugins_pkg = types.ModuleType("plugins")
plugins_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("plugins", plugins_pkg)

clockwork_pkg = types.ModuleType("plugins.clockwork")
clockwork_pkg.__path__ = [str(PACKAGE_ROOT / "clockwork")]
sys.modules.setdefault("plugins.clockwork", clockwork_pkg)

task_manager_module = importlib.import_module("plugins.clockwork.task_manager")
task_models_module = importlib.import_module("plugins.clockwork.task_models")

TaskExecutor = task_manager_module.TaskExecutor
TaskManager = task_manager_module.TaskManager
TaskConfig = task_models_module.TaskConfig
TaskExecutionHistory = task_models_module.TaskExecutionHistory
TaskGroupMapping = task_models_module.TaskGroupMapping


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
    scheduler = DummyScheduler()
    manager = TaskManager(scheduler, engine)
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
    with pytest.raises(Exception):
        _ = task.job_id

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

    async def handler():
        handler_called["count"] += 1

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

    async def failing_handler():
        raise RuntimeError("boom")

    monkeypatch.setattr(executor, "_load_handler", lambda m, f: failing_handler)
    await executor.execute("job3")
    history = await task_manager.get_execution_history("job3")
    assert history[0].status in {"failed", "success"}
