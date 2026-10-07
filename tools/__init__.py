import importlib
import pkgutil
from pathlib import Path

from langchain_core.tools import BaseTool

from .mcp_client import mcp_get_tools_async

# 跳过不应暴露给 Agent 的模块
# mcp_client 只负责按 mcp.json 异步加载外部 MCP 工具（经 ModuleTools.initialize
# 写入 external 组），其模块本身不定义任何 @tool。
_EXCLUDED_MODULES = {"__init__", "mcp_client"}

_DOMAIN_GROUPS = ("astro", "earth", "memory", "divination", "external")
_RESTRICTED_GROUPS = ("restricted",)
_ALL_TOOL_GROUPS = ("main", *_DOMAIN_GROUPS, *_RESTRICTED_GROUPS)

# Preserve the former PTC query classification for direct-tool error handling.
# Artifact-producing tools and unknown modules are deliberately excluded.
_READ_ONLY_MODULES = {
    "comet", "deepseek_balance", "earthquake", "iching", "radar",
    "rocket", "space_weather", "tarot", "weather",
}
_READ_ONLY_PREFIXES = {
    "milky_file": ("get_",),
    "milky_friend": ("get_",),
    "milky_group": ("get_",),
    "milky_message": ("get_",),
    "milky_system": ("get_",),
    "scheduled_task": ("list_",),
}

# Platform tools stay in the legacy ``main`` group during the migration, but
# are tagged here so neutral runtime callers can opt into only the tools their
# adapter can actually execute.  An empty capability set deliberately means
# "legacy mode" and keeps ACP, scheduled tasks, and existing QQ callers
# behavior-compatible.
_MODULE_REQUIRED_CAPABILITIES: dict[str, frozenset[str]] = {
    "adapter": frozenset({"qq:message"}),
    "milky_file": frozenset({"qq:file"}),
    "milky_friend": frozenset({"qq:friend"}),
    "milky_group": frozenset({"qq:group"}),
    "milky_message": frozenset({"qq:message"}),
    "milky_system": frozenset({"qq:system"}),
}
_BROAD_QQ_CAPABILITIES = frozenset({"qq", "platform:qq", "qq:tools"})

_TOOL_MODULE_GROUPS = {
    "adapter": "main",
    "milky_file": "main",
    "milky_friend": "main",
    "milky_group": "main",
    "milky_message": "main",
    "milky_system": "main",
    "deepseek_balance": "main",
    "reminder": "main",
    "scheduled_task": "main",
    "aurora": "astro",
    "comet": "astro",
    "heavens_above": "astro",
    "rocket": "astro",
    "satellite": "astro",
    "space_weather": "astro",
    "earthquake": "earth",
    "ens_normal": "restricted",
    "ens_professional": "restricted",

    "radar": "earth",
    "weather": "earth",
    "paint": "main",
    "video": "main",
    "memory": "memory",
    "NRCmerchant_current": "main",
    "webpage_screenshot": "restricted",
    "webpage_recording": "restricted",
    "NRCeggs_details": "main",
    "NRCeggs_groups": "main",
    "NRCevent_calendar": "main",
    "typhoon": "main",
    "iching": "divination",
    "tarot": "divination",
}


def _discover_tools() -> tuple[
    dict[str, list[BaseTool]],
    dict[str, dict[str, object]],
]:
    """扫描 tools 包，收集所有被 @tool 装饰的函数。"""
    tools_dir = Path(__file__).parent
    grouped_tools: dict[str, list[BaseTool]] = {group: [] for group in _ALL_TOOL_GROUPS}
    tool_metadata: dict[str, dict[str, object]] = {}

    for mod_info in pkgutil.iter_modules([str(tools_dir)]):
        if mod_info.name in _EXCLUDED_MODULES:
            continue
        module = importlib.import_module(f".{mod_info.name}", package=__package__)
        found = [obj for obj in vars(module).values() if isinstance(obj, BaseTool)]
        group = _TOOL_MODULE_GROUPS.get(mod_info.name, "main")
        grouped_tools[group].extend(found)
        for tool_obj in found:
            tool_metadata[tool_obj.name] = {
                "module": mod_info.name,
                "group": group,
                "platform": "qq" if mod_info.name in _MODULE_REQUIRED_CAPABILITIES else None,
                "required_capabilities": _MODULE_REQUIRED_CAPABILITIES.get(mod_info.name, frozenset()),
            }

    return grouped_tools, tool_metadata


class ModuleTools:
    def __init__(self):
        (
            self.subagent_tools,
            self.tool_metadata,
        ) = _discover_tools()

        # 记忆与其他领域工具都由主 Agent 按需调用。
        for group in ("astro", "earth", "memory", "divination"):
            self.subagent_tools["main"].extend(self.subagent_tools[group])

    @property
    def mcp_tools(self):
        return self.subagent_tools["external"]

    async def initialize(self):
        self.subagent_tools["external"] = await mcp_get_tools_async()

    @property
    def restricted_tools(self):
        return self.subagent_tools.get("restricted", [])

    def _capability_allows(self, tool: BaseTool, capabilities: frozenset[str]) -> bool:
        """Return whether a tool is available to an explicit adapter context.

        Common tools have no required capabilities and remain available to all
        platforms.  Platform tools declare a capability at module discovery
        time.  Broad QQ capabilities are useful for the legacy QQ adapter,
        while a scoped capability (for example ``qq:message``) exposes only
        that tool family.
        """

        if not capabilities:
            return True
        metadata = self.tool_metadata.get(getattr(tool, "name", ""), {})
        # _discover_tools() 为每个工具恒写入 frozenset 类型的 required_capabilities。
        required = metadata.get("required_capabilities") or frozenset()
        if not required:
            return True
        if _BROAD_QQ_CAPABILITIES & capabilities and metadata.get("platform") == "qq":
            return True
        return bool(required & capabilities)

    def _filtered_main_tools(self, capabilities: frozenset[str]) -> list[BaseTool]:
        return [tool for tool in self.subagent_tools["main"] if self._capability_allows(tool, capabilities)]

    def direct_tools_for(self, capabilities: frozenset[str]) -> list[BaseTool]:
        """Return direct tools visible in an explicit capability context."""

        return self._filtered_main_tools(capabilities) + self.mcp_tools

    @property
    def direct_tools(self):
        """Return regular Agent tools, including network search and page reading."""
        return [*self.subagent_tools["main"], *self.mcp_tools]

    def is_read_only_tool(self, tool: BaseTool) -> bool:
        """Classify registered query objects without trusting name prefixes alone."""
        if not any(tool is registered for registered in self.subagent_tools["main"]):
            return False
        if getattr(tool, "response_format", None) != "content":
            return False
        module = self.tool_metadata.get(tool.name, {}).get("module", "")
        return module in _READ_ONLY_MODULES or tool.name.startswith(_READ_ONLY_PREFIXES.get(module, ()))


_AGENT_TOOLS = None


def __getattr__(name):
    if name == "agent_tools":
        global _AGENT_TOOLS
        if _AGENT_TOOLS is None:
            _AGENT_TOOLS = ModuleTools()
        return _AGENT_TOOLS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
