# ruff: noqa: S101
import types

import pytest


class DummyMilkyBot:
    def __init__(self):
        self.calls = []

    async def get_login_info(self):
        self.calls.append(("get_login_info", {}))
        return types.SimpleNamespace(uin=10000, nickname="Frontier")

    async def get_impl_info(self):
        self.calls.append(("get_impl_info", {}))
        return types.SimpleNamespace(
            impl_name="Lagrange",
            impl_version="1.0",
            qq_protocol_version="1",
            qq_protocol_type="linux",
            milky_version="1.2",
        )

    async def get_user_profile(self, **kwargs):
        self.calls.append(("get_user_profile", kwargs))
        return types.SimpleNamespace(nickname="Alice", qid="alice", age=18, sex="unknown", level=42)

    async def get_friend_list(self, **kwargs):
        self.calls.append(("get_friend_list", kwargs))
        return [types.SimpleNamespace(user_id=1, nickname="Alice", remark="A")]

    async def get_friend_info(self, **kwargs):
        self.calls.append(("get_friend_info", kwargs))
        return types.SimpleNamespace(user_id=1, nickname="Alice", remark="A")

    async def get_group_list(self, **kwargs):
        self.calls.append(("get_group_list", kwargs))
        return [types.SimpleNamespace(group_id=123, group_name="群", member_count=3, max_member_count=500)]

    async def get_group_info(self, **kwargs):
        self.calls.append(("get_group_info", kwargs))
        return types.SimpleNamespace(group_id=123, group_name="群", member_count=3, max_member_count=500)

    async def get_group_member_list(self, **kwargs):
        self.calls.append(("get_group_member_list", kwargs))
        return [types.SimpleNamespace(user_id=456, nickname="Bob", card="小鲍", role="member")]

    async def get_group_member_info(self, **kwargs):
        self.calls.append(("get_group_member_info", kwargs))
        return types.SimpleNamespace(user_id=456, nickname="Bob", card="小鲍", role="member")

    async def get_peer_pins(self):
        self.calls.append(("get_peer_pins", {}))
        return {
            "friends": [types.SimpleNamespace(user_id=1, nickname="Alice")],
            "groups": [types.SimpleNamespace(group_id=123, group_name="群")],
        }

    async def set_peer_pin(self, **kwargs):
        self.calls.append(("set_peer_pin", kwargs))

    async def set_avatar(self, **kwargs):
        self.calls.append(("set_avatar", kwargs))

    async def set_nickname(self, **kwargs):
        self.calls.append(("set_nickname", kwargs))

    async def set_bio(self, **kwargs):
        self.calls.append(("set_bio", kwargs))

    async def get_custom_face_url_list(self):
        self.calls.append(("get_custom_face_url_list", {}))
        return ["https://example.com/face.png"]

    async def get_cookies(self, **kwargs):
        self.calls.append(("get_cookies", kwargs))
        return "uin=o10000;"

    async def get_csrf_token(self):
        self.calls.append(("get_csrf_token", {}))
        return "csrf"


def _install_dummy_bot(monkeypatch, module):
    bot = DummyMilkyBot()
    monkeypatch.setattr(module, "get_bot", lambda: bot)
    return bot


def _group_config(group_id=123):
    return {"configurable": {"group_id": group_id, "user_id": "456"}}


@pytest.mark.asyncio
async def test_system_read_tools_format_milky_results(load_tool_module, monkeypatch):
    system = load_tool_module("milky_system")
    bot = _install_dummy_bot(monkeypatch, system)

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
async def test_system_write_tools_call_milky(load_tool_module, monkeypatch, tmp_path):
    system = load_tool_module("milky_system")
    bot = _install_dummy_bot(monkeypatch, system)
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
