"""Conversation identity and serialization primitives."""

import asyncio
import uuid


def agent_thread_id(user_id: str, group_id: int | None) -> uuid.UUID:
    scope = f"group:{group_id}:user:{user_id}" if group_id is not None else f"dm:{user_id}"
    return uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=scope)


_agent_locks: dict[str, asyncio.Lock] = {}


async def run_serialized(thread_id: str, coro, *, timeout: float | None = None):
    """同一 conversation 内序列化 Agent 执行：同 key 互斥，不同 key 并发。"""
    key = str(thread_id)
    lock = _agent_locks.setdefault(key, asyncio.Lock())
    async with lock:
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro
