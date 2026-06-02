# ruff: noqa: S101

import types


class DummyTool:
    def __init__(self, name: str, description: str = "", args: dict | None = None):
        self.name = name
        self.description = description
        self.args = args or {}


def test_bm25_search_matches_chinese_and_english_tool_descriptions():
    from utils.tool_search import ToolMetadata, ToolSearchConfig, ToolSearchIndex

    weather = DummyTool("get_china_earthquake", "查询中国地震速报和震中信息")
    arxiv = DummyTool("get_arxiv_paper_info", "Search arXiv papers by query", {"query": {"type": "string"}})
    index = ToolSearchIndex(
        [
            ToolMetadata(tool=weather, module="earthquake", group="earth"),
            ToolMetadata(tool=arxiv, module="arxiv", group="research"),
        ],
        config=ToolSearchConfig(semantic_enabled=False, top_k=2),
    )

    assert [item.tool.name for item in index.search("帮我查一下今天中国地震")] == ["get_china_earthquake"]
    assert [item.tool.name for item in index.search("find an arxiv paper about transformers")] == [
        "get_arxiv_paper_info"
    ]


def test_semantic_failure_falls_back_to_bm25():
    from utils.tool_search import ToolMetadata, ToolSearchConfig, ToolSearchIndex

    class BrokenEmbeddings:
        def embed_documents(self, _docs):
            raise RuntimeError("embedding unavailable")

    tool = DummyTool("aurora_live", "极光实时监控 aurora forecast")
    index = ToolSearchIndex(
        [ToolMetadata(tool=tool, module="aurora", group="astro")],
        config=ToolSearchConfig(semantic_enabled=True),
        embeddings=BrokenEmbeddings(),
    )

    assert index.semantic_available is False
    assert [item.tool.name for item in index.search("aurora forecast")] == ["aurora_live"]


def test_hybrid_scores_dedupe_and_rank_stably():
    from utils.tool_search import ToolMetadata, ToolSearchConfig, ToolSearchIndex

    class FakeEmbeddings:
        def embed_documents(self, docs):
            return [[1.0, 0.0] if "space station" in doc else [0.0, 1.0] for doc in docs]

        def embed_query(self, _query):
            return [1.0, 0.0]

    station = DummyTool("station_location", "space station pass and satellite observation")
    tarot = DummyTool("tarot_reading", "tarot reading cards")
    index = ToolSearchIndex(
        [
            ToolMetadata(tool=tarot, module="tarot", group="divination"),
            ToolMetadata(tool=station, module="heavens_above", group="astro"),
        ],
        config=ToolSearchConfig(semantic_enabled=True, bm25_weight=0.5, vector_weight=0.5, top_k=2),
        embeddings=FakeEmbeddings(),
    )

    results = index.search("今晚能不能看到空间站")

    assert [item.tool.name for item in results] == ["station_location", "tarot_reading"]
    assert len({item.tool.name for item in results}) == len(results)


def test_expanded_search_uses_expanded_top_k():
    from utils.tool_search import ToolMetadata, ToolSearchConfig, ToolSearchIndex

    tools = [
        ToolMetadata(tool=DummyTool(f"tool_{i}", f"shared keyword capability {i}"), module="module", group="external")
        for i in range(5)
    ]
    index = ToolSearchIndex(tools, config=ToolSearchConfig(semantic_enabled=False, top_k=2, expanded_top_k=4))

    assert len(index.search("shared keyword")) == 2
    assert len(index.search("shared keyword", expanded=True)) == 4


def test_dynamic_middleware_injects_and_executes_runtime_tool():
    from utils.tool_search import DynamicToolSearchMiddleware, ToolMetadata, ToolSearchConfig, ToolSearchIndex

    core_tool = DummyTool("simple_calculator", "calculate expression")
    dynamic_tool = DummyTool("get_arxiv_paper_info", "Search arXiv papers by query")
    index = ToolSearchIndex(
        [ToolMetadata(tool=dynamic_tool, module="arxiv", group="research")],
        config=ToolSearchConfig(semantic_enabled=False, top_k=1),
    )
    middleware = DynamicToolSearchMiddleware(index)

    class ModelRequest:
        messages = [types.SimpleNamespace(content="请搜索 arxiv 论文")]
        tools = [core_tool]

        def override(self, **kwargs):
            clone = types.SimpleNamespace(**self.__dict__)
            clone.messages = self.messages
            clone.tools = kwargs.get("tools", self.tools)
            return clone

    captured = {}

    def model_handler(request):
        captured["tools"] = request.tools
        return "model-result"

    assert middleware.wrap_model_call(ModelRequest(), model_handler) == "model-result"
    assert [tool.name for tool in captured["tools"]] == ["simple_calculator", "get_arxiv_paper_info"]

    class ToolRequest:
        tool_call = {"id": "call-1", "name": "get_arxiv_paper_info"}
        tool = None

        def override(self, **kwargs):
            return types.SimpleNamespace(tool_call=self.tool_call, tool=kwargs.get("tool", self.tool))

    def tool_handler(request):
        return request.tool.name

    assert middleware.wrap_tool_call(ToolRequest(), tool_handler) == "get_arxiv_paper_info"


def test_dynamic_middleware_returns_controlled_error_for_unknown_tool_call():
    from utils.tool_search import DynamicToolSearchMiddleware, ToolSearchConfig, ToolSearchIndex

    middleware = DynamicToolSearchMiddleware(ToolSearchIndex([], config=ToolSearchConfig(semantic_enabled=False)))

    class ToolRequest:
        tool_call = {"id": "call-unknown", "name": "missing_tool"}
        tool = None

    result = middleware.wrap_tool_call(ToolRequest(), lambda _request: "should-not-run")

    assert result.tool_call_id == "call-unknown"
    assert "missing_tool" in result.content


def test_query_text_extracts_recent_message_content_and_state():
    from utils.tool_search import build_tool_search_query

    messages = [
        types.SimpleNamespace(content="old message"),
        {"role": "user", "content": [{"type": "text", "text": "查一下火箭发射"}, {"type": "image_url"}]},
    ]
    state = {"user_id": "u1", "group_id": 123}

    query = build_tool_search_query(messages, state=state)

    assert "查一下火箭发射" in query
    assert "group_id:123" in query
    assert "user_id:u1" in query
