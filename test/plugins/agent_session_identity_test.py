"""Exercise QQ identity across SQLite, neutral conversion and session settlement."""

# ruff: noqa: S101

import time
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage
from sqlmodel import Session, create_engine, select

from plugins.agent.adapters.qq import QqHistoryStore, QqMessageAdapter
from utils.agent_protocol import AgentRequest, HistoryQuery
from utils.agents.neutral_core import FrontierAgentCore
from utils.agents.runtime_gateway import AgentRuntimeResult
from utils.agents.sessions import HistoryBoundary, SessionKey, SessionManager, database_message_id
from utils.configs import EnvConfig, SessionConfig
from utils.database import Message, MessageDatabase
from utils.delivery import DeliveryResult


@pytest.fixture
def database(monkeypatch):
    from utils.database import store

    engine = create_engine("sqlite://")
    monkeypatch.setattr(store, "get_engine", lambda: engine)
    database = MessageDatabase()
    yield database
    engine.dispose()


async def _insert_user(database, *, platform_id, timestamp, content):
    return await database.insert(
        time=timestamp, msg_id=platform_id, user_id=10, sender_user_id=10,
        group_id=20, user_name="Alice", role="user", content=content, bot_user_id=99,
    )


@pytest.mark.asyncio
async def test_database_history_keeps_state_identity_through_neutral_bridge(database, monkeypatch):
    settings = SessionConfig(enabled=True)
    monkeypatch.setattr(EnvConfig, "SESSIONS", settings)
    timestamp = int(time.time() * 1000)
    previous = await _insert_user(database, platform_id=9001, timestamp=timestamp - 1000, content="previous")
    current = await _insert_user(database, platform_id=9002, timestamp=timestamp, content="current")
    rows = await database.prepare_session_history(
        bot_user_id=99, user_id=10, group_id=20, before_time=timestamp,
        before_message_id=current.message_id, query_numbers=100,
    )
    adapter = QqMessageAdapter(99)
    conversation = adapter.conversation(group_id=20, user_id=10)
    history = await QqHistoryStore(database, loader=lambda _query: rows).load(
        HistoryQuery(conversation, limit=100, before=datetime.fromtimestamp(timestamp / 1000, tz=UTC)),
    )
    expected_id = database_message_id("99", previous.message_id)
    assert history[0].message_id == "9001"
    assert history[0].state_id == expected_id

    manager = SessionManager()
    lease = manager.begin(SessionKey("99", "10", 20), HistoryBoundary(current.message_id, timestamp), settings, 1)
    captured = []

    class Runtime:
        async def prompt(self, request):
            captured.append(list(request.messages))
            return AgentRuntimeResult(text="done")

    message = adapter.text_message(
        message_id=9002, group_id=20, user_id=10, user_name="Alice", text="current",
        created_at=datetime.fromtimestamp(timestamp / 1000, tz=UTC),
    )
    try:
        await FrontierAgentCore(Runtime()).run(AgentRequest(
            "request", message, tuple(history), "group-20", frozenset(), "default", session_turn=lease,
        ))
        model_messages = captured[0]
        assert [item["id"] for item in model_messages] == [expected_id, lease.current_id]
        assert lease.inputs(model_messages) == model_messages
        # Reloading the same database history cannot add the old input again.
        assert lease.inputs(model_messages) == [model_messages[-1]]
    finally:
        await manager.finish(lease)
        await manager.close()


@pytest.mark.asyncio
async def test_delivered_database_identity_reaches_session_and_next_turn_stays_hot(database, monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins.agent import handlers as agent

    manager = SessionManager()
    monkeypatch.setattr(agent, "session_manager", manager)
    monkeypatch.setattr(agent, "messages_db", database)
    monkeypatch.setattr(agent.EnvConfig, "SESSIONS", SessionConfig(enabled=True))
    from utils.agents import sessions

    monkeypatch.setattr(sessions.EnvConfig, "SESSIONS", agent.EnvConfig.SESSIONS)
    monkeypatch.setattr(agent, "QqToolProvider", lambda: SimpleNamespace(tools=lambda _capabilities: ()))
    turns = []

    async def update(_config, _values):
        pass

    class Cognitive:
        async def chat_agent(self, messages, **kwargs):
            lease = kwargs["session_turn"]
            turns.append((lease.hot, lease.entry.thread_id, lease.inputs(messages)))
            lease.valid_result = True
            lease.entry.state = "awaiting_delivery"
            lease.graph = SimpleNamespace(aupdate_state=update)
            lease.final_message = AIMessage(content="reply", id=f"answer-{len(turns)}")
            return {"response": {"messages": [lease.final_message]}, "uni_messages": [], "should_reply": True}

    async def send(*_args):
        return DeliveryResult(attempted=1, sent=1, message_ids=(9001 + 2 * len(turns),))

    monkeypatch.setattr(agent, "f_cognitive", Cognitive())
    monkeypatch.setattr(agent, "send_messages", send)

    def context(inserted, platform_id, timestamp):
        return agent.AgentRequestContext(
            event=SimpleNamespace(self_id="99", data=SimpleNamespace(group_member=SimpleNamespace(role="member"))),
            user_id="10", user_name="Alice", event_id=platform_id, group_id=20, msg_time=timestamp,
            text="current", quoted_images=[], images=[], videos=[], direct_mention=True,
            message_id=inserted.message_id,
        )

    timestamp = int(time.time() * 1000) - 1000
    first = await _insert_user(database, platform_id=9002, timestamp=timestamp, content="first")
    key = SessionKey("99", "10", 20)
    try:
        assert await agent._process_agent_request(context(first, 9002, timestamp))
        with Session(database.engine) as session:
            delivered = session.exec(select(Message).where(Message.msg_id == 9003)).one()
        entry = manager.entries[key]
        assert delivered.id != delivered.msg_id
        assert entry.latest_db_id == delivered.id
        assert database_message_id("99", delivered.id) in entry.seen
        assert database_message_id("99", delivered.msg_id) not in entry.seen

        next_time = max(int(time.time() * 1000), entry.latest_time) + 1
        second = await _insert_user(database, platform_id=9004, timestamp=next_time, content="second")
        assert await agent._process_agent_request(context(second, 9004, next_time))
        assert turns[0][0] is False
        assert turns[1][0] is True
        assert turns[0][1] == turns[1][1]
        assert [item["id"] for item in turns[1][2]] == [database_message_id("99", second.message_id)]
        assert manager.metrics["snapshot_conflict"] == 0
    finally:
        await manager.close()
