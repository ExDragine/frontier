# ruff: noqa: S101

import types
from typing import Any, cast

from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

from utils.agents.subagents import document, memory, research


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


def test_build_research_subagent_is_bounded_and_uses_only_injected_tools(monkeypatch):
    captured = {}
    research_tools = [types.SimpleNamespace(name="web_search_exa"), types.SimpleNamespace(name="web_fetch_exa")]
    runnable = object()

    def fake_create_llm(**kwargs):
        captured["model_kwargs"] = kwargs
        return "basic-llm"

    monkeypatch.setattr(research, "create_llm", fake_create_llm)

    def fake_create_agent(**kwargs):
        captured["agent_kwargs"] = kwargs
        return runnable

    monkeypatch.setattr(research, "create_agent", fake_create_agent)

    subagent = research.build_research_subagent(research_tools)

    assert captured["model_kwargs"]["model"] == research.EnvConfig.BASIC_MODEL
    assert captured["agent_kwargs"]["model"] == "basic-llm"
    assert captured["agent_kwargs"]["tools"] == research_tools
    assert "429" in captured["agent_kwargs"]["system_prompt"]
    middleware = captured["agent_kwargs"]["middleware"]
    assert [type(item).__name__ for item in middleware] == [
        "ToolRetryMiddleware",
        "ToolCallLimitMiddleware",
        "ModelCallLimitMiddleware",
        "ModelRetryMiddleware",
    ]
    assert middleware[1].run_limit == 6
    assert middleware[2].run_limit == 5
    assert subagent["name"] == "research-agent"
    assert subagent["runnable"] is runnable


def test_research_rate_limit_stops_retrying():
    message = research._tool_failure_message(RuntimeError("429 Too Many Requests"))

    assert "停止继续搜索" in message
    assert "可能不完整" in message


def test_research_quota_error_stops_switching_backends():
    message = research._tool_failure_message(RuntimeError("Tavily usage limit exceeded"))

    assert "停止继续搜索" in message


def test_build_document_subagent_is_read_only_and_bounded(monkeypatch):
    captured = {}

    def fake_create_llm(**kwargs):
        captured["model_kwargs"] = kwargs
        return "basic-llm"

    monkeypatch.setattr(document, "create_llm", fake_create_llm)

    subagent = document.build_document_subagent()

    assert captured["model_kwargs"]["model"] == document.EnvConfig.BASIC_MODEL
    assert subagent["name"] == "document-agent"
    assert subagent["model"] == "basic-llm"
    assert subagent["tools"] == []
    assert [type(item).__name__ for item in subagent["middleware"]] == [
        "ToolCallLimitMiddleware",
        "ModelCallLimitMiddleware",
    ]
    middleware = cast(list[Any], subagent["middleware"])
    assert middleware[0].run_limit == 8
    assert middleware[1].run_limit == 6
    permission = subagent["permissions"][0]
    assert permission.operations == ["write"]
    assert permission.paths == ["/**"]
    assert permission.mode == "deny"
