from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from utils.memory import MemoryStore

memory = MemoryStore()


@tool(response_format="content")
async def get_memory(query: str, user_id: Annotated[str, InjectedState("user_id")]):
    """
    检索之前的记忆，返回与查询最相关的内容。
    基于相似度搜索和最大边际相关性（MMR）搜索。
    Args:
        query (str): 用户的查询内容
    Returns:
        str: 最相关的记忆内容与多样化相关记忆
    """
    result = await memory.similarity_search(user_id, query, {})
    mmr_result = await memory.mmr_search(user_id, query, 3, {})
    return "最相似的记忆:\n" + result + "\n多样化相关记忆:\n" + mmr_result
