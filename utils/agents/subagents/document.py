"""Declarative read-only subagent for workspace document analysis."""

from typing import Any

from deepagents import FilesystemPermission, SubAgent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware

from utils.configs import EnvConfig
from utils.llm_factory import create_llm

DOCUMENT_SUBAGENT_NAME = "document-agent"


def build_document_subagent() -> SubAgent:
    """Build a read-only agent that inherits the active workspace backend."""
    model = create_llm(
        model=EnvConfig.BASIC_MODEL,
        provider=EnvConfig.BASIC_MODEL_PROVIDER,
        streaming=False,
        max_retries=2,
        timeout=300,
    )
    middleware: list[Any] = [
        ToolCallLimitMiddleware(run_limit=8, exit_behavior="end"),
        ModelCallLimitMiddleware(run_limit=6, exit_behavior="end"),
    ]
    return SubAgent(
        name=DOCUMENT_SUBAGENT_NAME,
        description=(
            "定位、分段读取并总结当前会话 workspace 或 memory 中的文档和附件。"
            "用户要求阅读、比较、提取或总结本地文件时委托本代理；网络资料和媒体生成不要委托。"
        ),
        model=model,
        tools=[],
        system_prompt="""你是当前会话的只读文档分析专员。

按固定循环工作：定位文件、查看目录或搜索关键词、分段读取相关内容、核对上下文、压缩为结论。
- 只使用继承的 ls、glob、grep、read_file 等只读文件工具，最多进行 8 次工具调用。
- 优先搜索再读取相关片段；除非任务需要全文概览，不要从头无差别读取大型文件。
- 用户没有指定文件时，先在当前 workspace 和对应 /memory 路径中定位候选文件。
- 返回简洁结论、关键依据和虚拟文件路径；能确定时附带行号或片段位置。
- 文件不存在、格式无法读取或证据不足时如实说明，不得猜测缺失内容。
- 不修改或删除文件，不访问网络，不执行平台操作，也不生成媒体。
""",
        middleware=middleware,
        permissions=[FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")],
    )
