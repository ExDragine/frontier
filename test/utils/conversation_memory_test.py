# ruff: noqa: S101

import sys
import types

import pytest
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import ConversationSummary, Message, MessageDatabase


class _Message:
    def __init__(self, content="", *, message_type="human"):
        self.content = content
        self.type = message_type


class _HumanMessage(_Message):
    def __init__(self, content=""):
        super().__init__(content, message_type="human")


class _SystemMessage(_Message):
    def __init__(self, content=""):
        super().__init__(content, message_type="system")


def _content(value) -> str:
    if isinstance(value, dict):
        value = value.get("content", "")
    else:
        value = getattr(value, "content", value)
    return str(value)


def _count(messages, **_kwargs) -> int:
    return sum(max(1, len(_content(message)) // 10) for message in messages)


def _trim(messages, *, max_tokens, strategy="last", allow_partial=False, token_counter=None, **_kwargs):
    converted = [
        message
        if not isinstance(message, dict)
        else _Message(message.get("content", ""), message_type="human" if message.get("role") == "user" else "ai")
        for message in messages
    ]
    counter = token_counter or _count
    if counter(converted) <= max_tokens:
        return converted
    ordered = converted if strategy == "first" else list(reversed(converted))
    kept = []
    used = 0
    for message in ordered:
        tokens = counter([message])
        if used + tokens > max_tokens:
            if allow_partial and not kept:
                kept.append(_Message(_content(message)[: max_tokens * 10], message_type=message.type))
            break
        kept.append(message)
        used += tokens
    return kept if strategy == "first" else list(reversed(kept))


@pytest.fixture
def message_stubs(monkeypatch):
    messages_module = types.ModuleType("langchain_core.messages")
    messages_module.BaseMessage = _Message
    messages_module.HumanMessage = _HumanMessage
    messages_module.SystemMessage = _SystemMessage
    utils_module = types.ModuleType("langchain_core.messages.utils")
    utils_module.count_tokens_approximately = _count
    utils_module.trim_messages = _trim
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages_module)
    monkeypatch.setitem(sys.modules, "langchain_core.messages.utils", utils_module)


@pytest.fixture
def memory_database(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr(db_module, "DATABASE_FILE", "sqlite://")
    database = MessageDatabase()
    database.engine = engine
    Message.metadata.create_all(engine)
    return database


@pytest.mark.asyncio
async def test_assemble_uses_summary_cursor_and_token_budget(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    monkeypatch.setattr(memory.EnvConfig, "CONVERSATION_MEMORY_MAX_CONTEXT_TOKENS", 10_000)
    for index in range(1, 8):
        await memory_database.insert(
            index * 1000,
            index,
            10,
            123,
            f"User-{index}",
            "user",
            f"message-{index}-" + "x" * 80,
        )
    summary = ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=1,
        source_start_time=1000,
        source_end_time=3000,
        source_message_count=3,
        source_token_count=100,
        summary_text="前三条消息的累计摘要",
        estimated_tokens=10,
        model="basic",
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
        created_at=8000,
    )
    assert await memory_database.append_conversation_summary(summary, expected_version=0)

    request = memory.ConversationHistoryRequest(
        database=memory_database,
        scope=memory.ConversationScope.from_ids(10, 123),
        before_time=8000,
        prefix_message_count=0,
    )
    model = types.SimpleNamespace(profile={"max_input_tokens": 20_000})
    assembled, budget = await memory.assemble_conversation_history(
        request,
        model=model,
        system_prompt="system",
        tools=[],
        current_messages=[{"role": "user", "content": "current"}],
    )

    text = "\n".join(_content(message) for message in assembled)
    assert budget.input_target == 10_000
    assert "conversation_summary" in text
    assert "message-3-" not in text
    assert "message-4-" in text
    assert "message-7-" in text


@pytest.mark.asyncio
async def test_compaction_appends_versioned_summary(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    for index in range(1, 5):
        await memory_database.insert(
            index * 1000,
            index,
            10,
            None,
            "Alice",
            "user",
            f"history-{index}-" + "x" * 200,
        )

    class _Model:
        async def ainvoke(self, _messages):
            return types.SimpleNamespace(content="## 会话概览\nAlice 讨论了一个持续事项。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=None) is True
    latest = await memory_database.latest_conversation_summary(scope_type="private", scope_id="10")
    assert latest is not None
    assert latest.version == 1
    assert latest.source_start_time == 1000
    assert latest.source_end_time >= 1000
    assert "持续事项" in latest.summary_text


@pytest.mark.asyncio
async def test_compaction_rebuilds_incompatible_summary_from_raw_history(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    for index in range(1, 5):
        await memory_database.insert(
            index * 1000,
            index,
            10,
            123,
            f"Member-{index}",
            "user",
            f"history-{index}-" + "x" * 200,
        )
    legacy = ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=1,
        source_start_time=1000,
        source_end_time=2000,
        source_message_count=2,
        source_token_count=100,
        summary_text="旧摘要错误地混淆了参与者",
        estimated_tokens=20,
        model="old-model",
        prompt_version=1,
        created_at=5000,
    )
    assert await memory_database.append_conversation_summary(legacy, expected_version=0)
    captured = {}

    class _Model:
        async def ainvoke(self, messages):
            captured["prompt"] = messages[-1].content
            return types.SimpleNamespace(content="## 参与者与事实\n- user_id=10（Member-1）：保留正确归属。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123) is True
    latest = await memory_database.latest_conversation_summary(
        scope_type="group",
        scope_id="123",
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    assert latest is not None
    assert latest.version == 2
    assert latest.source_start_time == 1000
    assert latest.prompt_version == memory.SUMMARY_PROMPT_VERSION
    assert "旧摘要错误" not in captured["prompt"]
    assert "history-1-" in captured["prompt"]
