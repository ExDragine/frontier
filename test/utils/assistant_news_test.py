# ruff: noqa: S101

import types

import pytest

from utils.agents import assistant as assistant_mod


@pytest.mark.asyncio
async def test_assistant_agent_respects_explicit_route_and_preserves_tool_results(monkeypatch):
    captured = {}
    result = {"messages": [types.SimpleNamespace(type="tool", content="evidence")]}
    invocation = {"configurable": {"workspace_dir": "/news"}}

    class DummyAgent:
        async def ainvoke(self, request, *, config):
            assert request["messages"][0]["content"] == "research"
            assert config == invocation
            return result

    def create_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(assistant_mod, "create_llm", create_model)
    monkeypatch.setattr(assistant_mod, "create_agent", lambda **kwargs: DummyAgent())

    returned = await assistant_mod.assistant_agent(
        user_prompt="research", use_model="news-model", model_role="daily_news",
        model_provider="news-provider", model_timeout=45,
        model_extra_body={"thinking": {"type": "disabled"}},
        invoke_config=invocation, return_result=True,
    )

    assert returned is result
    assert captured["provider"] == "news-provider"
    assert captured["timeout"] == 45
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}


