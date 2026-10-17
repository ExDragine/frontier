# ruff: noqa: S101

import asyncio
from types import SimpleNamespace

import pytest

from utils.agents.progress import collect_progress
from utils.agents.tool_errors import ToolExecutionUncertainError


class FailingProjection:
    def __init__(self, error):
        self.error = error
        self.consumed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.consumed = True
        raise self.error


def _stream(errors):
    return SimpleNamespace(**{name: FailingProjection(error) for name, error in zip(
        ("subagents", "tool_calls", "messages"), errors, strict=True,
    )})


def _warnings(caplog):
    return [record for record in caplog.records if record.name == "utils.agents.progress"]


@pytest.mark.asyncio
async def test_shared_projection_failure_logs_once_with_all_sources(caplog):
    error = ToolExecutionUncertainError("private tool text")
    stream = _stream([error] * 3)
    await collect_progress(stream, None)
    logs = _warnings(caplog)
    assert len(logs) == 1
    assert "ToolExecutionUncertainError" in logs[0].getMessage()
    assert set(logs[0].getMessage().split("projections=", 1)[1].split(",")) == {"subagents", "tool_calls", "messages"}
    assert "private tool text" not in logs[0].getMessage()
    assert all(projection.consumed for projection in vars(stream).values())


@pytest.mark.asyncio
async def test_independent_projection_failures_are_not_deduplicated_by_text(caplog):
    await collect_progress(_stream([RuntimeError("same private text") for _ in range(3)]), None)
    assert len(_warnings(caplog)) == 3
    assert all("same private text" not in record.getMessage() for record in _warnings(caplog))


@pytest.mark.asyncio
async def test_projection_deduplication_is_local_to_each_collection(caplog):
    error = RuntimeError("private")
    await asyncio.gather(collect_progress(_stream([error] * 3), None), collect_progress(_stream([error] * 3), None))
    assert len(_warnings(caplog)) == 2


@pytest.mark.asyncio
async def test_progress_diagnostics_never_stringify_exceptions(caplog):
    class UnsafeError(Exception):
        def __str__(self):
            pytest.fail("collector stringified the original exception")

    await collect_progress(_stream([UnsafeError()] * 3), None)
    assert len(_warnings(caplog)) == 1
    assert "UnsafeError" in _warnings(caplog)[0].getMessage()


@pytest.mark.asyncio
async def test_projection_cancellation_propagates_without_warning(caplog):
    with pytest.raises(asyncio.CancelledError):
        await collect_progress(_stream([asyncio.CancelledError()] * 3), None)
    assert not _warnings(caplog)


@pytest.mark.asyncio
async def test_collected_failure_is_logged_even_when_another_projection_is_cancelled(caplog):
    started = asyncio.Event()

    class WaitingProjection:
        def __aiter__(self):
            return self

        async def __anext__(self):
            started.set()
            await asyncio.Event().wait()

    error = RuntimeError("private")
    stream = _stream([error] * 3)
    stream.messages = WaitingProjection()
    task = asyncio.create_task(collect_progress(stream, None))
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(_warnings(caplog)) == 1
    assert "projections=subagents,tool_calls" in _warnings(caplog)[0].getMessage()
