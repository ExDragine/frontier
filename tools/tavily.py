import dotenv
from langchain_tavily import TavilyCrawl, TavilyExtract, TavilyMap, TavilySearch

dotenv.load_dotenv()
tavily_search = TavilySearch(
    max_results=50,
    topic="general",
)
tavily_extract = TavilyExtract(
    extract_depth="advanced", include_images=False, include_favicon=False, format="markdown"
)
tavily_crawl = TavilyCrawl(
    max_depth=1,
    max_breadth=20,
    limit=50,
)
tavily_map = TavilyMap(
    max_depth=2,
    max_breadth=20,
    limit=50,
)
