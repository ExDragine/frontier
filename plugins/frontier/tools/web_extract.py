from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from langchain_core.tools import tool
from langchain_docling.loader import DoclingLoader, ExportType
from langchain_tavily import TavilyCrawl, TavilyExtract, TavilyMap, TavilySearch


@tool(response_format="content")
async def get_web_extract(url: str) -> str:
    """
    从网页或PDF链接中提取信息

    Args:
        url: 网页URL或PDF链接

    Returns:
        提取的信息
    """
    if not url:
        return "❌ URL不能为空"

    loader = DoclingLoader(
        url,
        export_type=ExportType.MARKDOWN,
        chunker=HybridChunker(
            tokenizer=HuggingFaceTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        ),
    )
    docs = loader.load()
    texts = "".join([doc.page_content for doc in docs])
    return texts


tavily_search = TavilySearch(
    max_results=5,
    topic="general",
)
tavily_extract = TavilyExtract(
    extract_depth="advanced", include_images=False, include_favicon=False, format="markdown"
)
tavily_crawl = tool = TavilyCrawl(
    max_depth=1,
    max_breadth=20,
    limit=50,
)
tavily_map = tool = TavilyMap(
    max_depth=2,
    max_breadth=20,
    limit=50,
)
