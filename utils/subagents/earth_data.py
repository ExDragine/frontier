"""Compiled subagent for read-only textual earth and weather data."""

import datetime
import zoneinfo
from collections.abc import Sequence
from typing import Any

from deepagents import CompiledSubAgent
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

from utils.configs import EnvConfig
from utils.llm_factory import create_llm

EARTH_DATA_SUBAGENT_NAME = "earth-data-agent"
_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")


def build_earth_data_subagent(tools: Sequence[Any]) -> CompiledSubAgent:
    """Build a query-only compiled subagent for textual earth and weather data."""
    model = create_llm(
        model=EnvConfig.BASIC_MODEL,
        provider=EnvConfig.BASIC_MODEL_PROVIDER,
        streaming=False,
        max_retries=2,
        timeout=300,
    )
    now = datetime.datetime.now(tz=_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S %Z")
    runnable = create_agent(
        model=model,
        tools=list(tools),
        system_prompt=f"""你是只读的地球与气象数据查询专员。当前时间是 {now}。

只处理工具能够回答的文本数据查询，例如中国地震、USGS 重大地震、雷达支持地区和火星天气：
- 必须调用合适的工具取得数据，不得凭记忆编造时效性事实。
- 只返回简洁结论和必要的时间、地点、震级等依据。
- 只返回最终结论，不返回中间工具调用过程或大段原始数据。
- 不执行平台写操作，不生成或发送图片，也不处理超出工具范围的普通问答。
- 工具没有结果或失败时如实说明，不自行补全。
""",
        middleware=[ToolRetryMiddleware(), ModelRetryMiddleware()],
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    return CompiledSubAgent(
        name=EARTH_DATA_SUBAGENT_NAME,
        description=(
            "查询只返回文本的地球与气象数据，包括中国地震、USGS 月度重大地震、"
            "中国雷达支持地区和火星天气。此类查询应委托本代理；雷达图、风图等图片仍由主代理处理。"
        ),
        runnable=runnable,
    )
