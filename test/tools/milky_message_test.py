# ruff: noqa: S101
import types

import pytest


def _config(group_id=123, user_id="456"):
    return {"configurable": {"group_id": group_id, "user_id": user_id}}


def _echoed_message(kwargs):
    return types.SimpleNamespace(
        message_scene=kwargs["message_scene"],
        peer_id=kwargs["peer_id"],
        message_seq=kwargs["message_seq"],
        sender_id=456,
        time=1714521600,
        segments=[{"type": "text", "data": {"text": "hello"}}],
    )


@pytest.mark.asyncio
async def test_message_send_and_recall_tools_call_milky(load_tool_module, install_milky_bot):
    message = load_tool_module("milky_message")
    bot = install_milky_bot(
        message,
        {
            "send_private_message": types.SimpleNamespace(message_seq=11, time=1714521600),
            "send_group_message": types.SimpleNamespace(message_seq=22, time=1714521601),
        },
    )

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
async def test_message_query_tools_use_context_and_format_results(load_tool_module, install_milky_bot):
    message = load_tool_module("milky_message")
    bot = install_milky_bot(
        message,
        {
            "get_message": _echoed_message,
            "get_resource_temp_url": "https://example.com/resource",
            "get_forwarded_messages": [
                types.SimpleNamespace(
                    message_seq=33,
                    sender_name="Alice",
                    avatar_url="https://example.com/avatar",
                    time=1714521600,
                    segments=[{"type": "text", "data": {"text": "forward"}}],
                )
            ],
        },
    )

    one = await message.get_message(message_scene="group", message_seq=88, config=_config())
    url = await message.get_resource_temp_url(resource_id="res-1")
    forwarded = await message.get_forwarded_messages(forward_id="fwd-1")
    marked = await message.mark_message_as_read(message_scene="group", message_seq=88, config=_config())

    assert "message_seq=88" in one
    assert "hello" in one
    assert url == "https://example.com/resource"
    assert "forward" in forwarded
    assert marked == "已将 group 会话 123 中消息 88 及之前消息标为已读"
    assert bot.calls == [
        ("get_message", {"message_scene": "group", "peer_id": 123, "message_seq": 88}),
        ("get_resource_temp_url", {"resource_id": "res-1"}),
        ("get_forwarded_messages", {"forward_id": "fwd-1"}),
        ("mark_message_as_read", {"message_scene": "group", "peer_id": 123, "message_seq": 88}),
    ]
