# ruff: noqa: S101
"""Plugin-owned resources resolve independently of the process working directory."""

import pytest


@pytest.mark.asyncio
async def test_toolbox_loads_and_caches_its_menu_from_another_directory(monkeypatch, tmp_path):
    from plugins.toolbox import menu

    calls = []

    async def render(html, **kwargs):
        calls.append((html, kwargs))
        return b"rendered-menu"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(menu, "_vep_menu_cache", None)
    monkeypatch.setattr(menu, "html_to_image", render)
    assert await menu._get_vep_menu() == b"rendered-menu"
    assert await menu._get_vep_menu() == b"rendered-menu"
    assert len(calls) == 1
    assert "<" in calls[0][0]
    assert calls[0][1]["css"]
    assert calls[0][1]["width"] == 480


def test_clockwork_daily_news_is_a_compatibility_wrapper():
    from plugins.clockwork import task_handlers

    assert callable(task_handlers.daily_news)


@pytest.mark.asyncio
async def test_agent_reads_its_reply_prompt_from_another_directory(monkeypatch, tmp_path):
    from plugins.agent import gateway

    class History:
        async def count_group_messages_since(self, **kwargs):
            return 0

        async def latest_group_role_message_time(self, **kwargs):
            return None

    async def decide(self, messages, questions):
        from utils.decision import DecisionResult

        assert questions["should_reply"]["instructions"]
        assert "帮我" in messages
        return DecisionResult(answers={"should_reply": {"type": "predicate", "probability": 1.0}}, provider="test", latency_ms=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(gateway, "messages_db", History())
    monkeypatch.setattr(gateway.LLMDecisionProvider, "decide", decide)
    monkeypatch.setattr(gateway, "_reply_check_last_checked_at", {})
    assert await gateway._reply_check_should_reply(123, "帮我解释这条报错", [{"content": "帮我解释这条报错"}])
