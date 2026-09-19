# ruff: noqa: S101

import asyncio
from types import SimpleNamespace

import pytest

from utils.agents import execution
from utils.agents.execution import managed_agent_turn
from utils.agents.usage import RunUsageCallback, UsageRegistry, _current_usage


def response(input_tokens=10, output_tokens=5):
    return SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(usage_metadata={
        "input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens,
        "input_token_details": {"cache_read": 4}, "output_token_details": {"reasoning": 2},
    }))]])


def test_usage_counts_retries_and_missing_metadata_without_double_counting():
    callback = RunUsageCallback()
    for run_id, component in [("one", "main"), ("two", "document"), ("three", "main")]:
        callback.on_chat_model_start({}, [], run_id=run_id, tags=[f"frontier:{component}"], metadata={"ls_model_name": "test"})
    callback.on_llm_end(response(), run_id="one")
    callback.on_llm_end(response(), run_id="one")
    callback.on_llm_end(response(7, 3), run_id="two")
    callback.on_llm_error(RuntimeError("private-key"), run_id="three")
    usage = callback.snapshot()
    assert usage["model_calls"] == 3
    assert usage["model_errors"] == 1
    assert usage["usage_missing_calls"] == 1
    assert usage["input_tokens"] == 17
    assert usage["output_tokens"] == 8
    assert usage["cache_read_tokens"] == 8
    assert usage["reasoning_tokens"] == 4
    assert {row["component"] for row in usage["models"]} == {"main", "document"}
    assert "private-key" not in str(usage)


@pytest.mark.asyncio
async def test_concurrent_turns_keep_usage_separate_and_failures_keep_completed_usage(monkeypatch):
    registry = UsageRegistry()
    monkeypatch.setattr(execution, "usage_registry", registry)

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None):
        callback = _current_usage.get()
        callback.on_chat_model_start({}, [], run_id=user_id)
        await asyncio.sleep(0)
        callback.on_llm_end(response(int(user_id), 1), run_id=user_id)
        if user_id == "20":
            raise TimeoutError
        return {"response": {"messages": []}, "uni_messages": [], "should_reply": True}

    first, second = await asyncio.gather(turn([], "10", "First"), turn([], "20", "Second"))
    assert first["usage"]["input_tokens"] == 10
    assert second["usage"]["input_tokens"] == 20
    assert second["status"] == "timeout"
    assert registry.snapshot()["input_tokens"] == 30
    assert registry.snapshot()["runs"] == 2
    assert _current_usage.get() is None


@pytest.mark.asyncio
async def test_cancelled_turn_records_partial_usage_and_reraises(monkeypatch):
    registry = UsageRegistry()
    monkeypatch.setattr(execution, "usage_registry", registry)

    @managed_agent_turn
    async def turn(messages, user_id, user_name, group_id=None):
        callback = _current_usage.get()
        callback.on_chat_model_start({}, [], run_id="model")
        callback.on_llm_end(response(), run_id="model")
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await turn([], "1", "User")
    snapshot = registry.snapshot()
    assert snapshot["recent_runs"][0]["status"] == "cancelled"
    assert snapshot["total_tokens"] == 15
    assert _current_usage.get() is None


def test_usage_registry_is_bounded_and_returns_detached_data():
    registry = UsageRegistry(recent_limit=2)
    usage = RunUsageCallback().snapshot()
    for index in range(3):
        registry.record(run_id=str(index), status="failed", error_code="budget_exceeded", duration=1, usage=usage)
    snapshot = registry.snapshot()
    assert [run["run_id"] for run in snapshot["recent_runs"]] == ["2", "1"]
    assert snapshot["runs"] == snapshot["budget_exceeded_runs"] == 3
    snapshot["recent_runs"][0]["usage"]["models"].append("mutated")
    assert registry.snapshot()["recent_runs"][0]["usage"]["models"] == []
