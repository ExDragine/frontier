# ruff: noqa: S101

import json
import os
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest
from sqlalchemy import text
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


def _set_context_updated_at(database: MessageDatabase, values: int | dict[int, int]) -> None:
    with database.engine.begin() as connection:
        if isinstance(values, int):
            connection.execute(text("UPDATE message SET context_updated_at = :value"), {"value": values})
            return
        for msg_time, updated_at in values.items():
            connection.execute(
                text("UPDATE message SET context_updated_at = :updated_at WHERE time = :msg_time"),
                {"updated_at": updated_at, "msg_time": msg_time},
            )


def _trim(messages, *, max_tokens, strategy="last", allow_partial=False, token_counter=None, **_kwargs):
    if strategy == "first" and _kwargs.get("start_on"):
        raise ValueError("start_on parameter is only valid with strategy='last'")
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


class _Scheduler:
    def __init__(self):
        self.jobs = {}

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def add_job(self, func, _trigger, **kwargs):
        job_id = kwargs["id"]
        if job_id in self.jobs and not kwargs.get("replace_existing"):
            raise RuntimeError(f"duplicate job: {job_id}")
        job = types.SimpleNamespace(func=func, **kwargs)
        self.jobs[job_id] = job
        return job


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
    _set_context_updated_at(memory_database, 1)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=None) is True
    latest = await memory_database.latest_conversation_summary(scope_type="private", scope_id="10")
    assert latest is not None
    assert latest.version == 1
    assert latest.source_start_time == 1000
    assert latest.source_end_time >= 1000
    assert "持续事项" in latest.summary_text


@pytest.mark.asyncio
async def test_compaction_rebuilds_after_covered_source_is_invalidated(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    for index in range(1, 5):
        await memory_database.insert(
            index * 1000,
            index,
            10,
            123,
            "Alice",
            "user",
            f"history-{index}-" + "x" * 200,
        )
    stale = ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=1,
        source_start_time=1000,
        source_end_time=2000,
        source_message_count=2,
        source_token_count=100,
        summary_text="旧内容",
        estimated_tokens=10,
        model="basic",
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
        created_at=5000,
    )
    assert await memory_database.append_conversation_summary(stale, expected_version=0)
    await memory_database.finalize_message_context(time=1000)
    _set_context_updated_at(memory_database, 1)

    class _Model:
        async def ainvoke(self, _messages):
            return types.SimpleNamespace(content="## 会话概览\n已从原文重建。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=10_000) is True
    latest = await memory_database.latest_conversation_summary(scope_type="group", scope_id="123")
    assert latest is not None
    assert latest.version == 2
    assert latest.source_start_time == 1000
    assert "原文重建" in latest.summary_text


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
    _set_context_updated_at(memory_database, 1)
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
    compaction_input = json.loads(captured["prompt"])
    first_event = compaction_input["new_history"][0]
    assert first_event["message"]["schema"] == "frontier.qq_message.v1"
    assert first_event["message"]["sender"]["user_id"] == "10"


def test_summary_envelope_is_valid_json_with_real_langchain(tmp_path):
    project_root = Path(__file__).resolve().parents[2]
    script = """
import json
from types import SimpleNamespace
from utils.agents.conversation_memory import _summary_message

summary = SimpleNamespace(
    scope_type="group",
    scope_id="123",
    source_end_time=1000,
    summary_text="## 会话概览\\n" + "甲乙丙丁" * 2000,
)
message = _summary_message(summary, 200)
assert message is not None
payload = json.loads(message.content)
assert payload["schema"] == "frontier.conversation_summary.v1"
assert payload["scope"] == {"type": "group", "id": "123"}
assert payload["content"].endswith("[摘要因上下文预算截断]")
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(project_root), value] if (value := env.get("PYTHONPATH")) else [str(project_root)]
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_schedule_freezes_cutoff_and_does_not_postpone_existing_job(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    await memory_database.insert(1000, 1, 10, 123, "Alice", "user", "old-" + "x" * 500)
    _set_context_updated_at(memory_database, 1)
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    seen_stability_cutoffs = []
    original_total = memory_database.context_token_total

    async def capture_total(**kwargs):
        seen_stability_cutoffs.append(kwargs.get("stable_before_time"))
        return await original_total(**kwargs)

    monkeypatch.setattr(memory_database, "context_token_total", capture_total)
    scheduler = _Scheduler()
    service = memory.ConversationMemoryService(memory_database)

    assert await service.maybe_schedule(scheduler, user_id=10, group_id=123) is True
    job_id = "conversation_compaction:group:123"
    first_job = scheduler.jobs[job_id]
    first_run_time = first_job.run_date
    cutoff_time = first_job.kwargs["cutoff_time"]

    assert await service.maybe_schedule(scheduler, user_id=10, group_id=123) is False
    assert scheduler.jobs[job_id] is first_job
    assert scheduler.jobs[job_id].run_date == first_run_time
    assert cutoff_time <= int((time.time() - memory.COMPACTION_SAFETY_WINDOW_SECONDS) * 1000) + 100
    assert seen_stability_cutoffs == [None, cutoff_time]


@pytest.mark.asyncio
async def test_recent_burst_schedules_safety_window_recheck(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    now_ms = int(time.time() * 1000)
    await memory_database.insert(now_ms, 1, 10, 123, "Alice", "user", "recent-" + "x" * 500)
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    scheduler = _Scheduler()
    service = memory.ConversationMemoryService(memory_database)

    assert await service.maybe_schedule(scheduler, user_id=10, group_id=123) is True
    job = scheduler.jobs["conversation_compaction:group:123"]

    assert job.kwargs["cutoff_time"] is None
    delay = (job.run_date - memory.datetime.now(memory.UTC)).total_seconds()
    assert memory.COMPACTION_SAFETY_WINDOW_SECONDS <= delay <= memory.COMPACTION_RECHECK_DELAY_SECONDS + 1

    class _Model:
        async def ainvoke(self, _messages):
            return types.SimpleNamespace(content="## 会话概览\n短时突发已压缩。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_safe_compaction_cutoff", lambda: now_ms + 1)
    scheduler.jobs.pop("conversation_compaction:group:123")
    assert await job.func(**job.kwargs) is True
    latest = await memory_database.latest_conversation_summary(scope_type="group", scope_id="123")
    assert latest is not None and latest.source_end_time == now_ms


@pytest.mark.asyncio
async def test_safe_backlog_above_low_watermark_schedules_immediate_drain(monkeypatch, message_stubs):
    from utils.agents import conversation_memory as memory

    class _Database:
        async def latest_conversation_summary(self, **_kwargs):
            return None

        async def context_token_total(self, *, stable_before_time=None, **_kwargs):
            return 80 if stable_before_time is not None else 110

    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 100)
    monkeypatch.setattr(memory, "_safe_compaction_cutoff", lambda: 123_000)
    scheduler = _Scheduler()
    service = memory.ConversationMemoryService(_Database())

    assert await service.maybe_schedule(scheduler, user_id=10, group_id=123, raw_budget=100) is True
    job = scheduler.jobs["conversation_compaction:group:123"]
    assert job.kwargs["cutoff_time"] == 123_000
    assert job.kwargs["raw_budget"] == 100
    assert (job.run_date - memory.datetime.now(memory.UTC)).total_seconds() <= 2


def test_nominal_budget_reserves_fixed_provider_prefix_before_raw_history(monkeypatch):
    from utils.agents import conversation_memory as memory

    monkeypatch.setattr(memory, "_catalog_context_window", lambda _model: 100_000)
    monkeypatch.setattr(memory.EnvConfig, "CONVERSATION_MEMORY_MAX_CONTEXT_TOKENS", 100_000)

    # 60k input target - 25% fixed prefix - 5% safety, then reserve 8% of
    # history for the SQL summary. This keeps the fallback watermark below the
    # actual raw-history window when tool schemas occupy a quarter of input.
    assert memory._nominal_raw_budget("model") == 38_640


def test_stale_message_estimate_includes_reply_snapshot():
    from utils.agents import conversation_memory as memory

    message = Message(
        time=1,
        msg_id=1,
        user_id=10,
        group_id=None,
        user_name="Alice",
        role="user",
        content="正文",
        reply_context_json="引用" * 500,
        estimated_tokens=1,
        token_estimate_version=0,
    )

    assert memory._message_estimate(message) == db_module.estimate_stored_message_tokens(
        message.content,
        message.user_name,
        reply_context_json=message.reply_context_json,
    )


@pytest.mark.asyncio
async def test_compaction_uses_frozen_cutoff_for_all_source_messages(monkeypatch, message_stubs, memory_database):
    from utils.agents import conversation_memory as memory

    now_ms = int(time.time() * 1000)
    cutoff_time = now_ms - memory.COMPACTION_SAFETY_WINDOW_SECONDS * 1000
    old_time = cutoff_time - 1000
    recent_time = cutoff_time + 1000
    await memory_database.insert(old_time, 1, 10, None, "Alice", "user", "old-safe-" + "x" * 500)
    await memory_database.insert(recent_time, 2, 10, None, "Alice", "user", "recent-unsafe-" + "x" * 500)
    _set_context_updated_at(
        memory_database,
        {
            old_time: cutoff_time - 1,
            recent_time: cutoff_time + 1,
        },
    )
    captured = {}

    class _Model:
        async def ainvoke(self, messages):
            captured["prompt"] = messages[-1].content
            return types.SimpleNamespace(content="## 会话概览\n旧消息。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=None, cutoff_time=cutoff_time) is True
    assert "old-safe-" in captured["prompt"]
    assert "recent-unsafe-" not in captured["prompt"]
    latest = await memory_database.latest_conversation_summary(scope_type="private", scope_id="10")
    assert latest is not None
    assert latest.source_end_time == old_time


@pytest.mark.asyncio
async def test_large_backlog_reschedules_same_cutoff_and_releases_scope_lock(
    monkeypatch, message_stubs, memory_database
):
    from utils.agents import conversation_memory as memory

    for index in range(10):
        await memory_database.insert(
            1000 + index,
            index,
            10,
            123,
            "Member",
            "user",
            f"backlog-{index}-" + "x" * 2000,
        )

    class _Model:
        async def ainvoke(self, _messages):
            return types.SimpleNamespace(content="## 会话概览\n积压摘要。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    monkeypatch.setattr(memory, "_catalog_context_window", lambda _model: 10_000)
    monkeypatch.setattr(memory, "MAX_COMPACTION_BATCHES", 1)
    _set_context_updated_at(memory_database, 1)
    scheduler = _Scheduler()
    service = memory.ConversationMemoryService(memory_database)
    service._scheduler = scheduler
    cutoff_time = 100_000

    assert (
        await service.compact_scope(
            user_id=10,
            group_id=123,
            cutoff_time=cutoff_time,
            drain=True,
        )
        is True
    )
    follow_up = scheduler.jobs["conversation_compaction:group:123"]
    assert follow_up.kwargs["cutoff_time"] == cutoff_time
    assert follow_up.kwargs["drain"] is True
    assert (follow_up.run_date - memory.datetime.now(memory.UTC)).total_seconds() <= 3
    assert len(service._locks) == 0


@pytest.mark.asyncio
async def test_compaction_never_advances_past_an_unstable_context_gap(
    monkeypatch, message_stubs, memory_database
):
    from utils.agents import conversation_memory as memory

    for msg_time, label in [(1000, "stable-a"), (2000, "unstable-b"), (3000, "stable-c")]:
        await memory_database.insert(
            msg_time,
            msg_time,
            10,
            123,
            "Member",
            "user",
            f"{label}-" + "x" * 500,
        )
    cutoff_time = 10_000
    _set_context_updated_at(memory_database, {1000: 1, 2000: cutoff_time, 3000: 1})
    prompts = []

    class _Model:
        async def ainvoke(self, messages):
            prompts.append(messages[-1].content)
            return types.SimpleNamespace(content="## 会话概览\n连续稳定前缀。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=cutoff_time) is True
    first = await memory_database.latest_conversation_summary(scope_type="group", scope_id="123")
    assert first is not None and first.source_end_time == 1000
    assert "stable-a-" in prompts[0]
    assert "unstable-b-" not in prompts[0]
    assert "stable-c-" not in prompts[0]

    _set_context_updated_at(memory_database, {2000: 1})
    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=cutoff_time) is True
    latest = await memory_database.latest_conversation_summary(scope_type="group", scope_id="123")
    assert latest is not None and latest.source_end_time == 3000
    assert "unstable-b-" in prompts[1]
    assert "stable-c-" in prompts[1]


@pytest.mark.asyncio
async def test_empty_summary_uses_safety_window_retry_instead_of_tight_loop(
    monkeypatch, message_stubs, memory_database
):
    from utils.agents import conversation_memory as memory

    for index in range(3):
        await memory_database.insert(
            1000 + index,
            index,
            10,
            123,
            "Member",
            "user",
            f"backlog-{index}-" + "x" * 500,
        )
    _set_context_updated_at(memory_database, 1)

    class _Model:
        async def ainvoke(self, _messages):
            return types.SimpleNamespace(content="")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    scheduler = _Scheduler()
    service = memory.ConversationMemoryService(memory_database)
    service._scheduler = scheduler

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=10_000, drain=True) is False
    retry = scheduler.jobs["conversation_compaction:group:123"]
    delay = (retry.run_date - memory.datetime.now(memory.UTC)).total_seconds()
    assert memory.COMPACTION_SAFETY_WINDOW_SECONDS <= delay <= memory.COMPACTION_RECHECK_DELAY_SECONDS + 1


@pytest.mark.asyncio
async def test_compaction_discards_summary_when_source_changes_during_model_call(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    for index in range(3):
        await memory_database.insert(
            1000 + index,
            index,
            10,
            123,
            "Member",
            "user",
            f"before-{index}-" + "x" * 500,
        )
    _set_context_updated_at(memory_database, 1)

    class _Model:
        async def ainvoke(self, _messages):
            with memory_database.engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE message SET content = :content, context_updated_at = :updated_at "
                        "WHERE time = :msg_time"
                    ),
                    {"content": "changed while summarizing", "updated_at": 20_000, "msg_time": 1000},
                )
            return types.SimpleNamespace(content="## 会话概览\n这份结果已经过期。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=10_000) is False
    assert await memory_database.latest_conversation_summary(scope_type="group", scope_id="123") is None


@pytest.mark.asyncio
async def test_compaction_discards_result_when_base_summary_is_invalidated_during_model_call(
    monkeypatch,
    message_stubs,
    memory_database,
):
    from utils.agents import conversation_memory as memory

    await memory_database.insert(1000, 1, 10, 123, "Alice", "user", "covered source")
    base = ConversationSummary(
        scope_type="group",
        scope_id="123",
        version=1,
        source_start_time=1000,
        source_end_time=1000,
        source_message_count=1,
        source_token_count=20,
        summary_text="旧的基摘要",
        estimated_tokens=10,
        model="basic",
        prompt_version=memory.SUMMARY_PROMPT_VERSION,
        created_at=1500,
    )
    assert await memory_database.append_conversation_summary(base, expected_version=0)
    for index in range(2, 5):
        await memory_database.insert(
            index * 1000,
            index,
            10,
            123,
            "Alice",
            "user",
            f"new-{index}-" + "x" * 500,
        )
    _set_context_updated_at(memory_database, 1)

    class _Model:
        async def ainvoke(self, _messages):
            await memory_database.finalize_message_context(time=1000)
            return types.SimpleNamespace(content="## 会话概览\n不应提交这份结果。")

    monkeypatch.setattr(memory, "create_llm", lambda **_kwargs: _Model())
    monkeypatch.setattr(memory, "_nominal_raw_budget", lambda _model: 50)
    service = memory.ConversationMemoryService(memory_database)

    assert await service.compact_scope(user_id=10, group_id=123, cutoff_time=10_000) is False
    assert await memory_database.latest_conversation_summary(scope_type="group", scope_id="123") is None
    audit = await memory_database.latest_conversation_summary(
        scope_type="group",
        scope_id="123",
        include_invalidated=True,
    )
    assert audit is not None
    assert audit.version == 1
    assert audit.invalidated_at is not None
