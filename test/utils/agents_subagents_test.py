# ruff: noqa: S101

from typing import Any, cast

from utils.agents.subagents import document
from utils.agents.tool_errors import read_only_error_message


def test_search_rate_limit_stops_retrying():
    message = read_only_error_message(RuntimeError("429 Too Many Requests"))

    assert "停止继续搜索" in message
    assert "可能不完整" in message


def test_search_quota_error_stops_switching_backends():
    message = read_only_error_message(RuntimeError("Tavily usage limit exceeded"))

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
        "ToolErrorMiddleware",
        "ToolCallLimitMiddleware",
        "ModelCallLimitMiddleware",
    ]
    middleware = cast(list[Any], subagent["middleware"])
    assert middleware[1].run_limit == 8
    assert middleware[2].run_limit == 6
    permission = subagent["permissions"][0]
    assert permission.operations == ["write"]
    assert permission.paths == ["/**"]
    assert permission.mode == "deny"
