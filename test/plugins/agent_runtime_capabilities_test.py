# ruff: noqa: S101
"""Verify the production QQ handler declares the neutral platform boundary."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from utils.agent_protocol import ConversationRef, Participant


def _context(agent):
    return agent.AgentRequestContext(
        event=cast(Any, SimpleNamespace(self_id="bot-1")),
        user_id="user-1",
        user_name="Alice",
        event_id=10,
        group_id=42,
        msg_time=100,
        text="hello",
        quoted_images=[],
        images=[],
        videos=[],
    )


@pytest.mark.asyncio
async def test_qq_handler_passes_neutral_identity_and_capabilities(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins.agent import handlers as agent

    captured = {}

    class Runtime:
        def __init__(self, cognitive):
            captured["cognitive"] = cognitive

        async def run(self, request, *, progress_reporter=None):
            captured["request"] = request
            captured["progress_reporter"] = progress_reporter
            return {"response": {"messages": []}, "uni_messages": [], "should_reply": False}

    monkeypatch.setattr(agent, "FrontierAgentRuntime", Runtime)
    monkeypatch.setattr(agent.EnvConfig, "QQ_TEXT_CANARY_ENABLED", False)
    monkeypatch.setattr(agent, "f_cognitive", object())

    context = _context(agent)
    assert await agent._execute_agent_request(context, history_messages=[]) is False

    request = captured["request"]
    assert request.conversation == ConversationRef(
        platform="qq",
        account_id="bot-1",
        kind="group",
        conversation_id="42",
    )
    assert request.principal == Participant(id="user-1", display_name="Alice")
    assert request.capabilities == frozenset({"platform:qq", "qq:tools"})
    # Keep the old workspace key so existing QQ memory and session files are
    # not moved merely by declaring the neutral identity.
    assert request.workspace_key == "group-42"
