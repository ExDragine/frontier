# ruff: noqa: S101
import types

import pytest


def _config(group_id=123, user_id="456"):
    return {"configurable": {"group_id": group_id, "user_id": user_id}}


@pytest.mark.asyncio
@pytest.mark.parametrize("group_id, method, target", [
    (123, "send_group_message", {"group_id": 123}),
    (None, "send_private_message", {"user_id": 456}),
    (0, "send_private_message", {"user_id": 456}),
])
async def test_plain_text_preserves_long_markdown_without_rendering(
    load_tool_module, install_milky_bot, monkeypatch, group_id, method, target,
):
    from utils import message as delivery

    async def fail_render(*_args, **_kwargs):
        pytest.fail("plain text must never enter Markdown rendering")

    monkeypatch.setattr(delivery.EnvConfig, "CONTENT_CHECK_ENABLED", False)
    monkeypatch.setattr(delivery, "markdown_to_image", fail_render)
    monkeypatch.setattr(delivery, "markdown_to_text", fail_render)
    message = load_tool_module("milky_message")
    bot = install_milky_bot(message, {method: types.SimpleNamespace(message_seq=7, time=123)})
    text = "  ```python\nprint('hello')\n```\nhttps://example.com\n" + "长文本\n" * 1000

    result = await message.send_plain_text(text, config=_config(group_id=group_id))

    assert "message_seq=7" in result
    assert len(bot.calls) == 1
    called_method, kwargs = bot.calls[0]
    assert called_method == method
    assert {key: value for key, value in kwargs.items() if key != "message"} == target
    assert len(kwargs["message"]) == 1
    assert kwargs["message"][0].type == "text"
    assert kwargs["message"][0].data == {"text": text}


@pytest.mark.asyncio
@pytest.mark.parametrize("text, config", [
    (" \n", _config()),
    ("hello", {}),
    ("hello", _config(group_id=-1)),
    ("hello", _config(group_id="invalid")),
    ("hello", _config(group_id=None, user_id=0)),
])
async def test_plain_text_rejects_empty_text_or_invalid_context(load_tool_module, install_milky_bot, text, config):
    message = load_tool_module("milky_message")
    bot = install_milky_bot(message)
    result = await message.send_plain_text(text, config=config)
    assert result
    assert not bot.calls


@pytest.mark.asyncio
async def test_plain_text_applies_output_safety_and_does_not_retry_on_failure(
    load_tool_module, monkeypatch,
):
    from utils import message as delivery

    async def sanitize(text):
        assert text == "original"
        return "blocked"

    calls = []

    class Bot:
        async def send_group_message(self, **kwargs):
            calls.append(kwargs)
            raise RuntimeError("platform rejected")

    message = load_tool_module("milky_message")
    monkeypatch.setattr(delivery, "sanitize_outgoing_text", sanitize)
    monkeypatch.setattr(message, "get_bot", lambda: Bot())
    with pytest.raises(RuntimeError, match="platform rejected"):
        await message.send_plain_text("original", config=_config())
    assert len(calls) == 1
    assert calls[0]["message"][0].data == {"text": "blocked"}


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
