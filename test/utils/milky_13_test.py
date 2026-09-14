# ruff: noqa: S101
"""Milky 1.3 application contracts using real adapter message types."""

from types import SimpleNamespace

import pytest
from nonebot.adapters.milky.event import GroupDisbandEvent
from nonebot.adapters.milky.message import Message

from plugins.agent import gateway as gateway_module
from plugins.agent.message_normalizer import normalize_segments
from utils import message as message_module
from utils.milky_tools import format_forwarded_messages, format_message


@pytest.mark.asyncio
async def test_markdown_survives_extraction_normalization_and_history_tools():
    content = "# 问题\n请解释 **WAL** 的作用。"
    segments = [{"type": "markdown", "data": {"content": content}}]
    text, images, audio, video = await message_module.message_extract(segments)
    assert (text, images, audio, video) == (content, [], [], [])
    result = await normalize_segments(None, segments)
    assert result.content == content
    assert "WAL" in format_message({"segments": segments})

    class Bot:
        async def get_forwarded_messages(self, **kwargs):
            return [SimpleNamespace(sender_name="Alice", time=123, segments=segments)]

    result = await normalize_segments(Bot(), [{"type": "forward", "data": {"forward_id": "f1"}}])
    assert result.derived_messages[0].content == content
    assert "WAL" in format_forwarded_messages(await Bot().get_forwarded_messages())


@pytest.mark.asyncio
async def test_markdown_wake_word_works_when_adapter_plaintext_is_empty(monkeypatch):
    seen = []

    async def active_check(text, words):
        seen.append(text)
        return True

    monkeypatch.setattr(gateway_module, "_message_gateway_blocked_by_access_policy", lambda *_: False)
    monkeypatch.setattr(gateway_module, "_get_wake_words", lambda *_: ["Frontier"])
    monkeypatch.setattr(gateway_module, "_active_trigger_should_reply", active_check)
    event = SimpleNamespace(
        data=SimpleNamespace(group=SimpleNamespace(group_id=123), segments=[
            {"type": "markdown", "data": {"content": "Frontier 请解释这张表"}},
        ]),
        get_user_id=lambda: "456", get_plaintext=lambda: "", is_tome=lambda: False, to_me=False,
    )
    assert await gateway_module.message_gateway(event, [])
    assert seen == ["Frontier 请解释这张表"]


@pytest.mark.asyncio
async def test_group_disband_passes_nudge_matcher_and_is_handled_without_reply(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins import playground
    from plugins.agent import handlers as agent

    event = GroupDisbandEvent(time=123, self_id=999, data={"group_id": 123, "operator_id": 456})
    assert not await playground._is_nudge(event)
    assert await agent._is_group_disband(event)
    await agent.handle_group_disband(event)


@pytest.mark.asyncio
@pytest.mark.parametrize("scene", ["friend", "group"])
async def test_forward_tool_preserves_node_times(load_tool_module, monkeypatch, scene):
    module = load_tool_module("milky_message")
    calls = []

    async def send(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(message_seq=3, time=456)

    monkeypatch.setattr(module, "get_bot", lambda: SimpleNamespace(send_group_message=send, send_private_message=send))
    result = await module.send_forwarded_message(
        messages=[
            {"user_id": 456, "sender_name": "Alice", "text": "first", "time": 123},
            {"user_id": 789, "sender_name": "Bob", "text": "second"},
        ],
        message_scene=scene, config={"configurable": {"group_id": 123, "user_id": "456"}},
    )
    assert "message_seq=3" in result
    assert calls[0]["group_id" if scene == "group" else "user_id"] == (123 if scene == "group" else 456)
    message = calls[0]["message"]
    assert isinstance(message, Message)
    nodes = message[0].data["messages"]
    assert [node.time for node in nodes] == [123, None]
    assert str(nodes[0].segments) == "first"


@pytest.mark.asyncio
@pytest.mark.parametrize("role,target,allowed", [("admin", 123, True), ("owner", 123, True),
                                               ("member", 123, False), (None, 123, False), ("admin", 999, False)])
async def test_persist_file_enforces_target_group_permission(load_tool_module, monkeypatch, role, target, allowed):
    module = load_tool_module("milky_file")
    calls = []

    async def persist(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(module, "get_bot", lambda: SimpleNamespace(persist_group_file=persist))
    result = await module.persist_group_file(
        file_id="file-1", group_id=target,
        config={"configurable": {"group_id": 123, "group_member_role": role}},
    )
    assert bool(calls) is allowed
    if allowed:
        assert calls == [{"group_id": 123, "file_id": "file-1"}]
        assert "永久" in result
    else:
        assert "群主或管理员" in result


@pytest.mark.asyncio
async def test_file_download_tool_passes_self_send_flag(load_tool_module, monkeypatch):
    module = load_tool_module("milky_file")
    calls = []

    async def download(**kwargs):
        calls.append(kwargs)
        return "https://example.com/file"

    monkeypatch.setattr(module, "get_bot", lambda: SimpleNamespace(get_private_file_download_url=download))
    await module.get_private_file_download_url(
        file_id="own-file", file_hash="hash", user_id=456, is_self_send=True,
    )
    assert calls == [{"user_id": 456, "file_id": "own-file", "file_hash": "hash", "is_self_send": True}]
