# ruff: noqa: S101

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_arxiv_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("arxiv")

    class DummyLoader:
        def __init__(self, query):
            self.query = query

        def load(self):
            return [{"title": "A", "query": self.query}]

    monkeypatch.setattr(mod, "ArxivLoader", DummyLoader)
    result = await mod.get_arxiv_paper_info("llm")
    parsed = json.loads(result)
    assert parsed[0]["query"] == "llm"


def test_bilibili_extract_info(load_tool_module):
    mod = load_tool_module("bilibili")
    data = mod.extract_info(
        {
            "title": "标题",
            "url": "https://b23.tv/test",
            "owner": {"name": "UP", "mid": 1},
            "stat": {"view": 10},
            "dimension": {"width": 1920, "height": 1080},
            "pages": [{"part": "P1"}],
            "pubdate": 1700000000,
        }
    )
    assert data["标题"] == "标题"
    assert data["UP主"].startswith("UP")
    assert data["视频分辨率"] == "1920x1080"


@pytest.mark.asyncio
async def test_bilibili_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("bilibili")

    class DummyLoader:
        def __init__(self, urls):
            self.urls = urls

        def load(self):
            return [SimpleNamespace(metadata={"title": "Video", "url": self.urls[0], "pages": []})]

    monkeypatch.setattr(mod, "BiliBiliLoader", DummyLoader)
    result = await mod.get_bilibili_video_info("https://b23.tv/x")
    parsed = json.loads(result)
    assert parsed["标题"] == "Video"
    assert parsed["视频链接"] == "https://b23.tv/x"


def test_safe_eval_success_and_invalid(load_tool_module):
    mod = load_tool_module("calculator")
    assert mod.safe_eval("1+2*3") == 7.0

    with pytest.raises(ValueError):
        mod.safe_eval("__import__('os').system('echo hi')")


@pytest.mark.asyncio
async def test_simple_calculator(load_tool_module):
    mod = load_tool_module("calculator")
    ok = await mod.simple_calculator("2**3")
    fail = await mod.simple_calculator("a+b")
    assert "计算结果" in ok
    assert "计算失败" in fail


@pytest.mark.asyncio
async def test_wikipedia_tool(load_tool_module, monkeypatch):
    mod = load_tool_module("wikipedia")

    class DummyLoader:
        def __init__(self, **_kwargs):
            pass

        def load(self):
            return [
                SimpleNamespace(metadata={"title": "Earth", "source": "https://wiki/Earth"}, page_content="planet")
            ]

    monkeypatch.setattr(mod, "WikipediaLoader", DummyLoader)
    result = await mod.get_wikipedia_pages("earth")
    assert "Title: Earth" in result
    assert "URL: https://wiki/Earth" in result


def test_tavily_objects_created(load_tool_module):
    mod = load_tool_module("tavily")
    assert hasattr(mod, "tavily_search")
    assert hasattr(mod, "tavily_extract")
    assert hasattr(mod, "tavily_crawl")
    assert hasattr(mod, "tavily_map")


def test_mcp_get_tools(load_tool_module, monkeypatch):
    Path("mcp.json").write_text("{}", encoding="utf-8")
    mod = load_tool_module("mcp_client")

    class DummyClient:
        async def get_tools(self):
            return ["a", "b"]

    monkeypatch.setattr(mod, "client", DummyClient())
    tools = mod.mcp_get_tools()
    assert tools == ["a", "b"]
