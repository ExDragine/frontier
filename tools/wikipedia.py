from langchain.tools import tool
from langchain_community.document_loaders import WikipediaLoader


@tool(response_format="content")
async def get_wikipedia_pages(keyword: str):
    """
    获取维基百科页面
    Args:
        keyword: 关键词
    Returns:
        references: 维基百科页面
    """
    docs = WikipediaLoader(query=keyword, load_max_docs=3).load()
    references = ""
    for doc in docs:
        references += f"Title: {doc.metadata['title']}\n"
        references += f"URL: {doc.metadata['source']}\n"
        references += f"Content: {doc.page_content}\n\n"
    return references.strip() if references else "No relevant information found."
