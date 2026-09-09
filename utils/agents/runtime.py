"""Conversation identity and serialization primitives."""

import asyncio
import hashlib
import inspect
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast


def conversation_workspace_key(user_id: str | int, group_id: int | None) -> str:
    """Return a filesystem-safe key that cannot collide across chat scopes."""
    if group_id is not None:
        return f"group-{group_id}"
    normalized_user_id = str(user_id)
    if normalized_user_id.isascii() and normalized_user_id.isdecimal():
        return f"dm-{normalized_user_id}"
    digest = hashlib.sha256(normalized_user_id.encode("utf-8")).hexdigest()
    return f"dm-h-{digest}"


def agent_thread_id(user_id: str, group_id: int | None) -> uuid.UUID:
    scope = f"group:{group_id}:user:{user_id}" if group_id is not None else f"dm:{user_id}"
    return uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=scope)


@dataclass
class _LockEntry:
    lock: asyncio.Lock
    users: int = 0


_agent_locks: dict[tuple[asyncio.AbstractEventLoop, str], _LockEntry] = {}


async def run_serialized(
    thread_id: str,
    operation: Awaitable | Callable[[], Awaitable],
    *,
    timeout: float | None = None,
):
    """Serialize a scope, counting queue time in the optional deadline.

    A factory avoids creating work that might be cancelled while still queued.
    Idle entries are released, and locks are never reused across event loops.
    """
    key = (asyncio.get_running_loop(), str(thread_id))
    entry = _agent_locks.setdefault(key, _LockEntry(asyncio.Lock()))
    entry.users += 1
    started = False
    try:
        async with asyncio.timeout(timeout):
            async with entry.lock:
                started = True
                awaitable = operation() if callable(operation) else operation
                return await cast(Awaitable[Any], awaitable)
    finally:
        if not started and inspect.iscoroutine(operation):
            operation.close()
        entry.users -= 1
        if not entry.users:
            _agent_locks.pop(key, None)
