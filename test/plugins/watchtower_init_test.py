# ruff: noqa: S101

import types

import pytest

from nonebug import App
from nonebot_plugin_alconna import UniMessage
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage

from plugins.watchtower import on_startup, handle_setting


@pytest.mark.asyncio
async def test_on_startup_creates_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "env.toml.example").write_text("", encoding="utf-8")
    (tmp_path / "mcp.json.example").write_text("{}", encoding="utf-8")
    (tmp_path / ".env.example").write_text("", encoding="utf-8")
    (tmp_path / "cache").mkdir()

    class DummyMemory:
        def ensure_schema_ready(self):
            return None

    monkeypatch.setattr("plugins.watchtower.memory", DummyMemory())
    await on_startup()
    assert (tmp_path / "env.toml").exists()
    assert (tmp_path / "mcp.json").exists()
    assert (tmp_path / ".env").exists()


@pytest.mark.asyncio
async def test_handle_setting_default(monkeypatch):
    async def fake_message_extract(*_args, **_kwargs):
        return "", [], [], []

    monkeypatch.setattr("plugins.watchtower.message_extract", fake_message_extract)

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)

        incoming = IncomingMessage(
            message_scene="group",
            peer_id=123,
            message_seq=1,
            sender_id=456,
            time=0,
            segments=[{"type": "text", "data": {"text": "/model"}}],
            friend=None,
            group=Group(group_id=123, group_name="g", member_count=1, max_member_count=1),
            group_member=Member(
                user_id=456,
                nickname="u",
                sex="unknown",
                group_id=123,
                card="",
                title="",
                level="0",
                role="member",
                join_time=0,
                last_sent_time=0,
                shut_up_end_time=0,
            ),
        )
        event = MessageEvent(data=incoming, to_me=True, time=0, self_id="1")

        async def fake_send(self, *args, **kwargs):
            return None

        monkeypatch.setattr(UniMessage, "send", fake_send)
        ctx.receive_event(bot, event)
        ctx.should_finished()
