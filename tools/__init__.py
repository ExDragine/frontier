import importlib
import pkgutil
from pathlib import Path

from langchain.tools import BaseTool

from .mcp_client import mcp_get_tools

# 跳过不应暴露给 Agent 的模块
_EXCLUDED_MODULES = {"__init__", "mcp_client", "artifact_bridge"}

# 这些模块的工具归入 web_tools 分组
_WEB_TOOL_MODULES = {"tavily"}

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
    "tavily": "research",
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
    "iching": "divination",
    "tarot": "divination",
}


def _empty_tool_groups() -> dict[str, list[BaseTool]]:
    return {group: [] for group in _ALL_TOOL_GROUPS}


def _discover_tools() -> tuple[list[BaseTool], list[BaseTool], dict[str, list[BaseTool]]]:
    """扫描 tools 包，收集所有被 @tool 装饰的函数。"""
    tools_dir = Path(__file__).parent
    local_tools: list[BaseTool] = []
    web_tools: list[BaseTool] = []
    grouped_tools = _empty_tool_groups()

    for mod_info in pkgutil.iter_modules([str(tools_dir)]):
        if mod_info.name in _EXCLUDED_MODULES:
            continue
        module = importlib.import_module(f".{mod_info.name}", package=__package__)
        found = [obj for obj in vars(module).values() if isinstance(obj, BaseTool)]
        local_tools.extend(found)
        grouped_tools[_TOOL_MODULE_GROUPS.get(mod_info.name, "main")].extend(found)
        if mod_info.name in _WEB_TOOL_MODULES:
            web_tools.extend(found)

    return local_tools, web_tools, grouped_tools


class ModuleTools:
    def __init__(self):
        self._mcp_tools = None
        self.local_tools, self.web_tools, self.subagent_tools = _discover_tools()
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
