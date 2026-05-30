import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")


class AgentQueueFullError(RuntimeError):
    def __init__(self, thread_id: str, maxsize: int):
        super().__init__(f"Agent queue for {thread_id} is full (maxsize={maxsize})")
        self.thread_id = thread_id
        self.maxsize = maxsize


@dataclass(slots=True)
class _QueuedJob:
    run: Callable[[], Awaitable[object]]
    future: asyncio.Future


@dataclass(slots=True)
class _ThreadQueueState:
    queue: asyncio.Queue[_QueuedJob]
    worker_task: asyncio.Task | None = None
    last_used: float = field(default_factory=time.monotonic)


class AgentQueueManager:
    def __init__(
        self,
        *,
        maxsize: int = 5,
        idle_ttl_seconds: float = 1800.0,
        job_timeout_seconds: float = 900.0,
    ) -> None:
        self.maxsize = maxsize
        self.idle_ttl_seconds = idle_ttl_seconds
        self.job_timeout_seconds = job_timeout_seconds
        self._states: dict[str, _ThreadQueueState] = {}
        self._states_lock = asyncio.Lock()

    async def submit(self, thread_id: object, run: Callable[[], Awaitable[T]]) -> T:
        key = str(thread_id)
        loop = asyncio.get_running_loop()
        future: asyncio.Future[T] = loop.create_future()
        state = await self._get_state(key)
        state.last_used = time.monotonic()
        try:
            state.queue.put_nowait(_QueuedJob(run=run, future=future))
        except asyncio.QueueFull as exc:
            raise AgentQueueFullError(key, self.maxsize) from exc
        if state.worker_task is None or state.worker_task.done():
            state.worker_task = asyncio.create_task(self._worker(key, state))
        return await future

    async def _get_state(self, key: str) -> _ThreadQueueState:
        async with self._states_lock:
            state = self._states.get(key)
            if state is None:
                state = _ThreadQueueState(queue=asyncio.Queue(maxsize=self.maxsize))
                self._states[key] = state
            return state

    async def _worker(self, key: str, state: _ThreadQueueState) -> None:
        while True:
            try:
                job = await asyncio.wait_for(state.queue.get(), timeout=self.idle_ttl_seconds)
            except TimeoutError:
                async with self._states_lock:
                    if state.queue.empty() and self._states.get(key) is state:
                        self._states.pop(key, None)
                        return
                continue

            state.last_used = time.monotonic()
            try:
                result = await asyncio.wait_for(job.run(), timeout=self.job_timeout_seconds)
            except asyncio.CancelledError:
                # Python 3.9+ CancelledError is NOT an Exception subclass.
                # We must resolve the pending future before re-raising, or
                # the caller that awaits submit() will hang forever.
                if not job.future.done():
                    job.future.set_exception(
                        RuntimeError(f"Agent queue worker for {key} cancelled during job execution")
                    )
                raise
            except Exception as exc:
                if not job.future.done():
                    job.future.set_exception(exc)
            else:
                if not job.future.done():
                    job.future.set_result(result)
            finally:
                state.queue.task_done()

    async def aclose(self) -> None:
        """Shut down all worker tasks, resolving any pending futures first."""
        async with self._states_lock:
            tasks = [(key, state) for key, state in self._states.items() if state.worker_task is not None]
            self._states.clear()

        # Resolve any pending futures to prevent callers from hanging
        for _key, state in tasks:
            while not state.queue.empty():
                try:
                    job = state.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if not job.future.done():
                    job.future.set_exception(
                        RuntimeError("Agent queue shutting down — job discarded")
                    )
                state.queue.task_done()

        # Cancel workers with timeout guard
        worker_tasks = [t for _, state in tasks if (t := state.worker_task) is not None]
        for task in worker_tasks:
            task.cancel()
        for task in worker_tasks:
            with contextlib.suppress(asyncio.CancelledError, TimeoutError):
                await asyncio.wait_for(task, timeout=10.0)

    def queue_size(self, thread_id: object) -> int:
        state = self._states.get(str(thread_id))
        return 0 if state is None else state.queue.qsize()
