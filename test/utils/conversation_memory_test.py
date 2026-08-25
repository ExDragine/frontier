# ruff: noqa: S101

import json
import sys
import types
from typing import Any

import pytest
from sqlalchemy import text
from sqlmodel import create_engine

from utils import database as db_module
from utils.database import ConversationSummary, Message, MessageDatabase

HOUR = 60 * 60 * 1000
CURRENT_HOUR = 20 * HOUR
REFERENCE_TIME = CURRENT_HOUR + 30 * 60 * 1000


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


def _trim(messages, *, max_tokens, strategy="last", token_counter=None, **_kwargs):
    converted = [
        message
        if not isinstance(message, dict)
        else _Message(message.get("content", ""), message_type="human" if message.get("role") == "user" else "ai")
        for message in messages
    ]
    counter = token_counter or _count
    ordered = converted if strategy == "first" else list(reversed(converted))
    kept = []
    used = 0
    for message in ordered:
        tokens = counter([message])
        if used + tokens > max_tokens:
            break
        kept.append(message)
        used += tokens
    return kept if strategy == "first" else list(reversed(kept))


@pytest.fixture
def message_stubs(monkeypatch):
    messages_module: Any = types.ModuleType("langchain_core.messages")
    messages_module.BaseMessage = _Message
    messages_module.HumanMessage = _HumanMessage
    messages_module.SystemMessage = _SystemMessage
    utils_module: Any = types.ModuleType("langchain_core.messages.utils")
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


def _set_context_stable(database: MessageDatabase) -> None:
    with database.engine.begin() as connection:
        connection.execute(text("UPDATE message SET context_updated_at = 1"))


def _summary(*, bucket_start: int, version: int, prompt_version: int = 4) -> ConversationSummary:
    return ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=version,
        source_start_time=bucket_start,
        source_end_time=bucket_start + HOUR - 1,
        source_message_count=1,
        source_token_count=10,
        summary_text=f"hour-summary-{bucket_start}",
        estimated_tokens=10,
        model="basic",
        prompt_version=prompt_version,
        created_at=REFERENCE_TIME,
    )


def test_rolling_window_contains_twelve_completed_hour_buckets():
    from utils.agents import conversation_memory as memory

    window_start, current_hour = memory._rolling_window(REFERENCE_TIME)

    assert current_hour == CURRENT_HOUR
    assert window_start == CURRENT_HOUR - 12 * HOUR
    assert len(list(memory._bucket_starts(window_start, current_hour))) == 12
    assert memory.SUMMARY_INJECTION_HOURS == 3


@pytest.mark.asyncio
async def test_assemble_injects_only_three_recent_summaries_and_current_hour_raw(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    monkeypatch.setattr(memory.EnvConfig, "CONVERSATION_MEMORY_MAX_CONTEXT_TOKENS", 20_000)
    expired_summary_hour = CURRENT_HOUR - 4 * HOUR
    summary_hours = [CURRENT_HOUR - offset * HOUR for offset in (3, 2, 1)]
    missing_hour = CURRENT_HOUR - HOUR
    await memory_database.insert(CURRENT_HOUR - 13 * HOUR, 1, 10, 123, "Old", "user", "too-old")
    await memory_database.insert(missing_hour + 1000, 3, 10, 123, "Bob", "user", "covered-raw")
    await memory_database.insert(CURRENT_HOUR + 1000, 4, 10, 123, "Alice", "user", "current-raw")
    for version, bucket_start in enumerate([expired_summary_hour, *summary_hours], start=1):
        assert await memory_database.append_conversation_summary(
            _summary(bucket_start=bucket_start, version=version),
            expected_version=version - 1,
        )

    assembled, _budget = await memory.assemble_conversation_history(
        memory.ConversationHistoryRequest(
            database=memory_database,
            scope=memory.ConversationScope.from_ids(10, 123),
            before_time=REFERENCE_TIME,
            prefix_message_count=0,
        ),
        model=types.SimpleNamespace(profile={"max_input_tokens": 40_000}),
        system_prompt="system",
        tools=[],
        current_messages=[{"role": "user", "content": "current"}],
    )

    text_content = "\n".join(_content(message) for message in assembled)
    assert all(f"hour-summary-{bucket}" in text_content for bucket in summary_hours)
    assert f"hour-summary-{expired_summary_hour}" not in text_content
    assert "covered-raw" not in text_content
    assert "current-raw" in text_content
    assert "too-old" not in text_content


@pytest.mark.asyncio
async def test_assemble_does_not_fallback_to_completed_hour_raw_messages(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    monkeypatch.setattr(memory.EnvConfig, "CONVERSATION_MEMORY_MAX_CONTEXT_TOKENS", 20_000)
    await memory_database.insert(CURRENT_HOUR - HOUR + 1000, 1, 10, 123, "Bob", "user", "unsummarized")
    await memory_database.insert(CURRENT_HOUR + 1000, 2, 10, 123, "Alice", "user", "current")

    assembled, _budget = await memory.assemble_conversation_history(
        memory.ConversationHistoryRequest(
            database=memory_database,
            scope=memory.ConversationScope.from_ids(10, 123),
            before_time=REFERENCE_TIME,
            prefix_message_count=0,
        ),
        model=types.SimpleNamespace(profile={"max_input_tokens": 40_000}),
        system_prompt="system",
        tools=[],
        current_messages=[{"role": "user", "content": "latest"}],
    )

    text_content = "\n".join(_content(message) for message in assembled)
    assert "unsummarized" not in text_content
    assert "current" in text_content


@pytest.mark.asyncio
async def test_compaction_creates_independent_summaries_for_each_active_hour(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    first_hour = CURRENT_HOUR - 2 * HOUR
    second_hour = CURRENT_HOUR - HOUR
    await memory_database.insert(first_hour + 1000, 1, 10, 123, "Alice", "user", "first-hour")
    await memory_database.insert(second_hour + 1000, 2, 20, 123, "Bob", "user", "second-hour")
    _set_context_stable(memory_database)
    prompts = []

    class _Model:
        async def ainvoke(self, messages):
            prompts.append(json.loads(messages[-1].content))
            return types.SimpleNamespace(content=f"summary-{len(prompts)}")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=REFERENCE_TIME)
    summaries = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=CURRENT_HOUR - 12 * HOUR,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )

    assert [item.source_start_time for item in summaries] == [first_hour, second_hour]
    assert [item.summary_text for item in summaries] == ["summary-1", "summary-2"]
    assert all(item.source_end_time == item.source_start_time + HOUR - 1 for item in summaries)
    assert [prompt["period"]["start"] for prompt in prompts] == [first_hour, second_hour]
    assert all("existing_summary" not in prompt for prompt in prompts)
    assert all(prompt["existing_hour_summary"] == "无" for prompt in prompts)


@pytest.mark.asyncio
async def test_large_hour_is_summarized_in_incremental_chunks(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    bucket = CURRENT_HOUR - HOUR
    await memory_database.insert(bucket + 1000, 1, 10, 123, "Alice", "user", "first")
    await memory_database.insert(bucket + 2000, 2, 20, 123, "Bob", "user", "second")
    with memory_database.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE message SET estimated_tokens = 700, context_updated_at = 1 "
                "WHERE group_id = 123"
            )
        )
    prompts = []

    class _Model:
        profile = {"max_input_tokens": 2048}

        async def ainvoke(self, messages):
            prompts.append(json.loads(messages[-1].content))
            return types.SimpleNamespace(content=f"partial-{len(prompts)}")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=REFERENCE_TIME)
    summaries = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=bucket,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )

    assert len(prompts) == 2
    assert prompts[0]["existing_hour_summary"] == "无"
    assert prompts[1]["existing_hour_summary"] == "partial-1"
    assert [len(prompt["history"]) for prompt in prompts] == [1, 1]
    assert len(summaries) == 1
    assert summaries[0].summary_text == "partial-2"


@pytest.mark.asyncio
async def test_late_message_invalidates_and_rebuilds_only_its_hour(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    earlier_bucket = CURRENT_HOUR - 2 * HOUR
    bucket = CURRENT_HOUR - HOUR
    await memory_database.insert(earlier_bucket + 1000, 0, 10, 123, "Alice", "user", "earlier")
    await memory_database.insert(bucket + 1000, 1, 10, 123, "Alice", "user", "original")
    _set_context_stable(memory_database)
    calls = 0

    class _Model:
        async def ainvoke(self, _messages):
            nonlocal calls
            calls += 1
            return types.SimpleNamespace(content=f"summary-v{calls}")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    service = memory.ConversationMemoryService(memory_database)
    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=REFERENCE_TIME)

    await memory_database.insert(bucket + 2000, 2, 20, 123, "Bob", "user", "late")
    still_active = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=earlier_bucket,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    assert [item.source_start_time for item in still_active] == [earlier_bucket]

    _set_context_stable(memory_database)
    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=REFERENCE_TIME)
    rebuilt = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=bucket,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    assert len(rebuilt) == 1
    assert rebuilt[0].summary_text == "summary-v3"
    assert rebuilt[0].source_message_count == 2


@pytest.mark.asyncio
async def test_compaction_summarizes_completed_hour_but_skips_current_hour(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    completed = CURRENT_HOUR - HOUR
    await memory_database.insert(completed + 1000, 1, 10, 123, "Alice", "user", "unstable")
    await memory_database.insert(CURRENT_HOUR + 1000, 2, 10, 123, "Alice", "user", "current")
    calls = []

    class _Model:
        async def ainvoke(self, messages):
            calls.append(json.loads(messages[-1].content))
            return types.SimpleNamespace(content="completed-summary")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=REFERENCE_TIME)
    summaries = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=CURRENT_HOUR - 12 * HOUR,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    assert len(calls) == 1
    assert len(summaries) == 1
    assert summaries[0].source_start_time == completed


@pytest.mark.asyncio
async def test_compaction_discards_result_when_source_changes_during_model_call(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    bucket = CURRENT_HOUR - HOUR
    message_time = bucket + 1000
    await memory_database.insert(message_time, 1, 10, 123, "Alice", "user", "before")
    _set_context_stable(memory_database)

    class _Model:
        async def ainvoke(self, _messages):
            with memory_database.engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE message SET content = 'changed', context_updated_at = :updated "
                        "WHERE time = :message_time"
                    ),
                    {"updated": REFERENCE_TIME, "message_time": message_time},
                )
            return types.SimpleNamespace(content="stale-summary")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    service = memory.ConversationMemoryService(memory_database)

    assert not await service.compact_scope(user_id=10, group_id=123, cutoff_time=REFERENCE_TIME)
    assert await memory_database.latest_conversation_summary(scope_type="group", scope_id="123") is None


@pytest.mark.asyncio
async def test_prune_removes_expired_and_legacy_summaries(memory_database):
    from utils.agents import conversation_memory as memory

    old = _summary(bucket_start=CURRENT_HOUR - 13 * HOUR, version=1)
    legacy = _summary(bucket_start=CURRENT_HOUR - HOUR, version=2, prompt_version=3)
    current = _summary(bucket_start=CURRENT_HOUR - 2 * HOUR, version=3)
    assert await memory_database.append_conversation_summary(old, expected_version=0)
    assert await memory_database.append_conversation_summary(legacy, expected_version=1)
    assert await memory_database.append_conversation_summary(current, expected_version=2)

    deleted = await memory_database.prune_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=CURRENT_HOUR - 12 * HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )

    assert deleted == 2
    latest = await memory_database.latest_conversation_summary(scope_type="group", scope_id="123")
    assert latest is not None and latest.version == 3


@pytest.mark.asyncio
async def test_hourly_refresh_skips_model_when_completed_hour_has_no_messages(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    monkeypatch.setattr(memory.EnvConfig, "CONVERSATION_MEMORY_ENABLED", True)
    monkeypatch.setattr(
        memory,
        "create_llm",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("model must not be called")),
    )
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_active_scopes(reference_time=REFERENCE_TIME) == 0


@pytest.mark.asyncio
async def test_hourly_refresh_compacts_only_scopes_active_in_completed_hour(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    previous_hour = CURRENT_HOUR - HOUR
    await memory_database.insert(previous_hour + 1000, 1, 10, None, "Private", "user", "private")
    await memory_database.insert(previous_hour + 2000, 2, 20, 123, "Group", "user", "group")
    await memory_database.insert(CURRENT_HOUR + 1000, 3, 30, 456, "Current", "user", "not-completed")
    _set_context_stable(memory_database)
    prompts = []

    class _Model:
        async def ainvoke(self, messages):
            prompts.append(json.loads(messages[-1].content))
            return types.SimpleNamespace(content=f"summary-{len(prompts)}")

    monkeypatch.setattr(memory.EnvConfig, "CONVERSATION_MEMORY_ENABLED", True)
    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_active_scopes(reference_time=REFERENCE_TIME) == 2
    assert len(prompts) == 2
    private = await memory_database.hourly_conversation_summaries(
        scope_type="private",
        scope_id="10",
        window_start=previous_hour,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    group = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="123",
        window_start=previous_hour,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    inactive = await memory_database.hourly_conversation_summaries(
        scope_type="group",
        scope_id="456",
        window_start=previous_hour,
        window_end=CURRENT_HOUR,
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
    )
    assert len(private) == len(group) == 1
    assert inactive == []


def test_summary_envelope_identifies_one_hour(message_stubs):
    from utils.agents import conversation_memory as memory

    summary = _summary(bucket_start=CURRENT_HOUR - HOUR, version=1)
    message = memory._summary_message(summary, 1000)

    assert message is not None
    payload = json.loads(message.content)
    assert payload["schema"] == "frontier.conversation_summary.v1"
    assert payload["period"] == {
        "start": CURRENT_HOUR - HOUR,
        "end": CURRENT_HOUR,
    }
    assert payload["trust"] == "untrusted_history"


@pytest.mark.asyncio
async def test_empty_window_does_not_call_model(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    monkeypatch.setattr(
        memory,
        "create_llm",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("model must not be called")),
    )
    service = memory.ConversationMemoryService(memory_database)

    assert not await service.compact_scope(user_id=10, group_id=None, cutoff_time=REFERENCE_TIME)


def test_summary_prompt_is_hour_local_and_compact():
    from utils.agents import conversation_memory as memory

    assert "单个自然小时" in memory.SUMMARY_SYSTEM_PROMPT
    assert "不引用更早时段" in memory.SUMMARY_SYSTEM_PROMPT
    assert "累计记忆" in memory.SUMMARY_SYSTEM_PROMPT
    assert memory.ROLLING_MEMORY_HOURS == 12
