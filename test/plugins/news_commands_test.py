# ruff: noqa: S101

"""Regression tests for the /news operator command replies.

``Matcher.finish`` forwards its argument straight to ``bot.send``, which the
Milky adapter feeds into ``Message(...)``. UniMessage segments are rejected
there (``ValueError: Unexpected type: ... uniseg.segment.Text``), so command
replies must go through ``UniMessage.send`` instead.
"""

import time
from types import SimpleNamespace

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.message import Message
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebot_plugin_alconna import UniMessage
from nonebug import App

import plugins.news.commands as news_commands

CFG = SimpleNamespace(board="general")
REPORT = {
    "id": "general-2026-09-30-09",
    "board": "general",
    "namespace": "published",
    "scheduled_at": time.time(),
    "status": "ready",
    "payload": {
        "top_stories": [{"title": "房贷贴息", "summary": "财政部等三部门联合通知"}],
        "worth_reading": [{"title": "霍尔木兹海峡", "summary": "双方分歧仍大"}],
    },
    "evidence": [],
    "image": None,
}


class FakeRepo:
    def __init__(self, report=None, deliveries=()):
        self.report = report
        self.rows = list(deliveries)
        self.retried: list[tuple[str, tuple[str, ...]]] = []

    async def initialize(self):
        return None

    async def latest(self, _board):
        return self.report

    async def deliveries(self, _report_id):
        return self.rows

    async def retry_failed(self, report_id, targets):
        self.retried.append((report_id, tuple(targets)))
        return targets


def _event(text: str, *, user_id: int = 456, group_id: int = 123) -> MessageEvent:
    incoming = IncomingMessage(
        message_scene="group",
        peer_id=group_id,
        message_seq=1,
        sender_id=user_id,
        time=0,
        segments=[{"type": "text", "data": {"text": text}}],
        friend=None,
        group=Group(group_id=group_id, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=user_id,
            nickname="u",
            sex="unknown",
            group_id=group_id,
            card="",
            title="",
            level="0",
            role="member",
            join_time=0,
            last_sent_time=0,
            shut_up_end_time=0,
        ),
    )
    return MessageEvent(
        data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message()
    )


def _install_send_spy(monkeypatch) -> list[str]:
    """Capture replies sent through the UniMessage exporter."""

    sent: list[str] = []

    async def fake_send(self: UniMessage, *_args, **_kwargs):
        sent.append(self.extract_plain_text())

    monkeypatch.setattr(UniMessage, "send", fake_send)
    return sent


async def _receive(event: MessageEvent):
    async with App().test_matcher(news_commands.news) as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_ignore_permission(news_commands.news)


@pytest.mark.asyncio
async def test_latest_replies_through_unimessage_send(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    monkeypatch.setattr(news_commands, "context", lambda: (CFG, FakeRepo(REPORT), None))

    await _receive(_event("/news latest"))

    assert sent == [news_commands.render_text(REPORT)]


@pytest.mark.asyncio
async def test_latest_without_report_replies_placeholder(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    monkeypatch.setattr(news_commands, "context", lambda: (CFG, FakeRepo(None), None))

    await _receive(_event("/news latest"))

    assert sent == ["暂无新闻简报"]


@pytest.mark.asyncio
async def test_status_lists_delivery_states(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    rows = [{"target": "123", "state": "sent"}, {"target": "456", "state": "failed"}]
    monkeypatch.setattr(news_commands, "context", lambda: (CFG, FakeRepo(REPORT, rows), None))

    await _receive(_event("/news status"))

    assert sent == [f"{REPORT['id']} ready / 123=sent, 456=failed"]


@pytest.mark.asyncio
async def test_status_without_report_replies_placeholder(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    monkeypatch.setattr(news_commands, "context", lambda: (CFG, FakeRepo(None), None))

    await _receive(_event("/news status"))

    assert sent == ["暂无新闻简报"]


@pytest.mark.asyncio
async def test_preview_uses_preview_namespace(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    namespaces: list[str] = []

    async def fake_generate(*, namespace="published"):
        namespaces.append(namespace)
        return CFG, FakeRepo(REPORT), REPORT

    monkeypatch.setattr(news_commands, "context", lambda: (CFG, FakeRepo(REPORT), None))
    monkeypatch.setattr(news_commands, "generate", fake_generate)

    await _receive(_event("/news preview"))

    assert namespaces == ["preview"]
    assert sent == [news_commands.render_text(REPORT)]


@pytest.mark.asyncio
async def test_retry_requeues_failed_target(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    repo = FakeRepo(REPORT)
    delivered: list[tuple] = []

    async def fake_deliver(_repo, report, targets, _cfg, *, stage=True):
        delivered.append((report["id"], tuple(targets), stage))
        return [123]

    monkeypatch.setattr(news_commands, "context", lambda: (CFG, repo, None))
    monkeypatch.setattr(news_commands, "deliver", fake_deliver)

    await _receive(_event("/news retry 123"))

    assert repo.retried == [(REPORT["id"], ("123",))]
    assert delivered == [(REPORT["id"], ("123",), False)]
    assert sent == ["已补发"]


@pytest.mark.asyncio
async def test_retry_without_matching_failed_delivery(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    repo = FakeRepo(REPORT)

    async def fake_deliver(_repo, _report, _targets, _cfg, *, stage=True):
        return []

    monkeypatch.setattr(news_commands, "context", lambda: (CFG, repo, None))
    monkeypatch.setattr(news_commands, "deliver", fake_deliver)

    await _receive(_event("/news retry 123"))

    assert sent == ["未补发：仅 failed 状态允许显式重试"]


@pytest.mark.asyncio
async def test_retry_rejects_non_numeric_target(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    repo = FakeRepo(REPORT)
    monkeypatch.setattr(news_commands, "context", lambda: (CFG, repo, None))

    await _receive(_event("/news retry abc"))

    assert repo.retried == []
    assert sent == ["用法：/news retry <群号>"]


@pytest.mark.asyncio
async def test_unknown_action_replies_usage(monkeypatch):
    sent = _install_send_spy(monkeypatch)
    monkeypatch.setattr(news_commands, "context", lambda: (CFG, FakeRepo(REPORT), None))

    await _receive(_event("/news nope"))

    assert sent == ["用法：/news latest|status|preview|retry <群号>"]
