# ruff: noqa: S101, S105

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from utils.agents.dsh.agent import DSH_EMPTY_RESPONSE_RECOVERY_PROMPT, DshAgent
from utils.agents.dsh.service import DshAgentService, notification_to_progress


class FakeHarness:
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.runs = []
        self.closed = 0

    def run(self, prompt, *, session_id, on_notification):
        self.runs.append((prompt, session_id))
        on_notification(
            SimpleNamespace(
                method="session.event",
                payload={"event": {"type": "turn/start", "data": {"turn": 1}}},
            )
        )
        on_notification(
            SimpleNamespace(
                method="session.event",
                payload={"event": {"type": "tool/call", "data": {"name": "bash"}}},
            )
        )
        return SimpleNamespace(final_response="done", finish_reason="completed")

    def close(self):
        self.closed += 1


def test_cordis_uses_wsl_compatible_local_backends():
    cordis_path = Path(__file__).resolve().parents[2] / "utils" / "agents" / "dsh" / "cordis.yml"
    cordis = cordis_path.read_text(encoding="utf-8")

    assert "@deepseek-ai/dsh-bash-local" in cordis
    assert "@deepseek-ai/dsh-fs-local" in cordis
    assert "@deepseek-ai/dsh-sandbox-local" not in cordis
    assert "@deepseek-ai/dsh-sandbox-policy" not in cordis


def _configure(monkeypatch):
    from utils.agents.dsh import service

    monkeypatch.setattr(service.EnvConfig, "DSH_MODEL_PROVIDER", "deepseek-test")
    monkeypatch.setattr(service.EnvConfig, "DSH_MODEL", "deepseek-v4-flash")
    monkeypatch.setattr(service.EnvConfig, "DSH_MAX_TOKENS", 1234)
    monkeypatch.setattr(service.EnvConfig, "AGENT_JOB_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(
        service,
        "get_provider_profile",
        lambda name: {
            "type": "deepseek",
            "base_url": "https://deepseek.example",
            "api_key": "sk-test",
        },
    )


@pytest.mark.asyncio
async def test_service_reuses_runtime_per_workspace_and_streams_progress(monkeypatch, tmp_path):
    _configure(monkeypatch)
    created = []

    def factory(**kwargs):
        harness = FakeHarness(kwargs)
        created.append(harness)
        return harness

    service = DshAgentService(root_dir=tmp_path, harness_factory=factory)
    progress = []

    async def reporter(event):
        progress.append(event)

    first = await service.run(
        "first",
        workspace_key="group:1",
        session_id="session-1",
        progress_reporter=reporter,
    )
    second = await service.run(
        "second",
        workspace_key="group:1",
        session_id="session-1",
        progress_reporter=reporter,
    )

    assert first.final_response == second.final_response == "done"
    assert len(created) == 1
    assert created[0].runs == [("first", "session-1"), ("second", "session-1")]
    assert created[0].kwargs["provider"] == "deepseek-official"
    assert created[0].kwargs["model"] == "deepseek-v4-flash"
    assert created[0].kwargs["base_url"] == "https://deepseek.example"
    assert created[0].kwargs["api_key"] == "sk-test"
    assert [event.type for event in progress] == ["thinking", "tool_call", "thinking", "tool_call"]
    assert (tmp_path / "workspaces").is_dir()
    assert (tmp_path / "sessions").is_dir()

    await service.close()
    assert created[0].closed == 1


@pytest.mark.asyncio
async def test_service_uses_distinct_runtime_for_each_workspace(monkeypatch, tmp_path):
    _configure(monkeypatch)
    created = []

    def factory(**kwargs):
        harness = FakeHarness(kwargs)
        created.append(harness)
        return harness

    service = DshAgentService(root_dir=tmp_path, harness_factory=factory)
    await service.run("one", workspace_key="dm:1", session_id="s1")
    await service.run("two", workspace_key="dm:2", session_id="s2")

    assert len(created) == 2
    assert created[0].kwargs["cwd"] != created[1].kwargs["cwd"]
    await service.close()


@pytest.mark.asyncio
async def test_service_evicts_oldest_workspace_runtime(monkeypatch, tmp_path):
    _configure(monkeypatch)
    created = []

    def factory(**kwargs):
        harness = FakeHarness(kwargs)
        created.append(harness)
        return harness

    service = DshAgentService(root_dir=tmp_path, harness_factory=factory, max_runtimes=1)
    await service.run("one", workspace_key="dm:1", session_id="s1")
    await service.run("two", workspace_key="dm:2", session_id="s2")

    assert len(created) == 2
    assert created[0].closed == 1
    await service.close()


@pytest.mark.asyncio
async def test_service_cleanup_removes_inactive_workspace_and_session(monkeypatch, tmp_path):
    _configure(monkeypatch)
    created = []

    def factory(**kwargs):
        harness = FakeHarness(kwargs)
        created.append(harness)
        return harness

    service = DshAgentService(root_dir=tmp_path, harness_factory=factory)
    await service.run("one", workspace_key="dm:1", session_id="s1")
    scope_id = service._scope_id("dm:1")
    workspace = tmp_path / "workspaces" / scope_id
    sessions = tmp_path / "sessions" / scope_id
    (workspace / "artifact.txt").write_text("data", encoding="utf-8")
    (sessions / "session.jsonl").write_text("{}", encoding="utf-8")

    cleaned = await service.cleanup_cache()

    assert cleaned == 1
    assert created[0].closed == 1
    assert not workspace.exists()
    assert not sessions.exists()
    assert service._runtimes == {}


@pytest.mark.asyncio
async def test_service_cleanup_skips_active_scope(monkeypatch, tmp_path):
    _configure(monkeypatch)
    started = threading.Event()
    released = threading.Event()

    class BlockingHarness(FakeHarness):
        def run(self, *_args, **_kwargs):
            started.set()
            released.wait(timeout=2)
            return SimpleNamespace(final_response="done", finish_reason="completed")

    created = []

    def factory(**kwargs):
        harness = BlockingHarness(kwargs)
        created.append(harness)
        return harness

    service = DshAgentService(root_dir=tmp_path, harness_factory=factory)
    run_task = asyncio.create_task(service.run("slow", workspace_key="dm:1", session_id="s1"))
    assert await asyncio.to_thread(started.wait, 1)
    scope_id = service._scope_id("dm:1")
    workspace = tmp_path / "workspaces" / scope_id

    assert await service.cleanup_cache() == 0
    assert workspace.is_dir()
    assert created[0].closed == 0

    released.set()
    await run_task
    assert await service.cleanup_cache() == 1
    assert not workspace.exists()


@pytest.mark.asyncio
async def test_service_timeout_closes_and_discards_runtime(monkeypatch, tmp_path):
    _configure(monkeypatch)
    from utils.agents.dsh import service as service_module

    monkeypatch.setattr(service_module.EnvConfig, "AGENT_JOB_TIMEOUT_SECONDS", 0.01)
    released = threading.Event()

    class BlockingHarness(FakeHarness):
        def run(self, *_args, **_kwargs):
            released.wait(timeout=1)
            return SimpleNamespace(final_response="late", finish_reason="completed")

        def close(self):
            super().close()
            released.set()

    created = []

    def factory(**kwargs):
        harness = BlockingHarness(kwargs)
        created.append(harness)
        return harness

    service = DshAgentService(root_dir=tmp_path, harness_factory=factory)

    with pytest.raises(TimeoutError, match="DSH 执行超过"):
        await service.run("slow", workspace_key="dm:1", session_id="s1")

    assert created[0].closed == 1
    assert service._runtimes == {}


def test_notification_to_progress_handles_subagents_and_unknown_events():
    started = notification_to_progress(
        {"method": "subagent.started", "payload": {"childSessionId": "child"}}
    )
    finished = notification_to_progress(
        {"method": "subagent.finished", "payload": {"childSessionId": "child", "status": "ok"}}
    )

    assert started is not None and started.type == "subagent_start"
    assert finished is not None and finished.type == "subagent_done"
    assert notification_to_progress({"method": "session.status", "payload": {}}) is None


@pytest.mark.asyncio
async def test_dsh_agent_adapts_successful_result():
    class FakeService:
        async def run(self, *_args, **_kwargs):
            return SimpleNamespace(final_response="answer", finish_reason="completed")

    result = await DshAgent(FakeService()).chat_agent(
        "task",
        workspace_key="dm:1",
        session_id="session-1",
    )

    assert result["response"]["messages"][0].content == "answer"
    assert result["uni_messages"] == []
    assert "error" not in result


@pytest.mark.asyncio
async def test_dsh_agent_recovers_completed_empty_response():
    class FakeService:
        def __init__(self):
            self.prompts = []

        async def run(self, prompt, *_args, **_kwargs):
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                return SimpleNamespace(
                    final_response="",
                    finish_reason="completed",
                    events=[{"type": "turn/end"}],
                    notifications=[],
                )
            return SimpleNamespace(final_response="recovered", finish_reason="completed")

    service = FakeService()
    result = await DshAgent(service).chat_agent(
        "task",
        workspace_key="dm:1",
        session_id="session-1",
    )

    assert service.prompts == ["task", DSH_EMPTY_RESPONSE_RECOVERY_PROMPT]
    assert result["response"]["messages"][0].content == "recovered"
    assert "error" not in result


@pytest.mark.asyncio
async def test_dsh_agent_reports_empty_response_after_recovery():
    class FakeService:
        async def run(self, *_args, **_kwargs):
            return SimpleNamespace(final_response="", finish_reason="completed", events=[], notifications=[])

    result = await DshAgent(FakeService()).chat_agent(
        "task",
        workspace_key="dm:1",
        session_id="session-1",
    )

    assert "没有生成文本回复" in result["response"]["messages"][0].content
    assert "finish_reason=completed" in result["error"]
