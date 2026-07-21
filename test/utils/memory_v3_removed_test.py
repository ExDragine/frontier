# ruff: noqa: S101

import sys
import types
from pathlib import Path

import pytest

from utils import agents


class _FakeStream:
    def __init__(self, result: dict):
        self._result = result

    async def output(self):
        return self._result


@pytest.mark.asyncio
async def test_chat_agent_does_not_import_or_append_memory_v3_context(monkeypatch, tmp_path):
    captured = {}

    class FakeMemoryManager:
        def build_context_injection(self, *_args, **_kwargs):
            return "## 长期记忆（V3）\n- preference: should not appear"

    fake_memory_v3 = types.SimpleNamespace(get_memory_manager=lambda: FakeMemoryManager())
    monkeypatch.setitem(sys.modules, "utils.memory_v3", fake_memory_v3)

    class DummyAgent:
        async def astream_events(self, payload, config=None, context=None, version=None):
            return _FakeStream(
                {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)]},
            )

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr(agents, "create_llm", lambda **_kwargs: object())
    monkeypatch.setattr(agents, "model_supports", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        agents.FrontierCognitive, "load_system_prompt", staticmethod(lambda *_args, **_kwargs: "base prompt")
    )

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.memory_subagent = {"name": "memory-agent", "description": "memory", "runnable": object()}
    frontier.earth_data_subagent = {"name": "earth-data-agent", "description": "earth", "runnable": object()}
    frontier.working_dir = str(tmp_path / "sandbox")

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="123",
        user_name="tester",
    )

    assert captured["system_prompt"] == "base prompt"


def test_memory_v3_and_dreaming_pipeline_modules_are_removed():
    repo_root = Path(__file__).resolve().parents[2]

    assert not (repo_root / "utils" / "memory_v3.py").exists()
    assert not (repo_root / "utils" / "dreaming_pipeline.py").exists()


def test_clockwork_no_longer_registers_dreaming_task():
    repo_root = Path(__file__).resolve().parents[2]
    clockwork_source = (repo_root / "plugins" / "clockwork" / "__init__.py").read_text(encoding="utf-8")

    assert "dreaming_pipeline" not in clockwork_source
    assert "build_dreaming_task_config" not in clockwork_source
    assert "delete_task" in clockwork_source
    assert "dreaming_daily_v3" in clockwork_source
