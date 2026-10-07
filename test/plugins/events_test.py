# ruff: noqa: S101
import asyncio
import importlib

import pytest


def test_plain_package_import_does_not_register_runtime():
    package = importlib.import_module("plugins.events")
    assert package.__doc__
    assert not hasattr(package, "__plugin__")


@pytest.mark.asyncio
async def test_event_plugin_lifecycle_and_real_request_normalization(monkeypatch, tmp_path):
    from nonebot.adapters.milky.event import FriendRequestEvent
    from sqlmodel import create_engine

    from plugins.events import runtime
    from utils.database.platform_events import PlatformEventStore
    from utils.event_orchestration import EventOrchestrator
    from utils.event_policy import EventConfig

    engine = create_engine(f"sqlite:///{tmp_path / 'inbox.db'}", connect_args={"check_same_thread": False})
    store = PlatformEventStore(engine)
    cfg = EventConfig()
    runner = EventOrchestrator(store, lambda: cfg, lambda _: pytest.fail("record mode cannot use bot"))
    monkeypatch.setattr(runtime, "store", store)
    monkeypatch.setattr(runtime, "orchestrator", runner)
    monkeypatch.setattr(runtime, "tasks", [])
    monkeypatch.setattr(runtime, "ready", asyncio.Event())
    monkeypatch.setattr(runtime, "get_bots", lambda: {})
    await runtime.startup()
    try:
        event = FriendRequestEvent(time=123, self_id=100, data={
            "initiator_id": 456, "initiator_uid": "u-456", "comment": "hello", "via": "search",
        })
        assert await runtime.supported(event)
        await runtime.receive(event)
        assert len(await store.recent()) == 1
    finally:
        pending = list(runtime.tasks)
        await runtime.shutdown()
        assert all(task.done() for task in pending)
        assert not runtime.ready.is_set()
        engine.dispose()
