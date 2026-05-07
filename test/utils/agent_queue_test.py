# ruff: noqa: S101

import asyncio

import pytest

from utils.agent_queue import AgentQueueFullError, AgentQueueManager


@pytest.mark.asyncio
async def test_same_thread_jobs_run_fifo():
    manager = AgentQueueManager(maxsize=4, idle_ttl_seconds=1.0, job_timeout_seconds=1.0)
    first_started = asyncio.Event()
    release_first = asyncio.Event()
    second_started = asyncio.Event()
    order = []

    async def first_job():
        order.append("first-start")
        first_started.set()
        await release_first.wait()
        order.append("first-end")
        return "first"

    async def second_job():
        order.append("second-start")
        second_started.set()
        return "second"

    first_task = asyncio.create_task(manager.submit("thread-a", first_job))
    await first_started.wait()
    second_task = asyncio.create_task(manager.submit("thread-a", second_job))
    await asyncio.sleep(0)

    assert not second_started.is_set()

    release_first.set()

    assert await first_task == "first"
    assert await second_task == "second"
    assert order == ["first-start", "first-end", "second-start"]

    await manager.aclose()


@pytest.mark.asyncio
async def test_different_threads_run_concurrently():
    manager = AgentQueueManager(maxsize=2, idle_ttl_seconds=1.0, job_timeout_seconds=1.0)
    started = []
    release = asyncio.Event()

    async def job(name):
        started.append(name)
        await release.wait()
        return name

    task_a = asyncio.create_task(manager.submit("thread-a", lambda: job("a")))
    task_b = asyncio.create_task(manager.submit("thread-b", lambda: job("b")))

    while len(started) < 2:
        await asyncio.sleep(0)

    assert set(started) == {"a", "b"}

    release.set()

    assert await task_a == "a"
    assert await task_b == "b"

    await manager.aclose()


@pytest.mark.asyncio
async def test_queue_full_rejects_extra_waiting_jobs():
    manager = AgentQueueManager(maxsize=1, idle_ttl_seconds=1.0, job_timeout_seconds=1.0)
    first_started = asyncio.Event()
    release_first = asyncio.Event()

    async def first_job():
        first_started.set()
        await release_first.wait()
        return "first"

    async def waiting_job():
        return "waiting"

    first_task = asyncio.create_task(manager.submit("thread-a", first_job))
    await first_started.wait()

    waiting_task = asyncio.create_task(manager.submit("thread-a", waiting_job))
    await asyncio.sleep(0)

    with pytest.raises(AgentQueueFullError):
        await manager.submit("thread-a", waiting_job)

    release_first.set()

    assert await first_task == "first"
    assert await waiting_task == "waiting"

    await manager.aclose()


@pytest.mark.asyncio
async def test_timed_out_job_fails_and_worker_continues():
    manager = AgentQueueManager(maxsize=2, idle_ttl_seconds=1.0, job_timeout_seconds=0.01)

    async def slow_job():
        await asyncio.sleep(1.0)
        return "slow"

    async def fast_job():
        return "fast"

    slow_task = asyncio.create_task(manager.submit("thread-a", slow_job))
    fast_task = asyncio.create_task(manager.submit("thread-a", fast_job))

    with pytest.raises(TimeoutError):
        await slow_task

    assert await fast_task == "fast"

    await manager.aclose()


@pytest.mark.asyncio
async def test_idle_worker_removes_thread_state():
    manager = AgentQueueManager(maxsize=2, idle_ttl_seconds=0.01, job_timeout_seconds=1.0)

    async def job():
        return "ok"

    assert await manager.submit("thread-a", job) == "ok"

    for _ in range(20):
        if manager.queue_size("thread-a") == 0 and "thread-a" not in manager._states:
            break
        await asyncio.sleep(0.01)

    assert "thread-a" not in manager._states

    await manager.aclose()
