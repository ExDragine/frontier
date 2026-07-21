# ruff: noqa: S101
import types

import pytest


class DummyMilkyBot:
    def __init__(self):
        self.calls = []

    async def set_group_name(self, **kwargs):
        self.calls.append(("set_group_name", kwargs))

    async def set_group_avatar(self, **kwargs):
        self.calls.append(("set_group_avatar", kwargs))

    async def set_group_member_card(self, **kwargs):
        self.calls.append(("set_group_member_card", kwargs))

    async def set_group_member_special_title(self, **kwargs):
        self.calls.append(("set_group_member_special_title", kwargs))

    async def set_group_member_admin(self, **kwargs):
        self.calls.append(("set_group_member_admin", kwargs))

    async def set_group_member_mute(self, **kwargs):
        self.calls.append(("set_group_member_mute", kwargs))

    async def set_group_whole_mute(self, **kwargs):
        self.calls.append(("set_group_whole_mute", kwargs))

    async def kick_group_member(self, **kwargs):
        self.calls.append(("kick_group_member", kwargs))

    async def get_group_announcements(self, **kwargs):
        self.calls.append(("get_group_announcements", kwargs))
        return [
            types.SimpleNamespace(
                announcement_id="ann-1",
                user_id=456,
                time=1714521600,
                content="今天维护",
                image_url=None,
            )
        ]

    async def send_group_announcement(self, **kwargs):
        self.calls.append(("send_group_announcement", kwargs))

    async def delete_group_announcement(self, **kwargs):
        self.calls.append(("delete_group_announcement", kwargs))

    async def get_group_essence_messages(self, **kwargs):
        self.calls.append(("get_group_essence_messages", kwargs))
        return types.SimpleNamespace(
            messages=[
                types.SimpleNamespace(
                    message_seq=88,
                    sender_id=456,
                    sender_name="Alice",
                    operator_id=789,
                    operator_name="Bob",
                    operation_time=1714521700,
                )
            ],
            is_end=True,
        )

    async def set_group_essence_message(self, **kwargs):
        self.calls.append(("set_group_essence_message", kwargs))

    async def quit_group(self, **kwargs):
        self.calls.append(("quit_group", kwargs))

    async def send_group_message_reaction(self, **kwargs):
        self.calls.append(("send_group_message_reaction", kwargs))

    async def send_group_nudge(self, **kwargs):
        self.calls.append(("send_group_nudge", kwargs))

    async def get_group_notifications(self, **kwargs):
        self.calls.append(("get_group_notifications", kwargs))
        return [
            {
                "type": "join_request",
                "group_id": 123,
                "notification_seq": 9001,
                "initiator_id": 456,
                "state": "pending",
                "comment": "申请入群",
                "is_filtered": False,
            }
        ], 8999

    async def accept_group_request(self, **kwargs):
        self.calls.append(("accept_group_request", kwargs))

    async def reject_group_request(self, **kwargs):
        self.calls.append(("reject_group_request", kwargs))

    async def accept_group_invitation(self, **kwargs):
        self.calls.append(("accept_group_invitation", kwargs))

    async def reject_group_invitation(self, **kwargs):
        self.calls.append(("reject_group_invitation", kwargs))


def _install_dummy_bot(monkeypatch, module):
    bot = DummyMilkyBot()
    monkeypatch.setattr(module, "get_bot", lambda: bot)
    return bot


def _group_config(group_id=123, role="admin"):
    configurable = {"group_id": group_id}
    if role is not None:
        configurable["group_member_role"] = role
    return {"configurable": configurable}


_ADMIN_REQUIRED_MESSAGE = "只有目标群的群主或管理员才能执行此群管理操作。"


def test_group_tools_are_split_out_of_adapter(load_tool_module):
    adapter = load_tool_module("adapter")

    assert not hasattr(adapter, "set_group_name")
    assert not hasattr(adapter, "kick_group_member")


@pytest.mark.asyncio
async def test_group_management_uses_current_group_from_config(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    result = await group.set_group_name(new_group_name="新群名", config=_group_config())

    assert result == "已将群 123 的名称设置为：新群名"
    assert bot.calls == [("set_group_name", {"group_id": 123, "new_group_name": "新群名"})]


@pytest.mark.asyncio
async def test_group_management_prefers_typed_runtime_context(load_tool_module, monkeypatch):
    from utils.agent_context import FrontierRuntimeContext

    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)
    runtime = types.SimpleNamespace(
        context=FrontierRuntimeContext(
            user_id="42",
            group_id=123,
            group_member_role="owner",
            workspace_dir="/workspace",
        )
    )

    result = await group.set_group_name(
        new_group_name="新群名",
        config=_group_config(group_id=999, role="member"),
        runtime=runtime,
    )

    assert result == "已将群 123 的名称设置为：新群名"
    assert bot.calls == [("set_group_name", {"group_id": 123, "new_group_name": "新群名"})]


@pytest.mark.asyncio
async def test_group_management_allows_explicit_group_id(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    result = await group.set_group_member_mute(
        group_id=456, user_id=789, duration=60, config=_group_config(group_id=456)
    )

    assert result == "已将群 456 内用户 789 禁言 60 秒"
    assert bot.calls == [("set_group_member_mute", {"group_id": 456, "user_id": 789, "duration": 60})]


@pytest.mark.asyncio
async def test_group_management_requires_group_context(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    _install_dummy_bot(monkeypatch, group)

    result = await group.set_group_whole_mute(config={"configurable": {"group_id": None}})

    assert result == "缺少群号：请在群聊中使用，或显式传入 group_id。"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call_tool",
    [
        lambda group: group.set_group_name(new_group_name="新群名", config=_group_config(role="member")),
        lambda group: group.set_group_avatar(
            image_uri="https://example.com/avatar.png", config=_group_config(role="member")
        ),
        lambda group: group.set_group_member_card(user_id=789, card="小明", config=_group_config(role="member")),
        lambda group: group.set_group_member_special_title(
            user_id=789,
            special_title="头衔",
            config=_group_config(role="member"),
        ),
        lambda group: group.set_group_member_admin(user_id=789, is_set=True, config=_group_config(role="member")),
        lambda group: group.set_group_member_mute(user_id=789, duration=60, config=_group_config(role="member")),
        lambda group: group.set_group_whole_mute(is_mute=True, config=_group_config(role="member")),
        lambda group: group.kick_group_member(user_id=789, config=_group_config(role="member")),
        lambda group: group.send_group_announcement(content="公告", config=_group_config(role="member")),
        lambda group: group.delete_group_announcement(announcement_id="ann-1", config=_group_config(role="member")),
        lambda group: group.set_group_essence_message(message_seq=88, config=_group_config(role="member")),
        lambda group: group.quit_group(config=_group_config(role="member")),
        lambda group: group.accept_group_request(
            notification_seq=9001,
            notification_type="join_request",
            group_id=123,
            config=_group_config(role="member"),
        ),
        lambda group: group.reject_group_request(
            notification_seq=9002,
            notification_type="invited_join_request",
            group_id=123,
            config=_group_config(role="member"),
        ),
    ],
)
async def test_privileged_group_tools_require_admin_or_owner(load_tool_module, monkeypatch, call_tool):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    result = await call_tool(group)

    assert result == _ADMIN_REQUIRED_MESSAGE
    assert bot.calls == []


@pytest.mark.asyncio
async def test_privileged_group_tools_reject_when_role_context_is_missing_or_for_another_group(
    load_tool_module,
    monkeypatch,
):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    missing_role = await group.set_group_whole_mute(config=_group_config(role=None))
    other_group = await group.kick_group_member(user_id=789, group_id=456, config=_group_config(group_id=123))

    assert missing_role == _ADMIN_REQUIRED_MESSAGE
    assert other_group == _ADMIN_REQUIRED_MESSAGE
    assert bot.calls == []


@pytest.mark.asyncio
async def test_privileged_group_tools_allow_group_owner(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    result = await group.set_group_whole_mute(config=_group_config(role="owner"))

    assert result == "已开启群 123 的全员禁言"
    assert bot.calls == [("set_group_whole_mute", {"group_id": 123, "is_mute": True})]


@pytest.mark.asyncio
async def test_set_group_avatar_converts_image_uri_for_milky(load_tool_module, monkeypatch, tmp_path):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)
    avatar_path = tmp_path / "avatar.png"

    result = await group.set_group_avatar(image_uri=f"file://{avatar_path}", config=_group_config())

    assert result == "已更新群 123 的头像"
    assert bot.calls == [("set_group_avatar", {"group_id": 123, "path": str(avatar_path)})]


@pytest.mark.asyncio
async def test_group_announcement_tools_call_milky_and_format_results(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    listed = await group.get_group_announcements(config=_group_config())
    sent = await group.send_group_announcement(
        content="公告内容",
        image_uri="https://example.com/a.png",
        config=_group_config(),
    )
    deleted = await group.delete_group_announcement(announcement_id="ann-1", config=_group_config())

    assert "群 123 公告" in listed
    assert "ann-1" in listed
    assert "今天维护" in listed
    assert sent == "已向群 123 发送群公告"
    assert deleted == "已删除群 123 的公告 ann-1"
    assert bot.calls == [
        ("get_group_announcements", {"group_id": 123}),
        (
            "send_group_announcement",
            {"group_id": 123, "content": "公告内容", "url": "https://example.com/a.png"},
        ),
        ("delete_group_announcement", {"group_id": 123, "announcement_id": "ann-1"}),
    ]


@pytest.mark.asyncio
async def test_group_essence_reaction_and_nudge_tools(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    essence = await group.get_group_essence_messages(page_index=0, page_size=10, config=_group_config())
    set_result = await group.set_group_essence_message(message_seq=88, is_set=True, config=_group_config())
    reaction_result = await group.send_group_message_reaction(
        message_seq=88,
        reaction="351",
        reaction_type="face",
        is_add=False,
        config=_group_config(),
    )
    nudge_result = await group.send_group_nudge(user_id=456, config=_group_config())

    assert "群 123 精华消息" in essence
    assert "message_seq=88" in essence
    assert set_result == "已将群 123 的消息 88 设为精华"
    assert reaction_result == "已移除群 123 消息 88 的 face 表情回应 351"
    assert nudge_result == "已向群 123 内用户 456 发送戳一戳"
    assert bot.calls == [
        ("get_group_essence_messages", {"group_id": 123, "page_index": 0, "page_size": 10}),
        ("set_group_essence_message", {"group_id": 123, "message_seq": 88, "is_set": True}),
        (
            "send_group_message_reaction",
            {"group_id": 123, "message_seq": 88, "reaction": "351", "reaction_type": "face", "is_add": False},
        ),
        ("send_group_nudge", {"group_id": 123, "user_id": 456}),
    ]


@pytest.mark.asyncio
async def test_group_notification_and_invitation_tools(load_tool_module, monkeypatch):
    group = load_tool_module("milky_group")
    bot = _install_dummy_bot(monkeypatch, group)

    notifications = await group.get_group_notifications(start_notification_seq=9010, is_filtered=True, limit=5)
    accepted = await group.accept_group_request(
        notification_seq=9001,
        notification_type="join_request",
        group_id=123,
        is_filtered=True,
        config=_group_config(),
    )
    rejected = await group.reject_group_request(
        notification_seq=9002,
        notification_type="invited_join_request",
        group_id=123,
        reason="不符合要求",
        config=_group_config(),
    )
    invite_accepted = await group.accept_group_invitation(group_id=123, invitation_seq=77)
    invite_rejected = await group.reject_group_invitation(group_id=123, invitation_seq=78)

    assert "群通知" in notifications
    assert "next_notification_seq=8999" in notifications
    assert "join_request" in notifications
    assert accepted == "已同意群 123 的 join_request 请求 9001"
    assert rejected == "已拒绝群 123 的 invited_join_request 请求 9002"
    assert invite_accepted == "已同意加入群 123 的邀请 77"
    assert invite_rejected == "已拒绝加入群 123 的邀请 78"
    assert bot.calls == [
        (
            "get_group_notifications",
            {"start_notification_seq": 9010, "is_filtered": True, "limit": 5},
        ),
        (
            "accept_group_request",
            {
                "notification_seq": 9001,
                "notification_type": "join_request",
                "group_id": 123,
                "is_filtered": True,
            },
        ),
        (
            "reject_group_request",
            {
                "notification_seq": 9002,
                "notification_type": "invited_join_request",
                "group_id": 123,
                "is_filtered": False,
                "reason": "不符合要求",
            },
        ),
        ("accept_group_invitation", {"group_id": 123, "invitation_seq": 77}),
        ("reject_group_invitation", {"group_id": 123, "invitation_seq": 78}),
    ]
