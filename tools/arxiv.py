import json

from langchain.tools import tool
from langchain_community.document_loaders import ArxivLoader


@tool(response_format="content")
async def get_arxiv_paper_info(query: str):
    """获取arxiv论文信息
    Args:
        query (str): 查询关键词
    Returns:
        提取的信息
    """
    loader = ArxivLoader(query)
    docs = loader.load()
    return json.dumps(docs, indent=4, ensure_ascii=False)
