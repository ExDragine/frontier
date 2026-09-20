# ruff: noqa: S101

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from plugins.news.config import NewsConfig
from plugins.news.schemas import Edition
from plugins.news.sources import SearchSource, SourcePool, publication_time


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
