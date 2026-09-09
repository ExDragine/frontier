# ruff: noqa: S101
"""Behavioral contracts for complete Agent turns and shared workspaces."""

import asyncio

import pytest
from langchain_core.exceptions import ModelTimeoutError

from utils.agents import execution
from utils.agents.execution import managed_agent_turn
from utils.agents.runtime import _agent_locks, run_serialized
from utils.configs import EnvConfig


def success():
    return {"response": {"messages": []}, "uni_messages": [], "should_reply": True}


@pytest.mark.asyncio
async def test_deadline_covers_queued_turn_and_releases_lock(monkeypatch):
    monkeypatch.setattr(EnvConfig, "AGENT_JOB_TIMEOUT_SECONDS", 0.03)
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def holder():
        entered.set()
        await release.wait()

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None, progress_reporter=None):
        calls.append(user_id)
        return success()

    holding = asyncio.create_task(run_serialized("workspace:group-123", holder))
    await entered.wait()
    result = await turn([], "one", "One", group_id=123)
    assert result["status"] == "timeout"
    assert calls == []
    release.set()
    await holding
    result = await turn([], "one", "One", group_id=123)
    assert result["status"] == "success"
    assert not _agent_locks


@pytest.mark.asyncio
async def test_cancellation_cleans_running_work_and_allows_next_turn():
    entered = asyncio.Event()
    cleaned = asyncio.Event()

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None, progress_reporter=None):
        try:
            entered.set()
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    task = asyncio.create_task(turn([], "one", "One"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cleaned.is_set()
    assert not _agent_locks


@pytest.mark.asyncio
async def test_shared_group_workspace_serializes_different_members():
    active = set()
    overlap = []

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None, progress_reporter=None):
        if active:
            overlap.append(user_id)
        active.add(user_id)
        await asyncio.sleep(0)
        active.remove(user_id)
        return success()

    results = await asyncio.gather(*(turn([], str(i), "Member", group_id=123) for i in range(5)))
    assert not overlap
    assert len({result["run_id"] for result in results}) == 5
    assert all(result["status"] == "success" for result in results)
    assert not _agent_locks


@pytest.mark.asyncio
async def test_initialization_failure_is_reported_without_provider_secrets(monkeypatch):
    from utils.agents import cognitive

    def fail(**kwargs):
        raise ValueError("secret provider configuration")

    # All construction now happens inside the managed lifetime, not __init__.
    monkeypatch.setattr(cognitive, "build_document_subagent", fail)
    agent = cognitive.FrontierCognitive()
    result = await agent.chat_agent([], "1", "One")
    assert result["status"] == "failed"
    assert result["error"] == "ValueError"
    assert "secret" not in str(result)
    assert result["uni_messages"] == []


@pytest.mark.asyncio
async def test_configuration_revision_rebuilds_model_dependent_components(monkeypatch):
    from utils.agents import cognitive

    builds = []

    def document():
        builds.append(EnvConfig.REVISION)
        return {"name": "document-agent"}

    monkeypatch.setattr(cognitive, "build_document_subagent", document)
    agent = cognitive.FrontierCognitive()
    await agent._prepare_components()
    await agent._prepare_components()
    assert len(builds) == 1
    monkeypatch.setattr(EnvConfig, "REVISION", EnvConfig.REVISION + 1)
    await agent._prepare_components()
    assert len(builds) == 2


@pytest.mark.asyncio
async def test_failure_returns_when_terminal_reporter_stalls(monkeypatch):
    monkeypatch.setattr(execution, "_TERMINAL_PROGRESS_TIMEOUT_SECONDS", 0.01)
    reporter_cleaned = asyncio.Event()

    async def stalled_reporter(event):
        try:
            await asyncio.Event().wait()
        finally:
            reporter_cleaned.set()

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None, progress_reporter=None):
        raise ModelTimeoutError("private provider response")

    result = await asyncio.wait_for(turn([], "one", "One", progress_reporter=stalled_reporter), 1)
    assert result["status"] == "timeout"
    assert reporter_cleaned.is_set()
    assert "private provider" not in str(result)
    assert not _agent_locks


@pytest.mark.asyncio
async def test_cancellation_does_not_wait_for_progress_transport():
    entered = asyncio.Event()

    async def stalled_reporter(event):
        await asyncio.Event().wait()

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None, progress_reporter=None):
        entered.set()
        await asyncio.Event().wait()

    task = asyncio.create_task(turn([], "one", "One", progress_reporter=stalled_reporter))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 1)
    assert not _agent_locks
