# ruff: noqa: S101
import types

import pytest

_GROUP = types.SimpleNamespace(group_id=123, group_name="群", member_count=3, max_member_count=500)
_MEMBER = types.SimpleNamespace(user_id=456, nickname="Bob", card="小鲍", role="member")
_FRIEND = types.SimpleNamespace(user_id=1, nickname="Alice", remark="A")


def _group_config(group_id=123):
    return {"configurable": {"group_id": group_id, "user_id": "456"}}


@pytest.fixture
def system_bot(load_tool_module, install_milky_bot):
    """Milky bot stub for the system tool module plus the loaded module."""

    system = load_tool_module("milky_system")
    bot = install_milky_bot(
        system,
        {
            "get_login_info": types.SimpleNamespace(uin=10000, nickname="Frontier"),
            "get_impl_info": types.SimpleNamespace(
                impl_name="Lagrange",
                impl_version="1.0",
                qq_protocol_version="1",
                qq_protocol_type="linux",
                milky_version="1.2",
            ),
            "get_user_profile": types.SimpleNamespace(
                nickname="Alice", qid="alice", age=18, sex="unknown", level=42
            ),
            "get_friend_list": [_FRIEND],
            "get_friend_info": _FRIEND,
            "get_group_list": [_GROUP],
            "get_group_info": _GROUP,
            "get_group_member_list": [_MEMBER],
            "get_group_member_info": _MEMBER,
            "get_peer_pins": {
                "friends": [types.SimpleNamespace(user_id=1, nickname="Alice")],
                "groups": [types.SimpleNamespace(group_id=123, group_name="群")],
            },
            "get_custom_face_url_list": ["https://example.com/face.png"],
            "get_cookies": "uin=o10000;",
            "get_csrf_token": "csrf",
        },
    )
    return system, bot


@pytest.mark.asyncio
async def test_system_read_tools_format_milky_results(system_bot):
    system, bot = system_bot

    login = await system.get_login_info()
    impl = await system.get_impl_info()
    profile = await system.get_user_profile(user_id=456)
    friends = await system.get_friend_list(no_cache=True)
    friend = await system.get_friend_info(user_id=1)
    groups = await system.get_group_list()
    group = await system.get_group_info(config=_group_config())
    members = await system.get_group_member_list(config=_group_config())
    member = await system.get_group_member_info(user_id=456, config=_group_config())
    pins = await system.get_peer_pins()
    faces = await system.get_custom_face_url_list()
    cookies = await system.get_cookies(domain="qq.com")
    csrf = await system.get_csrf_token()

    assert "uin=10000" in login
    assert "Lagrange" in impl
    assert "Alice" in profile
    assert "好友列表" in friends
    assert "user_id=1" in friend
    assert "群列表" in groups
    assert "group_id=123" in group
    assert "群 123 成员" in members
    assert "user_id=456" in member
    assert "置顶好友" in pins
    assert "https://example.com/face.png" in faces
    assert cookies == "uin=o10000;"
    assert csrf == "csrf"
    assert bot.calls == [
        ("get_login_info", {}),
        ("get_impl_info", {}),
        ("get_user_profile", {"user_id": 456}),
        ("get_friend_list", {"no_cache": True}),
        ("get_friend_info", {"user_id": 1, "no_cache": False}),
        ("get_group_list", {"no_cache": False}),
        ("get_group_info", {"group_id": 123, "no_cache": False}),
        ("get_group_member_list", {"group_id": 123, "no_cache": False}),
        ("get_group_member_info", {"group_id": 123, "user_id": 456, "no_cache": False}),
        ("get_peer_pins", {}),
        ("get_custom_face_url_list", {}),
        ("get_cookies", {"domain": "qq.com"}),
        ("get_csrf_token", {}),
    ]


@pytest.mark.asyncio
async def test_system_write_tools_call_milky(system_bot, tmp_path):
    system, bot = system_bot
    avatar = tmp_path / "avatar.png"

    pin = await system.set_peer_pin(message_scene="group", peer_id=123, is_pinned=False)
    avatar_result = await system.set_avatar(image_uri=f"file://{avatar}")
    nickname = await system.set_nickname(new_nickname="新昵称")
    bio = await system.set_bio(new_bio="新的个签")

    assert pin == "已取消 group 会话 123 的置顶"
    assert avatar_result == "已更新当前 QQ 账号头像"
    assert nickname == "已将当前 QQ 账号昵称设置为：新昵称"
    assert bio == "已更新当前 QQ 账号个性签名"
    assert bot.calls == [
        ("set_peer_pin", {"message_scene": "group", "peer_id": 123, "is_pinned": False}),
        ("set_avatar", {"path": str(avatar)}),
        ("set_nickname", {"new_nickname": "新昵称"}),
        ("set_bio", {"new_bio": "新的个签"}),
    ]
