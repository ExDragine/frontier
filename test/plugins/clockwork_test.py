# ruff: noqa: S101

import datetime
import importlib
import json
import sys
import types
from pathlib import Path

import pytest
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
async def test_migrate_legacy_reminder(task_manager):
    await task_manager.register_task(
        job_id="reminder_42_1",
        name="提醒: 喝水",
        handler_module="plugins.clockwork.reminder_handler",
        handler_function="fire_reminder",
        trigger_type="date",
        trigger_args={"run_date": "2099-01-01T00:00:00+08:00"},
        group_ids=[100],
        description=json.dumps({"text": "喝水", "user_id": "42", "group_id": 100, "private": False}),
    )

    migrated = await task_manager.migrate_legacy_reminders()
    task = await task_manager.get_task("reminder_42_1")
    metadata = await task_manager.get_task_metadata("reminder_42_1")
    assert migrated == 1
    assert task is not None
    assert task.handler_module == "plugins.clockwork.agent_task_handler"
    assert metadata is not None
    assert metadata.owner_user_id == "42"
    assert metadata.target_type == "group"


@pytest.mark.asyncio
async def test_daily_news_uses_general_news_tools_and_custom_layout(monkeypatch):
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")
    captured = {}
    calls = []
    sent_targets = []

    async def fake_assistant_agent(system_prompt, user_prompt, **kwargs):
        calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt, "kwargs": kwargs})
        if len(calls) == 1:
            return "今日要闻候选：\n- 标题：要闻标题\n  要点：要闻摘要\n  影响：后续影响\n  来源：新华社"
        return task_handlers_module.DailyNewsPayload(
            top_stories=[
                task_handlers_module.TopStory(
                    title="要闻标题",
                    summary="要闻摘要",
                    impact="后续影响",
                    sources=["新华社"],
                )
            ],
            worth_reading=[
                task_handlers_module.WorthReadingStory(
                    category="科技",
                    title="更多标题",
                    summary="更多内容",
                    sources=["路透"],
                )
            ],
        )

    async def fake_html_to_image(summary, **kwargs):
        captured["rendered_summary"] = summary
        captured["render_kwargs"] = kwargs
        return b"news-image"

    class DummyTarget:
        @staticmethod
        def group(group_id):
            return f"group:{group_id}"

    class DummyUniMessage:
        def image(self, *, raw):
            captured["image_raw"] = raw
            return self

        async def send(self, *, target):
            sent_targets.append(target)

    async def fail_if_http_get_called(*_args, **_kwargs):
        raise AssertionError("daily_news should not fetch a fixed news API")

    monkeypatch.setattr(task_handlers_module, "assistant_agent", fake_assistant_agent)
    monkeypatch.setattr(task_handlers_module, "html_to_image", fake_html_to_image)
    monkeypatch.setattr(task_handlers_module, "Target", DummyTarget)
    monkeypatch.setattr(task_handlers_module, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(task_handlers_module.httpx_client, "get", fail_if_http_get_called)
    monkeypatch.setattr(task_handlers_module.EnvConfig, "NEWS_SUMMARY_GROUP_ID", [101, 202])
    monkeypatch.setattr(task_handlers_module, "tools", ["web-search-tool"])
    monkeypatch.setattr(task_handlers_module, "load_daily_news_css", lambda: ".news-hero {} .impact {} .watch-card {}")

    result = await task_handlers_module.daily_news()

    assert len(calls) == 2
    assert not hasattr(task_handlers_module, "markdown_to_image")
    fixed_api_constant = "SPACEFLIGHT" + "_NEWS_URL"
    narrow_topic = "航天" + "新闻"
    assert not hasattr(task_handlers_module, fixed_api_constant)
    assert "全球与中国主要新闻" in calls[0]["user_prompt"]
    assert "最近24小时" in calls[0]["user_prompt"]
    assert "纯文本素材包" in calls[0]["system_prompt"]
    assert "不要输出 HTML" in calls[0]["system_prompt"]
    assert narrow_topic not in calls[0]["user_prompt"]
    assert narrow_topic not in calls[0]["system_prompt"]
    assert calls[0]["kwargs"]["use_model"] == task_handlers_module.EnvConfig.ADVAN_MODEL
    assert calls[0]["kwargs"]["tools"] == ["web-search-tool"]
    assert "response_format" not in calls[0]["kwargs"]
    assert "今日要闻候选" in calls[1]["user_prompt"]
    assert "整理成严格 JSON" in calls[1]["system_prompt"]
    assert calls[1]["kwargs"]["use_model"] == task_handlers_module.EnvConfig.SIGNAL_MODEL
    assert calls[1]["kwargs"]["tools"] is None
    assert calls[1]["kwargs"]["response_format"] is task_handlers_module.DailyNewsPayload
    assert captured["rendered_summary"].startswith("<main class=\"news-page\">")
    assert "要闻标题" in captured["rendered_summary"]
    assert "更多标题" in captured["rendered_summary"]
    assert "css" in captured["render_kwargs"]
    assert ".news-hero" in captured["render_kwargs"]["css"]
    assert ".impact" in captured["render_kwargs"]["css"]
    assert ".watch-card" in captured["render_kwargs"]["css"]
    assert captured["image_raw"] == b"news-image"
    assert sent_targets == ["group:101", "group:202"]
    assert result.groups_sent == [101, 202]
    assert result.messages_sent == 2


def test_daily_news_tools_only_expose_search_tools():
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")
    selected_tools = task_handlers_module._daily_news_tools(
        [
            types.SimpleNamespace(name="web_search_exa"),
            types.SimpleNamespace(name="web_fetch_exa"),
        ]
    )

    assert {tool.name for tool in selected_tools} == {"web_search_exa"}


@pytest.mark.asyncio
async def test_daily_news_continues_when_one_group_send_fails(monkeypatch):
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")
    sent_targets = []

    class DummyTarget:
        @staticmethod
        def group(group_id):
            return f"group:{group_id}"

    class DummyUniMessage:
        def image(self, *, raw):
            return self

        async def send(self, *, target):
            if target == "group:101":
                raise RuntimeError("send failed")
            sent_targets.append(target)

    async def fake_build_daily_news_artifacts():
        return task_handlers_module.DailyNewsArtifacts(
            today="2026年05月21日",
            period="晚报",
            report_time="18:30",
            material="素材",
            payload=task_handlers_module.DailyNewsPayload(top_stories=[], worth_reading=[]),
            html="<main class=\"news-page\"></main>",
        )

    async def fake_html_to_image(summary, **kwargs):
        return b"news-image"

    monkeypatch.setattr(task_handlers_module, "build_daily_news_artifacts", fake_build_daily_news_artifacts)
    monkeypatch.setattr(task_handlers_module, "html_to_image", fake_html_to_image)
    monkeypatch.setattr(task_handlers_module, "Target", DummyTarget)
    monkeypatch.setattr(task_handlers_module, "UniMessage", DummyUniMessage)
    monkeypatch.setattr(task_handlers_module.EnvConfig, "NEWS_SUMMARY_GROUP_ID", [101, 202])
    monkeypatch.setattr(task_handlers_module, "load_daily_news_css", lambda: "")

    result = await task_handlers_module.daily_news()

    assert sent_targets == ["group:202"]
    assert result.groups_sent == [202]
    assert result.messages_sent == 1


@pytest.mark.asyncio
async def test_build_daily_news_artifacts_returns_material_payload_and_html(monkeypatch):
    task_handlers_module = importlib.import_module("plugins.clockwork.task_handlers")
    calls = []

    async def fake_assistant_agent(system_prompt, user_prompt, **kwargs):
        calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt, "kwargs": kwargs})
        if len(calls) == 1:
            return "今日要闻候选：\n- 标题：要闻标题\n  要点：要闻摘要\n  影响：后续影响\n  来源：新华社"
        return task_handlers_module.DailyNewsPayload(
            top_stories=[
                task_handlers_module.TopStory(
                    title="要闻标题",
                    summary="要闻摘要",
                    impact="后续影响",
                    sources=["新华社"],
                )
            ],
            worth_reading=[],
        )

    monkeypatch.setattr(task_handlers_module, "assistant_agent", fake_assistant_agent)
    monkeypatch.setattr(task_handlers_module, "tools", ["web-search-tool"])

    artifacts = await task_handlers_module.build_daily_news_artifacts(
        now_cn=datetime.datetime(2026, 5, 21, 9, 30, tzinfo=datetime.UTC)
    )

    assert artifacts is not None
    assert artifacts.today == "2026年05月21日"
    assert artifacts.period == "早报"
    assert artifacts.report_time == "17:30"
    assert "今日要闻候选" in artifacts.material
    assert artifacts.payload.top_stories[0].title == "要闻标题"
    assert "<main class=\"news-page\">" in artifacts.html
    assert len(calls) == 2


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
