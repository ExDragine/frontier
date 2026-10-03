# ruff: noqa: S101

"""End-to-end wiring: daily_news runs collect → edit → render → deliver.

Only the external boundaries are faked: the Exa MCP tool, the structured LLM
call, the HTML renderer, and QQ delivery. The repository is a real SQLite file
and the scheduler/service/delivery code paths are the real ones.
"""

import datetime as dt
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from plugins.news.config import NewsConfig
from plugins.news.repository import NewsRepository

ARTICLE_TEXT = "央行今日宣布启用新型货币政策工具，受访市场人士普遍认为这释放了明确的流动性支持信号，后续观察落地节奏。"


class FakeExaTool:
    name = "web_search_exa"
    args_schema = {
        "type": "object",
        "properties": {"query": {}, "numResults": {}, "startPublishedDate": {}, "endPublishedDate": {}},
    }

    async def ainvoke(self, args):
        # Publish one hour before the edition closes so the article is in-window
        # regardless of when the test runs.
        end = dt.datetime.fromisoformat(args["endPublishedDate"])
        published = end - dt.timedelta(hours=1)
        return {"results": [{
            "title": "央行启用新型货币政策工具",
            "url": "https://example.com/news/1",
            "text": ARTICLE_TEXT,
            "publishedDate": published.isoformat(),
        }]}


async def fake_structured_call(*, schema, user_prompt, **_kwargs):
    article = json.loads(user_prompt)["articles"][0]
    return schema(top_stories=[{
        "title": article["title"],
        "category": "财经",
        "summary": article["text"][:60],
        "evidence": [{"article_id": article["article_id"], "quote": article["text"][5:35]}],
    }], worth_reading=[])


class _Sent:
    def __init__(self, kind, payload):
        self.kind = kind
        self.payload = payload

    async def send(self, target=None, bot=None):
        FakeUniMessage.recorded.append((self.kind, target.id, self.payload))


class FakeUniMessage:
    recorded = []

    @classmethod
    def text(cls, text):
        return _Sent("text", text)

    def image(self, raw=None, **_kwargs):
        return _Sent("image", raw)


@pytest.fixture
def news_e2e(monkeypatch, tmp_path):
    from plugins.news import delivery, editor, scheduler

    monkeypatch.setenv("FRONTIER_NEWS_DB", str(tmp_path / "news.db"))
    monkeypatch.setattr(scheduler, "load_news_config", lambda: NewsConfig(
        model="fake", provider="fake", min_stories=1, target_stories=1, queries=("news",),
    ))
    monkeypatch.setattr(scheduler, "render_image", AsyncMock(return_value=b"png-bytes"))
    monkeypatch.setattr(editor, "structured_call", fake_structured_call)
    FakeUniMessage.recorded = []
    monkeypatch.setattr(delivery, "UniMessage", FakeUniMessage)

    mcp_client = types.ModuleType("tools.mcp_client")

    async def fake_discovery():
        return [FakeExaTool()]

    mcp_client.mcp_get_tools_async = fake_discovery
    monkeypatch.setitem(sys.modules, "tools.mcp_client", mcp_client)

    # Stub the clockwork package so daily_news resolves task_manager without
    # executing the real plugin __init__ (scheduler/driver side effects).
    clockwork_pkg = sys.modules.get("plugins.clockwork")
    if clockwork_pkg is None:
        clockwork_pkg = types.ModuleType("plugins.clockwork")
        clockwork_pkg.__path__ = [str(Path(__file__).resolve().parents[2] / "plugins" / "clockwork")]
        monkeypatch.setitem(sys.modules, "plugins.clockwork", clockwork_pkg)
    manager = SimpleNamespace(get_task_groups=AsyncMock(return_value=[123]))
    monkeypatch.setattr(clockwork_pkg, "task_manager", manager, raising=False)
    return scheduler


@pytest.mark.asyncio
async def test_daily_news_full_pipeline(news_e2e, tmp_path):
    scheduler = news_e2e

    result = await scheduler.daily_news(job_id="daily_news")

    assert result.status == "success"
    assert result.messages_sent == 1
    assert FakeUniMessage.recorded == [("image", "123", b"png-bytes")]

    report = await NewsRepository(tmp_path / "news.db").latest("general")
    assert report["status"] == "ready"
    assert report["image"] == b"png-bytes"
    story = report["payload"]["top_stories"][0]
    assert story["title"] == "央行启用新型货币政策工具"
    assert report["evidence"][0]["text"] == ARTICLE_TEXT

    # 第二轮：报告复用、已 sent 的群不重发。
    result = await scheduler.daily_news(job_id="daily_news")
    assert result.status == "success"
    assert result.messages_sent == 0
    assert len(FakeUniMessage.recorded) == 1
