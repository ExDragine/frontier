"""Durable inbox and action journal with conditional claims and expiring leases."""

import time

from sqlalchemy import Column, Float, Index, MetaData, String, Table, Text, delete, func, select, update
from sqlalchemy.dialects.sqlite import insert

from utils.platform_event import InboundEvent

from .engine import _run_database, get_engine

metadata = MetaData()
events = Table(
    "platform_event_inbox", metadata,
    Column("key", String, primary_key=True),
    Column("bot_id", String, nullable=False),
    Column("payload", Text, nullable=False),
    Column("status", String, nullable=False),
    Column("expires", Float, nullable=False),
    Column("lease", Float, nullable=False, default=0),
    Column("updated", Float, nullable=False),
    Column("detail", Text, nullable=False, default=""),
    Column("proposal", String, nullable=False, default=""),
    Column("policy", Text, nullable=False, default=""),
    Column("checked", Float, nullable=False, default=0),
)
Index("ix_platform_event_ready", events.c.status, events.c.bot_id, events.c.updated)
actions = Table(
    "platform_event_actions", metadata,
    Column("event_key", String, primary_key=True),
    Column("action", String, nullable=False),
    Column("status", String, nullable=False),
    Column("updated", Float, nullable=False),
)


class PlatformEventStore:
    def __init__(self, engine=None):
        self.engine = engine if engine is not None else get_engine()

    async def initialize(self):
        await _run_database(self.engine, metadata.create_all, self.engine)

    async def put(self, event: InboundEvent, status: str, ttl: int, max_pending: int) -> bool:
        def write():
            with self.engine.begin() as conn:
                conn.exec_driver_sql("BEGIN IMMEDIATE")
                if status == "pending":
                    count = conn.scalar(select(func.count()).select_from(events).where(
                        events.c.status.in_(("pending", "evaluating", "executing")),
                    ))
                    selected = "deferred" if count >= max_pending else status
                else:
                    selected = status
                result = conn.execute(insert(events).values(
                    key=event.key, bot_id=event.bot_id, payload=event.model_dump_json(),
                    status=selected, expires=min(event.received_at, event.occurred_at) + ttl,
                    lease=0, updated=time.time(), detail="queue_full" if selected != status else "",
                ).on_conflict_do_nothing())
                return result.rowcount == 1
        return await _run_database(self.engine, write)

    async def recover(self):
        def write():
            now = time.time()
            with self.engine.begin() as conn:
                stale = select(events.c.key).where(events.c.status == "executing", events.c.lease < now)
                conn.execute(update(actions).where(actions.c.event_key.in_(stale)).values(status="unknown", updated=now))
                conn.execute(update(events).where(events.c.status == "executing", events.c.lease < now).values(
                    status="unknown", detail="execution_interrupted", updated=now,
                ))
                conn.execute(update(events).where(events.c.status == "evaluating", events.c.lease < now).values(
                    status="pending", updated=now,
                ))
                conn.execute(update(events).where(
                    events.c.status.in_(("pending", "recorded", "deferred")), events.c.expires <= now,
                ).values(status="expired", updated=now))
        await _run_database(self.engine, write)

    async def claim(self, bot_ids: list[str], lease_seconds: int):
        def write():
            with self.engine.begin() as conn:
                key = conn.scalar(select(events.c.key).where(
                    events.c.status == "pending", events.c.bot_id.in_(bot_ids), events.c.expires > time.time(),
                ).order_by(events.c.updated).limit(1))
                if key is None:
                    return None
                row = conn.execute(update(events).where(events.c.key == key, events.c.status == "pending").values(
                    status="evaluating", lease=time.time() + lease_seconds, updated=time.time(),
                ).returning(events)).mappings().first()
                return dict(row) if row else None
        return await _run_database(self.engine, write)

    async def finish(self, key: str, status: str, detail: str = "", proposal: str = "", policy: str = ""):
        def write():
            with self.engine.begin() as conn:
                conn.execute(update(events).where(events.c.key == key).values(
                    status=status, detail=detail, proposal=proposal, policy=policy, updated=time.time(), lease=0,
                ))
                conn.execute(update(actions).where(actions.c.event_key == key).values(status=status, updated=time.time()))
        await _run_database(self.engine, write)

    async def begin_action(self, key: str, action: str, policy: str) -> bool:
        def write():
            with self.engine.begin() as conn:
                changed = conn.execute(update(events).where(
                    events.c.key == key, events.c.status == "evaluating", events.c.expires > time.time(),
                ).values(status="executing", proposal=action, policy=policy, updated=time.time()))
                if changed.rowcount != 1:
                    return False
                result = conn.execute(insert(actions).values(
                    event_key=key, action=action, status="executing", updated=time.time(),
                ).on_conflict_do_nothing())
                if result.rowcount != 1:
                    conn.execute(update(events).where(events.c.key == key).values(status="unknown"))
                    return False
                return True
        return await _run_database(self.engine, write)

    async def recent(self, limit: int = 20):
        def read():
            with self.engine.connect() as conn:
                return [dict(row) for row in conn.execute(
                    select(events).order_by(events.c.updated.desc()).limit(limit),
                ).mappings()]
        return await _run_database(self.engine, read)

    async def unknown(self, bot_ids: list[str], limit: int = 20):
        def read():
            with self.engine.connect() as conn:
                return [dict(row) for row in conn.execute(select(events).where(
                    events.c.status == "unknown", events.c.bot_id.in_(bot_ids),
                ).order_by(events.c.checked).limit(limit)).mappings()]
        return await _run_database(self.engine, read)

    async def mark_checked(self, key: str):
        def write():
            with self.engine.begin() as conn:
                conn.execute(update(events).where(events.c.key == key).values(checked=time.time()))
        await _run_database(self.engine, write)

    async def cleanup(self, days: int):
        def write():
            with self.engine.begin() as conn:
                old = select(events.c.key).where(
                    events.c.status.in_(("recorded", "deferred", "expired", "shadow", "succeeded", "resolved")),
                    events.c.expires < time.time(), events.c.updated < time.time() - days * 86400,
                )
                conn.execute(delete(actions).where(actions.c.event_key.in_(old)))
                conn.execute(delete(events).where(events.c.key.in_(old)))
        await _run_database(self.engine, write)

    async def requeue(self, key: str) -> bool:
        """Explicit operator retry is allowed only before any write was attempted."""
        def write():
            with self.engine.begin() as conn:
                result = conn.execute(update(events).where(
                    events.c.key == key, events.c.status.in_(("recorded", "deferred", "shadow")),
                    events.c.expires > time.time(),
                    ~events.c.key.in_(select(actions.c.event_key)),
                ).values(status="pending", updated=time.time()))
                return result.rowcount == 1
        return await _run_database(self.engine, write)
