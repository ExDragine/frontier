import importlib
import pkgutil
from pathlib import Path

from langchain_core.tools import BaseTool

from .mcp_client import mcp_get_tools

# 跳过不应暴露给 Agent 的模块
_EXCLUDED_MODULES = {"__init__", "mcp_client", "artifact_bridge"}

_SUBAGENT_GROUPS = ("research", "astro", "earth", "media", "memory", "divination", "external")
_ALL_TOOL_GROUPS = ("main", *_SUBAGENT_GROUPS)

_TOOL_MODULE_GROUPS = {
    "adapter": "main",
    "calculator": "main",
    "milky_file": "main",
    "milky_friend": "main",
    "milky_group": "main",
    "milky_message": "main",
    "milky_system": "main",
    "deepseek_balance": "main",
    "reminder": "main",
    "arxiv": "research",
    "bilibili": "research",
    "wikipedia": "research",
    "aurora": "astro",
    "comet": "astro",
    "heavens_above": "astro",
    "rocket": "astro",
    "satellite": "astro",
    "space_weather": "astro",
    "earthquake": "earth",
    "radar": "earth",
    "weather": "earth",
    "paint": "main",
    "video": "main",
    "memory": "memory",
    "NRCmerchant_current": "main",
    "iching": "divination",
    "tarot": "divination",
}


def _discover_tools() -> tuple[
    list[BaseTool],
    list[BaseTool],
    dict[str, list[BaseTool]],
    dict[str, dict[str, str]],
]:
    """扫描 tools 包，收集所有被 @tool 装饰的函数。"""
    tools_dir = Path(__file__).parent
    local_tools: list[BaseTool] = []
    web_tools: list[BaseTool] = []
    grouped_tools: dict[str, list[BaseTool]] = {group: [] for group in _ALL_TOOL_GROUPS}
    tool_metadata: dict[str, dict[str, str]] = {}

    for mod_info in pkgutil.iter_modules([str(tools_dir)]):
        if mod_info.name in _EXCLUDED_MODULES:
            continue
        module = importlib.import_module(f".{mod_info.name}", package=__package__)
        found = [obj for obj in vars(module).values() if isinstance(obj, BaseTool)]
        group = _TOOL_MODULE_GROUPS.get(mod_info.name, "main")
        local_tools.extend(found)
        grouped_tools[group].extend(found)
        for tool_obj in found:
            tool_metadata[tool_obj.name] = {"module": mod_info.name, "group": group}

    return local_tools, web_tools, grouped_tools, tool_metadata


class ModuleTools:
    def __init__(self):
        self._mcp_tools = None
        (
            self.local_tools,
            self.web_tools,
            self.subagent_tools,
            self.tool_metadata,
        ) = _discover_tools()
        # MCP 工具延迟加载，在 mcp_tools property 首次访问时才执行 asyncio.run()
        self.subagent_tools["main"].extend(self.web_tools)
        self.subagent_tools["main"].extend(self.subagent_tools["memory"])

        # 将所有子代理组的工具也暴露给主 Agent
        for group in ("research", "astro", "earth", "divination", "media"):
            self.subagent_tools["main"].extend(self.subagent_tools[group])

    @property
    def mcp_tools(self):
        if self._mcp_tools is None:
            self._mcp_tools = mcp_get_tools()
            self.subagent_tools["external"].extend(self._mcp_tools)
            self.subagent_tools["main"].extend(self._mcp_tools)
            for tool_obj in self._mcp_tools:
                self.tool_metadata[tool_obj.name] = {"module": "mcp", "group": "external"}
        return self._mcp_tools

    @property
    def main_tools(self):
        _ = self.mcp_tools  # 确保 MCP 工具已加载
        return self.subagent_tools["main"]

    @property
    def all_tools(self):
        return self.mcp_tools + self.local_tools


_AGENT_TOOLS = None


def __getattr__(name):
    if name == "agent_tools":
        global _AGENT_TOOLS
        if _AGENT_TOOLS is None:
            _AGENT_TOOLS = ModuleTools()
        return _AGENT_TOOLS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
