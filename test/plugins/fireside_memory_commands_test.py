# ruff: noqa: S101

import types

import pytest

from nonebug import App
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage

from plugins.fireside import memory_commands
from utils.memory_types import MemoryScope


def test_parse_scope_tokens():
    assert memory_commands._parse_scope("个人") == MemoryScope.USER
    assert memory_commands._parse_scope("群") == MemoryScope.GROUP
    assert memory_commands._parse_scope("other") is None


def test_strip_memory_prefix():
    assert memory_commands._strip_memory_prefix("/记忆 查看") == "查看"
    assert memory_commands._strip_memory_prefix("memory list") == "list"


@pytest.mark.asyncio
async def test_handle_memory_list_group_guard(monkeypatch):
    async def fake_list_memories(**_kwargs):
        return []

    monkeypatch.setattr(memory_commands.memory, "list_memories", fake_list_memories)

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)

        incoming = IncomingMessage(
            message_scene="group",
            peer_id=123,
            message_seq=1,
            sender_id=456,
            time=0,
            segments=[{"type": "text", "data": {"text": "记忆 查看 群"}}],
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

    ctx.should_call_send(event, "当前不在群聊中，无法查看群记忆。")
    ctx.receive_event(bot, event)
    ctx.should_finished()
