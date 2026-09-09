"""Per-turn LangChain usage, without storing prompts, tool arguments or user IDs."""

import copy
import threading
import time
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import register_configure_hook

_COMPONENTS = {"main", "research", "document", "assistant", "signal"}
_TOKEN_FIELDS = ("input_tokens", "output_tokens", "total_tokens", "cache_read_tokens", "reasoning_tokens")


def _counts() -> dict[str, int]:
    return dict.fromkeys((*_TOKEN_FIELDS, "model_calls", "model_errors", "usage_reported_calls"), 0)


def _count(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


class RunUsageCallback(BaseCallbackHandler):
    """Count actual LangChain model invocations, including retries and child graphs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pending: dict[Any, tuple[str, str]] = {}
        self._tools: set[Any] = set()
        self._models: dict[tuple[str, str], dict[str, int]] = {}
        self._tool_calls = 0
        self._tool_errors = 0

    def on_chat_model_start(self, serialized, messages, *, run_id, tags=None, metadata=None, **kwargs):
        del messages, kwargs
        metadata = metadata or {}
        serialized = serialized or {}
        model = str(metadata.get("ls_model_name") or serialized.get("name") or "unknown")
        component = next(
            (tag.removeprefix("frontier:") for tag in (tags or []) if tag.removeprefix("frontier:") in _COMPONENTS),
            "other",
        )
        with self._lock:
            if run_id in self._pending:
                return
            key = (component, model)
            self._pending[run_id] = key
            self._models.setdefault(key, _counts())["model_calls"] += 1

    def _finish_model(self, run_id, response, *, failed: bool) -> None:
        with self._lock:
            key = self._pending.pop(run_id, None)
            if key is None:
                return
            counts = self._models[key]
            counts["model_errors"] += int(failed)
            generations = getattr(response, "generations", None)
            message = getattr(generations[0][0], "message", None) if generations and generations[0] else None
            usage = getattr(message, "usage_metadata", None)
            if not isinstance(usage, dict):
                return
            counts["usage_reported_calls"] += 1
            for field in ("input_tokens", "output_tokens", "total_tokens"):
                counts[field] += _count(usage.get(field))
            input_details = usage.get("input_token_details") or {}
            output_details = usage.get("output_token_details") or {}
            counts["cache_read_tokens"] += _count(input_details.get("cache_read"))
            counts["reasoning_tokens"] += _count(output_details.get("reasoning"))

    def on_llm_end(self, response, *, run_id, **kwargs):
        self._finish_model(run_id, response, failed=False)

    def on_llm_error(self, error, *, run_id, **kwargs):
        self._finish_model(run_id, kwargs.get("response"), failed=True)

    def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        with self._lock:
            if run_id not in self._tools:
                self._tools.add(run_id)
                self._tool_calls += 1

    def on_tool_end(self, output, *, run_id, **kwargs):
        with self._lock:
            if run_id in self._tools:
                self._tools.remove(run_id)
                self._tool_errors += int(getattr(output, "status", None) == "error")

    def on_tool_error(self, error, *, run_id, **kwargs):
        with self._lock:
            if run_id in self._tools:
                self._tools.remove(run_id)
                self._tool_errors += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            totals = _counts()
            models = []
            for (component, model), counts in sorted(self._models.items()):
                models.append({"component": component, "model": model, **counts})
                for field in totals:
                    totals[field] += counts[field]
            return {
                **totals,
                "usage_missing_calls": totals["model_calls"] - totals["usage_reported_calls"],
                "tool_calls": self._tool_calls,
                "tool_errors": self._tool_errors,
                "models": models,
            }


_current_usage: ContextVar[RunUsageCallback | None] = ContextVar("frontier_run_usage", default=None)
register_configure_hook(_current_usage, inheritable=True)


@contextmanager
def collect_run_usage():
    callback = RunUsageCallback()
    token = _current_usage.set(callback)
    try:
        yield callback
    finally:
        _current_usage.reset(token)


class UsageRegistry:
    """Process-lifetime totals and a bounded recent-run list for Dashboard."""

    def __init__(self, recent_limit: int = 100) -> None:
        self._lock = threading.Lock()
        self._started_at = int(time.time())
        self._recent: deque[dict[str, Any]] = deque(maxlen=recent_limit)
        self._totals = {**_counts(), "tool_calls": 0, "tool_errors": 0, "usage_missing_calls": 0}
        self._runs = 0
        self._budget_exceeded_runs = 0

    def record(self, *, run_id: str, status: str, error_code: str | None, duration: float, usage: dict) -> None:
        with self._lock:
            self._runs += 1
            self._budget_exceeded_runs += int(error_code == "budget_exceeded")
            for field in self._totals:
                self._totals[field] += usage[field]
            self._recent.append({
                "run_id": run_id, "status": status, "error_code": error_code,
                "duration_seconds": round(duration, 3), "finished_at": int(time.time()), "usage": copy.deepcopy(usage),
            })

    def snapshot(self, *, include_recent: bool = True) -> dict[str, Any]:
        with self._lock:
            result = {
                "since": self._started_at, "runs": self._runs,
                "budget_exceeded_runs": self._budget_exceeded_runs, **self._totals,
            }
            if include_recent:
                result["recent_runs"] = copy.deepcopy(list(reversed(self._recent)))
            return result


usage_registry = UsageRegistry()
