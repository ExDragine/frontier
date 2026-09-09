"""Process-local QQ sessions, pinned through delivery and isolated by bot/scope."""

import asyncio
import logging
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from utils.configs import EnvConfig, SessionConfig

from .checkpoints import BoundedMemorySaver
from .runtime import conversation_workspace_key, run_serialized

logger = logging.getLogger(__name__)


def database_message_id(bot_id: str, message_id: int) -> str:
    return f"qq:{bot_id}:message:{message_id}"


@dataclass(frozen=True, slots=True)
class SessionKey:
    bot_id: str
    peer_id: str
    group_id: int | None = None

    def __post_init__(self):
        if self.group_id is not None:
            object.__setattr__(self, "peer_id", str(self.group_id))

    @property
    def workspace(self) -> str:
        return conversation_workspace_key(self.peer_id, self.group_id)

    @property
    def prefix(self) -> str:
        return f"qq:{self.bot_id}:{self.workspace}"


@dataclass(frozen=True, slots=True)
class HistoryBoundary:
    message_id: int
    before_time: int


@dataclass(slots=True)
class SessionEntry:
    key: SessionKey
    thread_id: str
    revision: int
    settings: SessionConfig
    finished_at: float
    state: str = "idle"
    turns: int = 0
    history_cursor: int = 0
    latest_db_id: int = 0
    latest_time: int = 0
    seen: set[str] = field(default_factory=set)


@dataclass(slots=True)
class TurnLease:
    entry: SessionEntry
    boundary: HistoryBoundary
    hot: bool
    saver: BoundedMemorySaver
    run_id: str | None = None
    graph: Any = None
    config: Any = None
    final_message: Any = None
    valid_result: bool = False
    finished: bool = False
    # Binary messages are consumed live, then the generation is retired so raw
    # bytes never become long-lived hot history. DB attachment references survive.
    media_turn: bool = False
    history_tokens: int = 0
    rebuild_seconds: float = 0

    @property
    def current_id(self) -> str:
        return database_message_id(self.entry.key.bot_id, self.boundary.message_id)

    def inputs(self, messages: list[dict]) -> list[dict]:
        result = []
        for message in messages:
            identifier = message.get("id")
            if identifier == self.current_id or identifier not in self.entry.seen:
                result.append(message)
            if identifier:
                self.entry.seen.add(identifier)
        self.entry.history_cursor = self.boundary.message_id
        return result


class SessionManager:
    """Mutations run under the entry's workspace lock; busy entries are pinned.

    No manager lock is held across awaits. Idle eviction is synchronous on the
    event-loop thread and cannot race a running/awaiting-delivery lease.
    """

    def __init__(self, *, clock=time.monotonic):
        self.clock = clock
        self.saver = BoundedMemorySaver()
        self.entries: dict[SessionKey, SessionEntry] = {}
        self.metrics = Counter()
        self._cleaner: asyncio.Task | None = None

    def _drop(self, entry: SessionEntry, reason: str) -> None:
        if self.entries.get(entry.key) is not entry:
            return
        # Failed deletion remains an invalid entry for the next sweep to retry.
        entry.state = "invalidated"
        self.saver.delete_thread(entry.thread_id)
        del self.entries[entry.key]
        self.metrics[reason] += 1

    def sweep(self, settings: SessionConfig) -> None:
        for entry in list(self.entries.values()):
            if entry.state not in {"idle", "invalidated"}:
                continue
            ttl = settings.group_idle_seconds if entry.key.group_id is not None else settings.private_idle_seconds
            if entry.state == "invalidated":
                self._drop(entry, "invalidated")
            elif not settings.enabled:
                self._drop(entry, "disabled")
            elif self.clock() - entry.finished_at >= ttl:
                self._drop(entry, "expired")
        for entry in sorted(self.entries.values(), key=lambda item: item.finished_at):
            if len(self.entries) <= settings.max_sessions and self.saver.size() < settings.max_total_bytes * 0.75:
                break
            if entry.state == "idle":
                self._drop(entry, "evicted")

    def begin(self, key: SessionKey, boundary: HistoryBoundary, settings: SessionConfig, revision: int) -> TurnLease | None:  # noqa: C901
        self.sweep(settings)
        if not settings.enabled:
            return None
        entry = self.entries.get(key)
        if entry is not None:
            if entry.state != "idle":
                self.metrics["busy_fallback"] += 1
                return None
            reason = None
            if entry.revision != revision or entry.settings != settings:
                reason = "incompatible"
            elif entry.latest_db_id >= boundary.message_id or entry.latest_time >= boundary.before_time:
                reason = "snapshot_conflict"
            elif entry.turns >= settings.max_generation_turns or self.saver.size(entry.thread_id) >= settings.max_session_bytes * 0.75:
                reason = "rotated"
            if reason:
                self._drop(entry, reason)
                entry = None
        hot = entry is not None
        if entry is None:
            if len(self.entries) >= settings.max_sessions:
                idle = [item for item in self.entries.values() if item.state == "idle"]
                if idle:
                    self._drop(min(idle, key=lambda item: item.finished_at), "evicted")
            if len(self.entries) >= settings.max_sessions or self.saver.size() >= settings.max_total_bytes * 0.75:
                self.metrics["capacity_fallback"] += 1
                return None
            entry = SessionEntry(key, f"{key.prefix}:generation:{uuid.uuid4().hex}", revision, settings, self.clock())
            self.entries[key] = entry
        try:
            self.saver.register(entry.thread_id, limit=settings.max_session_bytes, total_limit=settings.max_total_bytes)
        except Exception:
            entry.state = "invalidated"
            raise
        entry.state = "running"
        self.metrics["hot_hits" if hot else "cold_starts"] += 1
        return TurnLease(entry, boundary, hot, self.saver)

    async def finish(self, lease: TurnLease, *, delivered: bool = False, content: str = "",
                     message_id: int | None = None, delivered_at: int | None = None, silent: bool = False) -> None:
        async def settle():
            entry = lease.entry
            if lease.finished or self.entries.get(entry.key) is not entry:
                return
            try:
                if not lease.valid_result or not (delivered or silent):
                    self._drop(entry, "failed")
                    return
                if delivered and lease.final_message is not None:
                    # Preserve its identity, replace content with exactly what was
                    # audited and sent. Do not append another assistant message.
                    final = lease.final_message.model_copy(update={"content": content, "additional_kwargs": {}})
                    await lease.graph.aupdate_state(lease.config, {
                        "messages": [final], "image_inputs": [], "audio_inputs": [], "video_inputs": [],
                    })
                entry.latest_db_id = max(lease.boundary.message_id, message_id or 0)
                entry.latest_time = max(lease.boundary.before_time, delivered_at or 0)
                if message_id is not None:
                    entry.seen.add(database_message_id(entry.key.bot_id, message_id))
                entry.turns += 1
                entry.finished_at = self.clock()
                entry.state = "idle"
                self.metrics["finished_turns"] += 1
                self.metrics["history_tokens"] += lease.history_tokens
                self.metrics["rebuild_milliseconds"] += int(lease.rebuild_seconds * 1000)
                if lease.media_turn:
                    self._drop(entry, "media_rotations")
                elif not EnvConfig.SESSIONS.enabled:
                    self._drop(entry, "disabled")
                elif entry.turns >= entry.settings.max_generation_turns or self.saver.size(entry.thread_id) >= entry.settings.max_session_bytes * 0.75:
                    self._drop(entry, "rotated")
                logger.info("Session settled run_id=%s hot=%s history_tokens=%s", lease.run_id, lease.hot, lease.history_tokens)
            except BaseException:
                entry.state = "invalidated"
                raise
            finally:
                lease.finished = True
                lease.graph = lease.config = lease.final_message = None

        await run_serialized(f"workspace:{lease.entry.key.workspace}", settle)

    def snapshot(self) -> dict:
        return {
            "enabled": EnvConfig.SESSIONS.enabled,
            **self.metrics, "sessions": len(self.entries), "serialized_bytes_upper_bound": self.saver.size(),
            "running": sum(entry.state == "running" for entry in self.entries.values()),
            "awaiting_delivery": sum(entry.state == "awaiting_delivery" for entry in self.entries.values()),
            "capacity_errors": self.saver.capacity_errors,
        }

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(EnvConfig.SESSIONS.cleanup_interval_seconds)
            try:
                self.sweep(EnvConfig.SESSIONS)
            except Exception:
                logger.exception("Session cleanup failed")

    def start(self):
        if self._cleaner is None or self._cleaner.done():
            self._cleaner = asyncio.create_task(self._cleanup_loop())

    async def close(self):
        if self._cleaner is not None:
            self._cleaner.cancel()
            await asyncio.gather(self._cleaner, return_exceptions=True)
            self._cleaner = None
        # Active requests own their cleanup; shutdown must not delete their writes.
        for entry in list(self.entries.values()):
            if entry.state in {"idle", "invalidated"}:
                self._drop(entry, "shutdown")


session_manager = SessionManager()
