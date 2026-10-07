# ruff: noqa: S101
from types import SimpleNamespace

import pytest

from utils.agent_context import FrontierRuntimeContext
from utils.milky_tools import ToolInputError
from utils.platform_authorization import require_bot_owner


@pytest.mark.parametrize("owner", ["123", "milky:123"])
def test_frozen_identity_takes_precedence_over_config(monkeypatch, owner):
    from nonebot import get_driver

    monkeypatch.setattr(get_driver().config, "superusers", {owner})
    context = FrontierRuntimeContext(user_id="456", group_id=None, group_member_role=None, workspace_dir=".")
    with pytest.raises(ToolInputError):
        require_bot_owner({"configurable": {"user_id": "123"}}, SimpleNamespace(context=context))
    require_bot_owner({"configurable": {"user_id": "123"}})


@pytest.mark.asyncio
@pytest.mark.parametrize("module, name, args", [
    ("milky_friend", "accept_friend_request", {"initiator_uid": "u-456"}),
    ("milky_friend", "reject_friend_request", {"initiator_uid": "u-456"}),
    ("milky_friend", "delete_friend", {"user_id": 456}),
    ("milky_group", "accept_group_invitation", {"group_id": 123, "invitation_seq": 77}),
    ("milky_group", "reject_group_invitation", {"group_id": 123, "invitation_seq": 77}),
])
async def test_normal_users_cannot_manage_bot_relationships(load_tool_module, monkeypatch, module, name, args):
    tool_module = load_tool_module(module)
    monkeypatch.setattr(tool_module, "get_bot", lambda: pytest.fail("unauthorized tool accessed bot"))
    result = await getattr(tool_module, name)(**args, config={"configurable": {"user_id": "not-owner"}})
    assert "超级用户" in result
