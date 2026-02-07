from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from utils.configs import EnvConfig
from utils.memory import get_memory_service
from utils.memory_types import MemoryScope

memory = get_memory_service()


@tool(response_format="content")
async def get_memory(
    query: str,
    user_id: Annotated[str, InjectedState("user_id")],
    group_id: Annotated[int | None, InjectedState("group_id")] = None,
):
    """
    检索之前的记忆，返回与查询最相关的内容。
    基于用户层和群层的融合检索。
    Args:
        query (str): 用户的查询内容
    Returns:
        str: 最相关的记忆内容与多样化相关记忆
    """
    if not EnvConfig.MEMORY_ENABLED:
        return "记忆系统未启用。"

    items = await memory.retrieve_for_injection(
        query=query,
        user_id=user_id,
        group_id=group_id,
        max_items=EnvConfig.MEMORY_MAX_INJECTED_MEMORIES,
    )
    if not items:
        return "未找到相关记忆。"

    user_items = [item for item in items if item.scope == MemoryScope.USER]
    group_items = [item for item in items if item.scope == MemoryScope.GROUP]
    lines = []
    if user_items:
        lines.append("用户记忆:")
        lines.extend([f"* {item.content}" for item in user_items])
    if group_items:
        lines.append("群记忆:")
        lines.extend([f"* {item.content}" for item in group_items])
    return "\n".join(lines)
