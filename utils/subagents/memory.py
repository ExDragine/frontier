"""Compiled subagent for scoped chat-history retrieval."""

import datetime
import zoneinfo
from collections.abc import Sequence
from typing import Any

from deepagents import CompiledSubAgent
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

from utils.configs import EnvConfig
from utils.llm_factory import create_llm

MEMORY_SUBAGENT_NAME = "memory-agent"
_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")


def build_memory_subagent(tools: Sequence[Any]) -> CompiledSubAgent:
    """Build a minimal compiled subagent with access only to memory tools."""
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
        system_prompt=f"""你是聊天记忆检索专员。当前时间是 {now}。

你的唯一职责是检索、核对和总结当前会话的历史记录：
- 优先使用 search_messages 查询本地记忆；没有筛选条件时它会返回最近记录。
- 只有本地记忆不足，或必须按 QQ 消息序列继续翻页时，才使用 get_history_messages。
- 需要概览或总结时，自行组合关键词、时间、角色和分页条件，最多读取 1000 条记录；按页提炼，避免重复拉取。
- 不得猜测、补写或把没有检索到的信息当成事实；没有依据就明确说未找到。
- 返回简洁结论，并列出关键依据。依据必须保留时间、用户、角色和 msg_id；达到读取上限时说明结果可能不完整。
- 只返回最终结论，不返回中间工具调用过程或大段原始记录。
- 只回答主 Agent 委托的记忆问题，不处理普通问答，也不尝试调用任何其他能力。
""",
        middleware=[ToolRetryMiddleware(), ModelRetryMiddleware()],
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    return CompiledSubAgent(
        name=MEMORY_SUBAGENT_NAME,
        description=(
            "检索、核对或总结当前群聊/私聊的历史消息。用户询问之前说过什么、过去的决定、"
            "历史数据或需要基于聊天记录继续分析时，必须委托此代理。"
        ),
        runnable=runnable,
    )
