import importlib
import pkgutil
from pathlib import Path

from langchain_core.tools import BaseTool

from .mcp_client import mcp_get_tools_async

# 跳过不应暴露给 Agent 的模块
_EXCLUDED_MODULES = {"__init__", "mcp_client"}

_DOMAIN_GROUPS = ("astro", "earth", "memory", "divination", "external")
_RESTRICTED_GROUPS = ("restricted",)
_ALL_TOOL_GROUPS = ("main", *_DOMAIN_GROUPS, *_RESTRICTED_GROUPS)

# PTC is reserved for side-effect-free, text/structured queries. Artifact
# tools and tools with unknown or mutating behavior remain regular Agent tools
# so their ToolMessage metadata, retries, and UniMessage artifacts are kept.
_PTC_READ_ONLY_MODULES = {
    "comet",
    "deepseek_balance",
    "earthquake",
    "iching",
    "radar",
    "rocket",
    "space_weather",
    "tarot",
    "weather",
}
_PTC_READ_PREFIXES = {
    "milky_file": ("get_",),
    "milky_friend": ("get_",),
    "milky_group": ("get_",),
    "milky_message": ("get_",),
    "milky_system": ("get_",),
    "scheduled_task": ("list_",),
}

_TOOL_MODULE_GROUPS = {
    "adapter": "main",
    "milky_file": "main",
    "milky_friend": "main",
    "milky_group": "main",
    "milky_message": "main",
    "milky_system": "main",
    "deepseek_balance": "main",
    "reminder": "main",
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
    dict[str, dict[str, str]],
]:
    """扫描 tools 包，收集所有被 @tool 装饰的函数。"""
    tools_dir = Path(__file__).parent
    grouped_tools: dict[str, list[BaseTool]] = {group: [] for group in _ALL_TOOL_GROUPS}
    tool_metadata: dict[str, dict[str, str]] = {}

    for mod_info in pkgutil.iter_modules([str(tools_dir)]):
        if mod_info.name in _EXCLUDED_MODULES:
            continue
        module = importlib.import_module(f".{mod_info.name}", package=__package__)
        found = [obj for obj in vars(module).values() if isinstance(obj, BaseTool)]
        group = _TOOL_MODULE_GROUPS.get(mod_info.name, "main")
        grouped_tools[group].extend(found)
        for tool_obj in found:
            tool_metadata[tool_obj.name] = {"module": mod_info.name, "group": group}

    return grouped_tools, tool_metadata


class ModuleTools:
    def __init__(self):
        (
            self.subagent_tools,
            self.tool_metadata,
        ) = _discover_tools()

        # 记忆与其他领域工具都由主 Agent 按需调用，
        # 再按 direct / PTC 执行通道分流。
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

    @property
    def ptc_tools(self):
        """Return one-shot, read-only tools exposed only through PTC."""
        return [tool for tool in self.subagent_tools["main"] if self._uses_ptc(tool)]

    @property
    def direct_tools(self):
        """Return regular Agent tools, including network search and page reading."""
        return [tool for tool in self.subagent_tools["main"] if not self._uses_ptc(tool)] + self.mcp_tools

    @property
    def main_tools(self):
        return [*self.subagent_tools["main"], *self.mcp_tools]

    def _uses_ptc(self, tool: BaseTool) -> bool:
        if getattr(tool, "response_format", None) != "content":
            return False
        module = self.tool_metadata.get(tool.name, {}).get("module", "")
        if module in _PTC_READ_ONLY_MODULES:
            return True
        return tool.name.startswith(_PTC_READ_PREFIXES.get(module, ()))

_AGENT_TOOLS = None


def __getattr__(name):
    if name == "agent_tools":
        global _AGENT_TOOLS
        if _AGENT_TOOLS is None:
            _AGENT_TOOLS = ModuleTools()
        return _AGENT_TOOLS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
