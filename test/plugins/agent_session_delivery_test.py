# ruff: noqa: S101

import asyncio
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from utils.agents.sessions import SessionManager
from utils.configs import SessionConfig
from utils.delivery import DeliveryResult


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["success", "send_failure", "partial_artifacts", "db_failure", "cancel", "silent"])
async def test_session_lease_covers_qq_delivery_and_failure_cleanup(monkeypatch, outcome):  # noqa: C901
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    manager = SessionManager()
    monkeypatch.setattr(agent, "session_manager", manager)
    monkeypatch.setattr(agent.EnvConfig, "SESSIONS", SessionConfig(enabled=True))
    # sessions.py holds the same runtime config in production; tests reload it.
    from utils.agents import sessions
    monkeypatch.setattr(sessions.EnvConfig, "SESSIONS", agent.EnvConfig.SESSIONS)
    captured = {"updates": [], "sends": 0}

    async def update(config, values):
        captured["updates"].append(values)

    class Database:
        async def prepare_session_history(self, **kwargs):
            captured["query"] = kwargs
            return [{"role": "user", "content": "scoped history", "id": "qq:99:message:1"}]

        async def insert(self, **kwargs):
            captured["stored"] = kwargs["content"]
            if outcome == "db_failure":
                raise OSError("synthetic DB failure")
            return SimpleNamespace(message_id=3)

    class Cognitive:
        async def chat_agent(self, messages, **kwargs):
            lease = kwargs["session_turn"]
            captured["lease"] = lease
            assert messages[-1]["id"] == lease.current_id
            assert messages[0]["content"] == "scoped history"
            assert kwargs["group_member_role"] == "member"
            if outcome == "cancel":
                raise asyncio.CancelledError
            lease.valid_result = True
            lease.entry.state = "awaiting_delivery"
            lease.graph = SimpleNamespace(aupdate_state=update)
            lease.final_message = AIMessage(content="raw", id="answer")
            return {"response": {"messages": [lease.final_message]}, "uni_messages": ["artifact"] if outcome == "partial_artifacts" else [],
                    "should_reply": outcome != "silent"}

    async def sanitize(_text):
        return "audited"

    async def send(_group, _event, response):
        assert manager.snapshot()["awaiting_delivery"] == 1
        assert response["messages"][-1].content == "audited"
        captured["sends"] += 1
        if outcome == "send_failure":
            return DeliveryResult(attempted=1, errors=("failed",))
        return DeliveryResult(attempted=1, sent=1)

    async def artifacts(_items):
        return DeliveryResult(attempted=2, sent=1, errors=("one attachment failed",))

    monkeypatch.setattr(agent, "messages_db", Database())
    monkeypatch.setattr(agent, "f_cognitive", Cognitive())
    monkeypatch.setattr(agent, "sanitize_outgoing_text", sanitize)
    monkeypatch.setattr(agent, "send_messages", send)
    monkeypatch.setattr(agent, "send_artifacts", artifacts)
    context = agent.AgentRequestContext(
        event=SimpleNamespace(self_id="99", data=SimpleNamespace(group_member=SimpleNamespace(role="member"))),
        user_id="10", user_name="User", event_id=2, group_id=20, msg_time=2000,
        text="current", quoted_images=[], images=[], videos=[], message_id=2,
    )
    if outcome == "cancel":
        with pytest.raises(asyncio.CancelledError):
            await agent._process_agent_request(context, [{"role": "user", "content": "unscoped"}])
    else:
        await agent._process_agent_request(context, [{"role": "user", "content": "unscoped"}])
    assert captured["query"]["before_message_id"] == 2
    assert captured["query"]["before_time"] == 2000
    assert captured["query"]["bot_user_id"] == 99
    assert captured["lease"].finished
    assert captured["sends"] == (0 if outcome in {"cancel", "silent"} else 1)
    if outcome in {"success", "db_failure", "silent"}:
        assert len(manager.entries) == 1
        assert next(iter(manager.entries.values())).state == "idle"
        if outcome != "silent":
            assert captured["updates"][0]["messages"][0].content == "audited"
            assert captured["stored"] == "audited"
    else:
        assert not manager.entries
    await manager.close()


@pytest.mark.asyncio
async def test_history_failure_releases_running_lease(monkeypatch):
    import nonebot
    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    manager = SessionManager()
    monkeypatch.setattr(agent, "session_manager", manager)
    monkeypatch.setattr(agent.EnvConfig, "SESSIONS", SessionConfig(enabled=True))

    async def read(**kwargs):
        raise OSError("synthetic history failure")

    monkeypatch.setattr(agent, "messages_db", SimpleNamespace(prepare_session_history=read))
    context = agent.AgentRequestContext(event=SimpleNamespace(self_id="99"), user_id="10", user_name="User",
        event_id=2, group_id=20, msg_time=2000, text="current", quoted_images=[], images=[], videos=[], message_id=2)
    with pytest.raises(OSError):
        await agent._process_agent_request(context)
    assert not manager.entries


@pytest.mark.asyncio
async def test_cache_initialization_failure_uses_scoped_history_without_reexecution(monkeypatch):
    import nonebot
    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import agent

    manager = SessionManager()
    monkeypatch.setattr(agent, "session_manager", manager)
    monkeypatch.setattr(agent.EnvConfig, "SESSIONS", SessionConfig(enabled=True))
    calls = []

    def fail(*args):
        raise OSError("synthetic cache maintenance failure")

    async def read(**kwargs):
        assert kwargs["bot_user_id"] == 99 and kwargs["before_message_id"] == 2
        return [{"role": "user", "content": "scoped"}]

    async def execute(context, history, lease):
        assert lease is None and history == [{"role": "user", "content": "scoped"}]
        calls.append(context)
        return True

    monkeypatch.setattr(manager, "begin", fail)
    monkeypatch.setattr(agent, "messages_db", SimpleNamespace(prepare_session_history=read))
    monkeypatch.setattr(agent, "_execute_agent_request", execute)
    context = agent.AgentRequestContext(event=SimpleNamespace(self_id="99"), user_id="10", user_name="User",
        event_id=2, group_id=20, msg_time=2000, text="current", quoted_images=[], images=[], videos=[], message_id=2)
    assert await agent._process_agent_request(context, [{"role": "user", "content": "unscoped"}])
    assert calls == [context]
    assert manager.metrics["initialization_fallback"] == 1
