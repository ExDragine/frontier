# ruff: noqa: S101

import types

from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

from utils.subagents import earth_data, memory


def test_build_memory_subagent_uses_basic_model_and_only_injected_tools(monkeypatch):
    captured = {}
    memory_tools = [types.SimpleNamespace(name="search_messages"), types.SimpleNamespace(name="get_history_messages")]
    runnable = object()

    def fake_create_llm(**kwargs):
        captured["model_kwargs"] = kwargs
        return "basic-llm"

    def fake_create_agent(**kwargs):
        captured["agent_kwargs"] = kwargs
        return runnable

    monkeypatch.setattr(memory.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(memory.EnvConfig, "BASIC_MODEL_PROVIDER", "basic-provider")
    monkeypatch.setattr(memory.EnvConfig, "AGENT_DEBUG_MODE", True)
    monkeypatch.setattr(memory, "create_llm", fake_create_llm)
    monkeypatch.setattr(memory, "create_agent", fake_create_agent)

    subagent = memory.build_memory_subagent(memory_tools)

    assert captured["model_kwargs"] == {
        "model": "basic-model",
        "provider": "basic-provider",
        "streaming": False,
        "max_retries": 2,
        "timeout": 300,
    }
    assert captured["agent_kwargs"]["model"] == "basic-llm"
    assert captured["agent_kwargs"]["tools"] == memory_tools
    assert "最多读取 1000 条记录" in captured["agent_kwargs"]["system_prompt"]
    assert "只返回最终结论" in captured["agent_kwargs"]["system_prompt"]
    assert [type(item) for item in captured["agent_kwargs"]["middleware"]] == [
        ToolRetryMiddleware,
        ModelRetryMiddleware,
    ]
    assert subagent["name"] == "memory-agent"
    assert subagent["runnable"] is runnable
    assert "检索" in subagent["description"]


def test_build_earth_data_subagent_uses_basic_model_and_only_injected_tools(monkeypatch):
    captured = {}
    earth_tools = [types.SimpleNamespace(name="get_china_earthquake")]
    runnable = object()

    def fake_create_llm(**kwargs):
        captured["model_kwargs"] = kwargs
        return "basic-llm"

    def fake_create_agent(**kwargs):
        captured["agent_kwargs"] = kwargs
        return runnable

    monkeypatch.setattr(earth_data.EnvConfig, "BASIC_MODEL", "basic-model")
    monkeypatch.setattr(earth_data.EnvConfig, "BASIC_MODEL_PROVIDER", "basic-provider")
    monkeypatch.setattr(earth_data.EnvConfig, "AGENT_DEBUG_MODE", True)
    monkeypatch.setattr(earth_data, "create_llm", fake_create_llm)
    monkeypatch.setattr(earth_data, "create_agent", fake_create_agent)

    subagent = earth_data.build_earth_data_subagent(earth_tools)

    assert captured["model_kwargs"] == {
        "model": "basic-model",
        "provider": "basic-provider",
        "streaming": False,
        "max_retries": 2,
        "timeout": 300,
    }
    assert captured["agent_kwargs"]["model"] == "basic-llm"
    assert captured["agent_kwargs"]["tools"] == earth_tools
    assert "不得凭记忆编造" in captured["agent_kwargs"]["system_prompt"]
    assert "只返回最终结论" in captured["agent_kwargs"]["system_prompt"]
    assert [type(item) for item in captured["agent_kwargs"]["middleware"]] == [
        ToolRetryMiddleware,
        ModelRetryMiddleware,
    ]
    assert subagent["name"] == "earth-data-agent"
    assert subagent["runnable"] is runnable
    assert "雷达图" in subagent["description"]
