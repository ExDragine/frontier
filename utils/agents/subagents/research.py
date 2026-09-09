"""Compiled subagent for bounded web research and fact checking."""

from collections.abc import Sequence
from typing import Any

from deepagents import CompiledSubAgent
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    ToolCallLimitMiddleware,
)

from utils.configs import EnvConfig
from utils.llm_factory import create_llm

from ..tool_errors import tool_error_middleware

RESEARCH_SUBAGENT_NAME = "research-agent"


def build_research_subagent(tools: Sequence[Any]) -> CompiledSubAgent:
    """Build a query-only research agent with strict call budgets."""
    model = create_llm(
        model=EnvConfig.BASIC_MODEL,
        provider=EnvConfig.BASIC_MODEL_PROVIDER,
        streaming=False,
        max_retries=2,
        timeout=300,
        tags=["frontier:research"],
    )
    middleware: list[Any] = [
        tool_error_middleware(all_read_only=True),
        ToolCallLimitMiddleware(run_limit=6, exit_behavior="end"),
        ModelCallLimitMiddleware(run_limit=5, exit_behavior="end"),
        ModelRetryMiddleware(),
    ]
    runnable = create_agent(
        model=model,
        tools=list(tools),
        system_prompt="""你是受限预算的网络研究与事实核验专员。

按固定循环工作：提出搜索词、搜索、读取最相关来源、核对冲突，证据足够后立即停止。
- 最多进行 6 次工具调用；通常使用 1 至 3 个搜索词并读取不超过 5 个页面。
- 默认选择一个搜索后端完成任务；只在失败、结果不足或需要交叉核验时切换 Exa / Tavily，避免重复消耗配额。
- Tavily 中优先使用 search 与 extract；只在需要站点结构时使用 map / crawl，用户明确要求深度研究时才使用 research。
- 优先官方、一手资料和明确标注日期的来源；时效性事实必须核对事件日期，而非只看发布日期。
- 重要结论尽量由两个独立来源支持；无法交叉核验时明确降低置信度。
- 遇到 429 或搜索服务限流后不得继续重试，直接使用已有证据完成报告。
- 不执行平台写操作，不生成媒体，不处理当前聊天记忆或本地文件。
- 最终只返回：简洁结论、关键证据、来源标题与 URL、不确定性。不得虚构来源或链接。
""",
        middleware=middleware,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    return CompiledSubAgent(
        name=RESEARCH_SUBAGENT_NAME,
        description=(
            "使用 Exa / Tavily 对时效性、小众或需要来源支持的问题进行受限网络搜索、"
            "网页读取和交叉核验。"
            "需要查找最新资料、比较多个来源或提供可追溯链接时委托本代理；一次性本地/API 查询不要委托。"
        ),
        runnable=runnable,
    )
