# ruff: noqa: S101

import asyncio
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import ValidationError

from utils.agents.session_context import history_budget, messages_contain_media, recent_complete_turns
from utils.agents.sessions import HistoryBoundary, SessionKey, SessionManager, database_message_id
from utils.configs import EnvConfig, SessionConfig


@pytest.fixture
def setup_manager(monkeypatch):
    settings = SessionConfig(enabled=True)
    monkeypatch.setattr(EnvConfig, "SESSIONS", settings)
    now = [0.0]
    manager = SessionManager(clock=lambda: now[0])
    return manager, settings, now


async def complete(manager, lease, **kwargs):
    lease.valid_result = True
    lease.entry.state = "awaiting_delivery"
    await manager.finish(lease, silent=True, **kwargs)


def test_keys_share_group_but_isolate_bots_private_and_other_groups():
    assert SessionKey("1", "10", 20) == SessionKey("1", "11", 20)
    assert SessionKey("1", "10", 20) != SessionKey("2", "10", 20)
    assert SessionKey("1", "20") != SessionKey("1", "10", 20)
    assert SessionKey("1", "10", 20) != SessionKey("1", "10", 21)


@pytest.mark.parametrize("field,value", [
    ("group_idle_seconds", 0), ("private_idle_seconds", 0), ("max_sessions", 0),
    ("max_generation_turns", 0), ("max_session_bytes", 1), ("max_total_bytes", 1),
    ("history_max_tokens", 0), ("history_window_fraction", 0), ("history_window_fraction", 1.1),
    ("cleanup_interval_seconds", 0),
])
def test_session_config_rejects_invalid_limits(field, value):
    with pytest.raises(ValidationError):
        SessionConfig(**{field: value})


@pytest.mark.asyncio
async def test_failed_deletion_stays_invalid_until_cleanup_retries(setup_manager, monkeypatch):
    manager, settings, _ = setup_manager
    key = SessionKey("1", "10")
    lease = manager.begin(key, HistoryBoundary(1, 1000), settings, 1)
    original = manager.saver.delete_thread

    def fail(_thread):
        raise OSError("synthetic failure")

    monkeypatch.setattr(manager.saver, "delete_thread", fail)
    with pytest.raises(OSError):
        await manager.finish(lease)
    assert lease.finished and lease.entry.state == "invalidated"
    monkeypatch.setattr(manager.saver, "delete_thread", original)
    manager.sweep(settings)
    assert not manager.entries


@pytest.mark.asyncio
async def test_ttl_is_from_end_and_running_delivery_remains_pinned(setup_manager):
    manager, settings, now = setup_manager
    key = SessionKey("1", "10", 20)
    first = manager.begin(key, HistoryBoundary(1, 1000), settings, 1)
    now[0] = 10000
    manager.sweep(settings)
    assert manager.entries[key] is first.entry
    first.entry.state = "awaiting_delivery"
    manager.sweep(settings)
    assert manager.entries[key] is first.entry
    await complete(manager, first)
    now[0] += settings.group_idle_seconds - 1
    manager.sweep(settings)
    assert key in manager.entries
    now[0] += 1
    manager.sweep(settings)
    assert key not in manager.entries
    assert manager.metrics["expired"] == 1


@pytest.mark.asyncio
async def test_incremental_input_and_delivered_reply_ids_are_not_reinjected(setup_manager):
    manager, settings, _ = setup_manager
    key = SessionKey("1", "10", 20)
    first = manager.begin(key, HistoryBoundary(2, 1000), settings, 1)
    first.inputs([{"id": database_message_id("1", 1)}, {"id": first.current_id}])
    await complete(manager, first, message_id=4, delivered_at=1001)
    second = manager.begin(SessionKey("1", "11", 20), HistoryBoundary(5, 2000), settings, 1)
    assert second.hot
    # Message 3 arrived during generation, before assistant 4 was inserted.
    assert second.entry.history_cursor == 2
    messages = [{"id": database_message_id("1", number)} for number in range(1, 6)]
    assert [item["id"] for item in second.inputs(messages)] == [database_message_id("1", 3), second.current_id]
    await complete(manager, second)


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary,revision,reason", [
    (HistoryBoundary(3, 900), 1, "snapshot_conflict"),
    (HistoryBoundary(2, 2000), 1, "snapshot_conflict"),
    (HistoryBoundary(3, 2000), 2, "incompatible"),
])
async def test_snapshot_and_revision_conflicts_create_new_generation(setup_manager, boundary, revision, reason):
    manager, settings, _ = setup_manager
    key = SessionKey("1", "10")
    first = manager.begin(key, HistoryBoundary(1, 1000), settings, 1)
    await complete(manager, first, message_id=2, delivered_at=1100)
    second = manager.begin(key, boundary, settings, revision)
    assert not second.hot
    assert first.entry.thread_id != second.entry.thread_id
    assert manager.metrics[reason] == 1


@pytest.mark.asyncio
async def test_lru_capacity_and_disabled_cleanup_preserve_busy_entries(setup_manager):
    manager, settings, now = setup_manager
    settings = settings.model_copy(update={"max_sessions": 1})
    key = SessionKey("1", "10")
    lease = manager.begin(key, HistoryBoundary(1, 1000), settings, 1)
    other = SessionKey("1", "11")
    assert manager.begin(other, HistoryBoundary(2, 2000), settings, 1) is None
    assert manager.metrics["capacity_fallback"] == 1
    manager.sweep(settings.model_copy(update={"enabled": False}))
    assert key in manager.entries
    await complete(manager, lease)
    now[0] += 1
    assert manager.begin(other, HistoryBoundary(2, 2000), settings, 1) is not None
    assert key not in manager.entries


@pytest.mark.asyncio
async def test_rotation_media_and_failure_do_not_reuse_old_state(setup_manager):
    manager, settings, _ = setup_manager
    settings = settings.model_copy(update={"max_generation_turns": 1})
    key = SessionKey("1", "10")
    first = manager.begin(key, HistoryBoundary(1, 1000), settings, 1)
    await complete(manager, first)
    assert key not in manager.entries
    assert manager.metrics["rotated"] == 1
    second = manager.begin(key, HistoryBoundary(2, 2000), settings, 1)
    second.media_turn = True
    await complete(manager, second)
    assert manager.metrics["media_rotations"] == 1
    third = manager.begin(key, HistoryBoundary(3, 3000), settings, 1)
    await manager.finish(third)
    assert manager.metrics["failed"] == 1
    assert manager.saver.size() == 0


@pytest.mark.asyncio
async def test_settlement_uses_audited_text_and_cancellation_invalidates(setup_manager):
    manager, settings, _ = setup_manager
    key = SessionKey("1", "10")
    updates = []

    async def update(config, values):
        updates.append(values)

    lease = manager.begin(key, HistoryBoundary(1, 1000), settings, 1)
    lease.graph = SimpleNamespace(aupdate_state=update)
    lease.final_message = AIMessage(content="unreviewed", id="answer")
    lease.valid_result = True
    await manager.finish(lease, delivered=True, content="audited", message_id=2, delivered_at=1100)
    assert updates[0]["messages"][0].content == "audited"
    assert updates[0]["messages"][0].id == "answer"
    assert lease.graph is None
    await manager.finish(lease, delivered=True)  # idempotent settlement
    assert len(updates) == 1

    async def cancel(config, values):
        raise asyncio.CancelledError

    lease = manager.begin(key, HistoryBoundary(3, 2000), settings, 1)
    lease.graph = SimpleNamespace(aupdate_state=cancel)
    lease.final_message = AIMessage(content="unreviewed", id="next")
    lease.valid_result = True
    with pytest.raises(asyncio.CancelledError):
        await manager.finish(lease, delivered=True)
    assert lease.finished
    assert lease.entry.state == "invalidated"
    manager.sweep(settings)
    assert not manager.entries


def test_history_trimming_keeps_complete_tool_exchanges_and_obeys_profile_budget(setup_manager):
    _, settings, _ = setup_manager
    old = HumanMessage(content="old " * 1000)
    recent = [HumanMessage(content="read"), AIMessage(content="", tool_calls=[{"name": "read", "args": {}, "id": "c"}]),
              ToolMessage(content="result", tool_call_id="c"), AIMessage(content="done")]
    assert recent_complete_turns([old, AIMessage(content="old reply"), *recent], 100) == recent
    assert recent_complete_turns(recent, 0) == []
    assert history_budget(settings, {"max_input_tokens": 10000}) == 2500
    assert history_budget(settings, {"max_input_tokens": 10000}, reserved_tokens=9999) == 1
    assert history_budget(settings, None) == 8000


def test_media_in_history_or_tool_content_retires_generation():
    assert messages_contain_media([{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,YQ=="}}]}])
    assert messages_contain_media([ToolMessage(content=[{"type": "audio", "base64": "YQ==", "mime_type": "audio/wav"}], tool_call_id="a")])
    assert not messages_contain_media([HumanMessage(content="/memory/group_1/images/a.png")])


def test_parallel_saver_writes_share_one_global_budget():
    from concurrent.futures import ThreadPoolExecutor

    from utils.agents.checkpoints import BoundedMemorySaver
    from utils.agents.session_errors import CheckpointCapacityExceeded

    saver = BoundedMemorySaver()
    for index in range(8):
        saver.register(str(index), limit=8192, total_limit=12000)

    def write(index):
        try:
            saver.put_writes({"configurable": {"thread_id": str(index), "checkpoint_ns": "", "checkpoint_id": "one"}},
                             [("value", "x" * 4000)], str(index))
            return True
        except CheckpointCapacityExceeded:
            return False

    with ThreadPoolExecutor(max_workers=8) as executor:
        accepted = list(executor.map(write, range(8)))
    assert sum(accepted) == 2
    assert saver.size() <= 12000
    assert saver.capacity_errors == 6
    for index in range(8):
        saver.delete_thread(str(index))
    assert saver.size() == 0
