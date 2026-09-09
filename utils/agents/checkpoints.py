"""Bound the official memory saver without pruning delta-channel ancestors."""

import threading
from collections import defaultdict

from langchain_core.messages import ToolMessage
from langgraph.checkpoint.base import get_checkpoint_metadata
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from .session_errors import CheckpointCapacityExceeded


def _without_artifacts(value):
    # Artifacts belong to the current transport turn, not serialized graph memory.
    # Leave the live message untouched so the sender can still extract UniMessage.
    if isinstance(value, ToolMessage):
        return value.model_copy(update={"artifact": None})
    if isinstance(value, dict):
        return {key: _without_artifacts(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_without_artifacts(item) for item in value]
    if isinstance(value, tuple):
        if hasattr(value, "_fields"):
            return type(value)(*(_without_artifacts(item) for item in value))
        return tuple(_without_artifacts(item) for item in value)
    return value


class ArtifactSafeSerializer(JsonPlusSerializer):
    def dumps_typed(self, obj):
        return super().dumps_typed(_without_artifacts(obj))


class BoundedMemorySaver(InMemorySaver):
    """Count serialized writes conservatively; use only public saver operations.

    Replaced/duplicate writes remain charged until thread deletion. The counter is
    an upper bound on serialized payload traffic retained by a generation, not RSS.
    InMemorySaver's async methods dispatch to these sync methods exactly once.
    """

    def __init__(self):
        super().__init__(serde=ArtifactSafeSerializer())
        self._guard = threading.RLock()
        self._bytes = defaultdict(int)
        self._limits: dict[str, int] = {}
        self.total_limit = 256 * 1024 * 1024
        self.capacity_errors = 0

    def register(self, thread_id: str, *, limit: int, total_limit: int) -> None:
        with self._guard:
            self._limits[thread_id] = limit
            self.total_limit = total_limit

    def size(self, thread_id: str | None = None) -> int:
        with self._guard:
            return self._bytes.get(thread_id, 0) if thread_id is not None else sum(self._bytes.values())

    def _charge(self, thread_id: str, values) -> None:
        size = 1024 + sum(len(self.serde.dumps_typed(value)[1]) for value in values)
        limit = self._limits.get(thread_id)
        if limit is None or self.size(thread_id) + size > limit or self.size() + size > self.total_limit:
            self.capacity_errors += 1
            raise CheckpointCapacityExceeded("checkpoint storage budget exceeded")
        self._bytes[thread_id] += size

    def put(self, config, checkpoint, metadata, new_versions):
        with self._guard:
            values = checkpoint["channel_values"]
            header = {key: value for key, value in checkpoint.items() if key != "channel_values"}
            self._charge(config["configurable"]["thread_id"], [
                header, get_checkpoint_metadata(config, metadata),
                *(values[key] for key in new_versions if key in values),
            ])
            return super().put(config, checkpoint, metadata, new_versions)

    def put_writes(self, config, writes, task_id, task_path=""):
        with self._guard:
            writes = list(writes)
            self._charge(config["configurable"]["thread_id"], [value for _, value in writes])
            return super().put_writes(config, writes, task_id, task_path)

    def get_tuple(self, config):
        with self._guard:
            return super().get_tuple(config)

    def list(self, config, *, filter=None, before=None, limit=None):
        with self._guard:
            result = list(super().list(config, filter=filter, before=before, limit=limit))
        yield from result

    def get_delta_channel_history(self, *args, **kwargs):
        with self._guard:
            return super().get_delta_channel_history(*args, **kwargs)

    def delete_thread(self, thread_id):
        with self._guard:
            super().delete_thread(thread_id)
            self._bytes.pop(thread_id, None)
            self._limits.pop(thread_id, None)
