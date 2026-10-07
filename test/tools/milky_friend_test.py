# ruff: noqa: S101
import types

import pytest


def _config(user_id="456"):
    return {"configurable": {"user_id": user_id}}


@pytest.mark.asyncio
async def test_friend_action_tools_call_milky(load_tool_module, install_milky_bot, monkeypatch):
    from nonebot import get_driver

    monkeypatch.setattr(get_driver().config, "superusers", {"456"})
    friend = load_tool_module("milky_friend")
    bot = install_milky_bot(friend)

    nudge = await friend.send_friend_nudge(config=_config())
    like = await friend.send_profile_like(user_id=456, count=3)
    deleted = await friend.delete_friend(user_id=456, config=_config())

    assert nudge == "已向好友 456 发送戳一戳"
    assert like == "已给好友 456 名片点赞 3 次"
    assert deleted == "已删除好友 456"
    assert bot.calls == [
        ("send_friend_nudge", {"user_id": 456, "is_self": False}),
        ("send_profile_like", {"user_id": 456, "count": 3}),
        ("delete_friend", {"user_id": 456}),
    ]


@pytest.mark.asyncio
async def test_friend_request_tools_call_milky_and_format_results(load_tool_module, install_milky_bot, monkeypatch):
    from nonebot import get_driver

    monkeypatch.setattr(get_driver().config, "superusers", {"456"})
    friend = load_tool_module("milky_friend")
    bot = install_milky_bot(
        friend,
        {
            "get_friend_requests": [
                types.SimpleNamespace(
                    initiator_id=456,
                    initiator_uid="u-456",
                    target_user_id=10000,
                    state="pending",
                    comment="加好友",
                    is_filtered=False,
                )
            ],
        },
    )

    requests = await friend.get_friend_requests(limit=50, is_filtered=True)
    accepted = await friend.accept_friend_request(initiator_uid="u-456", is_filtered=True, config=_config())
    rejected = await friend.reject_friend_request(initiator_uid="u-789", reason="不认识", config=_config())

    assert "好友请求" in requests
    assert "u-456" in requests
    assert accepted == "已同意好友请求 u-456"
    assert rejected == "已拒绝好友请求 u-789"
    assert bot.calls == [
        ("get_friend_requests", {"limit": 50, "is_filtered": True}),
        ("accept_friend_request", {"initiator_uid": "u-456", "is_filtered": True}),
        ("reject_friend_request", {"initiator_uid": "u-789", "is_filtered": False, "reason": "不认识"}),
    ]
