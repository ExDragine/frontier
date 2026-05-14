# ruff: noqa: S101
import types

import pytest


class DummyMilkyBot:
    def __init__(self):
        self.calls = []

    async def send_private_message(self, **kwargs):
        self.calls.append(("send_private_message", kwargs))
        return types.SimpleNamespace(message_seq=11, time=1714521600)

    async def send_group_message(self, **kwargs):
        self.calls.append(("send_group_message", kwargs))
        return types.SimpleNamespace(message_seq=22, time=1714521601)

    async def recall_private_message(self, **kwargs):
        self.calls.append(("recall_private_message", kwargs))

    async def recall_group_message(self, **kwargs):
        self.calls.append(("recall_group_message", kwargs))

    async def get_message(self, **kwargs):
        self.calls.append(("get_message", kwargs))
        return types.SimpleNamespace(
            message_scene=kwargs["message_scene"],
            peer_id=kwargs["peer_id"],
            message_seq=kwargs["message_seq"],
            sender_id=456,
            time=1714521600,
            segments=[{"type": "text", "data": {"text": "hello"}}],
        )

    async def get_history_messages(self, **kwargs):
        self.calls.append(("get_history_messages", kwargs))
        return [
            types.SimpleNamespace(
                message_scene=kwargs["message_scene"],
                peer_id=kwargs["peer_id"],
                message_seq=1,
                sender_id=456,
                time=1714521600,
                segments=[{"type": "text", "data": {"text": "old"}}],
            )
        ], 0

    async def get_resource_temp_url(self, resource_id):
        self.calls.append(("get_resource_temp_url", {"resource_id": resource_id}))
        return "https://example.com/resource"

    async def get_forwarded_messages(self, forward_id):
        self.calls.append(("get_forwarded_messages", {"forward_id": forward_id}))
        return [
            types.SimpleNamespace(
                message_seq=33,
                sender_name="Alice",
                avatar_url="https://example.com/avatar",
                time=1714521600,
                segments=[{"type": "text", "data": {"text": "forward"}}],
            )
        ]

    async def mark_message_as_read(self, **kwargs):
        self.calls.append(("mark_message_as_read", kwargs))


def _install_dummy_bot(monkeypatch, module):
    bot = DummyMilkyBot()
    monkeypatch.setattr(module, "get_bot", lambda: bot)
    return bot


def _config(group_id=123, user_id="456"):
    return {"configurable": {"group_id": group_id, "user_id": user_id}}


@pytest.mark.asyncio
async def test_message_send_and_recall_tools_call_milky(load_tool_module, monkeypatch):
    message = load_tool_module("milky_message")
    bot = _install_dummy_bot(monkeypatch, message)

    private_sent = await message.send_private_message(user_id=456, message_text="你好")
    group_sent = await message.send_group_message(message_text="大家好", config=_config())
    private_recalled = await message.recall_private_message(user_id=456, message_seq=11)
    group_recalled = await message.recall_group_message(message_seq=22, config=_config())

    assert "message_seq=11" in private_sent
    assert "message_seq=22" in group_sent
    assert private_recalled == "已撤回私聊 456 的消息 11"
    assert group_recalled == "已撤回群 123 的消息 22"
    assert bot.calls == [
        ("send_private_message", {"user_id": 456, "message": "你好"}),
        ("send_group_message", {"group_id": 123, "message": "大家好"}),
        ("recall_private_message", {"user_id": 456, "message_seq": 11}),
        ("recall_group_message", {"group_id": 123, "message_seq": 22}),
    ]


@pytest.mark.asyncio
async def test_message_query_tools_use_context_and_format_results(load_tool_module, monkeypatch):
    message = load_tool_module("milky_message")
    bot = _install_dummy_bot(monkeypatch, message)

    one = await message.get_message(message_scene="group", message_seq=88, config=_config())
    history = await message.get_history_messages(message_scene="friend", limit=60, config=_config())
    url = await message.get_resource_temp_url(resource_id="res-1")
    forwarded = await message.get_forwarded_messages(forward_id="fwd-1")
    marked = await message.mark_message_as_read(message_scene="group", message_seq=88, config=_config())

    assert "message_seq=88" in one
    assert "hello" in one
    assert "next_message_seq=0" in history
    assert "old" in history
    assert url == "https://example.com/resource"
    assert "forward" in forwarded
    assert marked == "已将 group 会话 123 中消息 88 及之前消息标为已读"
    assert bot.calls == [
        ("get_message", {"message_scene": "group", "peer_id": 123, "message_seq": 88}),
        (
            "get_history_messages",
            {"message_scene": "friend", "peer_id": 456, "start_message_seq": None, "limit": 30},
        ),
        ("get_resource_temp_url", {"resource_id": "res-1"}),
        ("get_forwarded_messages", {"forward_id": "fwd-1"}),
        ("mark_message_as_read", {"message_scene": "group", "peer_id": 123, "message_seq": 88}),
    ]
