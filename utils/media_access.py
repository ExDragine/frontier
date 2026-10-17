"""Shared access checks for media commands and agent tools."""

from collections.abc import Sequence

from utils.agent_context import FrontierRuntimeContext
from utils.configs import EnvConfig
from utils.milky_tools import configurable

MEDIA_ACCESS_DENIED = "没有权限使用媒体生成功能"


def _contains_id(values: Sequence[int | str], target: int | str | None) -> bool:
    if target in (None, "", 0, "0"):
        return False
    return any(str(value) == str(target) for value in values)


def has_media_permission(
    user_id: int | str | None,
    group_id: int | str | None,
    *,
    policy: type[EnvConfig],
) -> bool:
    """Apply the shared paint/video policy, with blacklists taking priority."""
    if _contains_id(policy.PAINT_BLACKLIST_PERSON_LIST, user_id):
        return False
    if _contains_id(policy.PAINT_BLACKLIST_GROUP_LIST, group_id):
        return False
    if not policy.PAINT_WHITELIST_MODE:
        return True
    return _contains_id(policy.PAINT_WHITELIST_PERSON_LIST, user_id) or _contains_id(
        policy.PAINT_WHITELIST_GROUP_LIST, group_id
    )


def has_media_tool_permission(config=None, runtime=None, *, policy: type[EnvConfig]) -> bool:
    """Use injected identity; mutable graph state and model arguments cannot grant access."""
    context = getattr(runtime, "context", None)
    if isinstance(context, FrontierRuntimeContext):
        user_id, group_id = context.user_id, context.group_id
    else:
        cfg = configurable(config)
        user_id, group_id = cfg.get("user_id"), cfg.get("group_id")
    return has_media_permission(user_id, group_id, policy=policy)
