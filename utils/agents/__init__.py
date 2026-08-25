"""Frontier Agent public API with lazy imports for lightweight protocol startup."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "AcpAgent": (".acp", "AcpAgent"),
    "FrontierAgentState": (".cognitive", "FrontierAgentState"),
    "FrontierCognitive": (".cognitive", "FrontierCognitive"),
    "ProgressEvent": (".progress", "ProgressEvent"),
    "ProgressReporter": (".progress", "ProgressReporter"),
    "agent_thread_id": (".runtime", "agent_thread_id"),
    "conversation_workspace_key": (".runtime", "conversation_workspace_key"),
    "assistant_agent": (".assistant", "assistant_agent"),
    "run_serialized": (".runtime", "run_serialized"),
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        module_name, attribute = _EXPORTS[name]
        value = getattr(import_module(module_name, __name__), attribute)
        globals()[name] = value
        return value
    try:
        return import_module(f".{name}", __name__)
    except ModuleNotFoundError as exc:
        if exc.name == f"{__name__}.{name}":
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
        raise


__all__ = list(_EXPORTS)
