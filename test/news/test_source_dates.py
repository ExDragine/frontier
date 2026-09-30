# ruff: noqa: S101

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from plugins.news.config import NewsConfig
from plugins.news.schemas import Edition
from plugins.news.sources import (
    ExaMcpSource,
    SearchSource,
    SourcePool,
    _mcp_articles,
    configured_sources,
    publication_time,
)


@pytest.mark.parametrize("value", ["2026-09-19T00:00:00Z", "Sat, 19 Sep 2026 00:00:00 GMT", "Sat, 19 Sep 2026 08:00:00 +0800"])
def test_publication_timestamp_formats(value):
    assert publication_time(value) == dt.datetime(2026, 9, 19, tzinfo=dt.UTC)


@pytest.mark.parametrize("value", [None, "", "yesterday", "2026-09-19", "2026-09-19T00:00:00"])
def test_unknown_timezone_or_date_is_not_invented(value):
    assert publication_time(value) is None


@pytest.mark.asyncio
async def test_news_rfc_dates_survive_collection_and_unknown_dates_are_counted():
    edition = Edition("general", dt.datetime(2026, 9, 19, 1, tzinfo=dt.UTC))
    cfg = NewsConfig(min_stories=1, target_stories=1, queries=("news",))
    results = [
        {"url": f"https://example.com/{i}", "title": f"News {i}", "content": "supported news material " * 10,
         "published_date": date}
        for i, date in enumerate(["Sat, 19 Sep 2026 00:00:00 GMT", None, "Thu, 17 Sep 2026 00:00:00 GMT"])
    ]
    client = SimpleNamespace(post=AsyncMock(return_value=SimpleNamespace(status_code=200, json=lambda: {"results": results})))
    pool = SourcePool([SearchSource("tavily", "test-key", client, cfg)], cfg)
    articles = await pool.collect(edition, set())
    assert len(articles) == 1
    assert pool.stats == {"received": 3, "undated": 1, "outside_window": 1, "eligible": 1}


@pytest.mark.asyncio
@pytest.mark.parametrize("dictionary_schema", [False, True])
async def test_exa_mcp_is_used_when_rest_key_is_missing(monkeypatch, dictionary_schema):
    calls = []

    class FakeTool:
        name = "web_search_exa"
        args_schema = SimpleNamespace(
            model_fields={
                "query": object(),
                "numResults": object(),
                "startPublishedDate": object(),
                "endPublishedDate": object(),
            }
        )

        async def ainvoke(self, args):
            calls.append(args)
            return SimpleNamespace(
                artifact={
                    "structured_content": {
                        "results": [
                            {
                                "title": "实时新闻标题",
                                "url": "https://example.com/news",
                                "text": "这是一段足够长的新闻正文，用于验证 Exa MCP 返回的证据可以进入日报流程。",
                                "publishedDate": "2026-09-18T12:00:00Z",
                            }
                        ]
                    }
                }
            )

    if dictionary_schema:
        FakeTool.args_schema = {"type": "object", "properties": {
            name: {"type": "string"} for name in FakeTool.args_schema.model_fields
        }}

    import sys
    import types

    mcp_client = types.ModuleType("tools.mcp_client")

    async def fake_discovery():
        return [FakeTool()]

    mcp_client.mcp_get_tools_async = fake_discovery
    monkeypatch.setitem(sys.modules, "tools.mcp_client", mcp_client)
    edition = Edition("general", dt.datetime(2026, 9, 19, 1, tzinfo=dt.UTC))
    cfg = NewsConfig(min_stories=1, target_stories=1, queries=("news",))
    source = ExaMcpSource(cfg)

    articles = await source.search("news", edition)

    assert len(articles) == 1
    assert articles[0].provider == "exa"
    assert articles[0].published_at == dt.datetime(2026, 9, 18, 12, tzinfo=dt.UTC)
    assert calls[0]["query"] == "news"
    assert calls[0]["numResults"] == cfg.source_results
    assert calls[0]["startPublishedDate"] == "2026-09-18T01:00:00+00:00"


def test_configured_sources_uses_exa_mcp_without_rest_key(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    cfg = NewsConfig(sources=("exa",))
    sources = configured_sources(SimpleNamespace(), cfg).sources
    assert isinstance(sources[0], ExaMcpSource)


def test_exa_mcp_markdown_keeps_publication_date():
    result = """
[实时新闻标题](https://example.com/news)
Published Date: 2026-09-18T12:00:00Z
这是一段足够长的新闻正文，用于验证纯文本 MCP 结果中的发布时间不会丢失。
"""
    articles = _mcp_articles(result)
    assert len(articles) == 1
    assert articles[0].published_at == dt.datetime(2026, 9, 18, 12, tzinfo=dt.UTC)
