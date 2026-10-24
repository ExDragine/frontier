# ruff: noqa: S101

"""End-to-end wiring for the agent-led DeepSeek news pipeline."""

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
from plugins.news.schemas import NewsPayload

ARTICLE_TEXT = "央行今日宣布启用新型货币政策工具，受访市场人士普遍认为这释放了明确的流动性支持信号，后续观察落地节奏。"


async def fake_assistant_agent(*, user_prompt, **_kwargs):
    window = json.loads(user_prompt)["window"]
    published = dt.datetime.fromisoformat(window[1]) - dt.timedelta(hours=1)
    payload = NewsPayload(
        top_stories=[
            {
                "title": "央行启用新型货币政策工具",
                "category": "财经",
                "summary": ARTICLE_TEXT[:60],
                "evidence": [
                    {
                        "article_id": "https://example.com/news/1",
                        "quote": ARTICLE_TEXT[5:35],
                    }
                ],
            }
        ],
        worth_reading=[],
    )
    tool_result = {
        "status": "ok",
        "query": "news",
        "count": 1,
        "results": [
            {
                "title": "央行启用新型货币政策工具",
                "url": "https://example.com/news/1",
                "summary": ARTICLE_TEXT,
                "content": ARTICLE_TEXT,
                "date": published.isoformat(),
                "site_name": "example.com",
            }
        ],
    }
    return {
        "messages": [
            SimpleNamespace(
                type="tool",
                name="deepseek_web_search",
                content=json.dumps(tool_result, ensure_ascii=False),
            )
        ],
        "structured_response": payload,
    }


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
    monkeypatch.setattr(
        scheduler,
        "load_news_config",
        lambda: NewsConfig(
            model="fake",
            provider="fake",
            min_stories=1,
            target_stories=1,
            queries=("news",),
        ),
    )
    monkeypatch.setattr(scheduler, "render_image", AsyncMock(return_value=b"png-bytes"))
    monkeypatch.setattr(editor, "assistant_agent", fake_assistant_agent)
    FakeUniMessage.recorded = []
    monkeypatch.setattr(delivery, "UniMessage", FakeUniMessage)

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

    result = await scheduler.daily_news(job_id="daily_news")
    assert result.status == "success"
    assert result.messages_sent == 0
    assert len(FakeUniMessage.recorded) == 1
