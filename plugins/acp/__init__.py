"""ACP integration with a lightweight, lazily loaded public API."""

from importlib import import_module
from typing import Any

_EXPORTS = {
    "AcpAgent": (".agent", "AcpAgent"),
    "AcpAgentConfig": (".service", "AcpAgentConfig"),
    "AcpAgentService": (".service", "AcpAgentService"),
    "AcpArtifact": (".service", "AcpArtifact"),
    "AcpConfigurationError": (".service", "AcpConfigurationError"),
    "AcpInputMedia": (".service", "AcpInputMedia"),
    "AcpRunResult": (".service", "AcpRunResult"),
    "AcpUnavailableError": (".service", "AcpUnavailableError"),
    "FrontierAcpServer": (".server", "FrontierAcpServer"),
    "FrontierAcpV2Server": (".server_v2", "FrontierAcpV2Server"),
    "acp_service": (".service", "acp_service"),
    "load_acp_config": (".service", "load_acp_config"),
    "run_frontier_acp_server": (".server", "run_frontier_acp_server"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute = _EXPORTS[name]
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)

# NoneBot injects __plugin__ before executing a plugin package. Ordinary imports
# (including the standalone stdio server) must not register QQ commands.
if globals().get("__plugin__") is not None:
    from nonebot import require

    require("nonebot_plugin_alconna")
    require("nonebot_plugin_apscheduler")

    from . import commands as commands
    from . import lifecycle as lifecycle
