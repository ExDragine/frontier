from typing import cast

from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot

from utils.agent_context import FrontierRuntimeContext
from utils.milky_tools import format_records, input_error_text, require_user_id
from utils.platform_authorization import require_bot_owner

_DEFAULT_CONFIG = cast(RunnableConfig, None)
_DEFAULT_RUNTIME = cast(ToolRuntime[FrontierRuntimeContext, dict], None)


@tool(response_format="content")
@input_error_text
async def send_friend_nudge(
    user_id: int | None = None,
    is_self: bool = False,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """发送好友戳一戳。
    Args:
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
        is_self: 是否向自己发送
    """
    resolved_user_id = require_user_id(user_id, config)
    await get_bot().send_friend_nudge(user_id=resolved_user_id, is_self=is_self)
    return f"已向好友 {resolved_user_id} 发送戳一戳"


@tool(response_format="content")
async def send_profile_like(user_id: int, count: int = 1) -> str:
    """发送个人名片点赞。
    Args:
        user_id: 好友 QQ 号
        count: 点赞次数
    """
    count = max(1, min(count, 10))
    await get_bot().send_profile_like(user_id=user_id, count=count)
    return f"已给好友 {user_id} 名片点赞 {count} 次"


@tool(response_format="content")
@input_error_text
async def delete_friend(
    user_id: int, config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
) -> str:
    """删除好友。
    Args:
        user_id: 好友 QQ 号
    """
    require_bot_owner(config, runtime)
    await get_bot().delete_friend(user_id=user_id)
    return f"已删除好友 {user_id}"


@tool(response_format="content")
async def get_friend_requests(limit: int = 20, is_filtered: bool = False) -> str:
    """获取好友请求列表。
    Args:
        limit: 获取数量上限
        is_filtered: True 只获取被过滤请求，False 只获取未过滤请求
    """
    limit = max(1, min(limit, 100))
    requests = await get_bot().get_friend_requests(limit=limit, is_filtered=is_filtered)
    return format_records(
        "好友请求",
        requests,
        ("initiator_id", "initiator_uid", "target_user_id", "state", "comment", "is_filtered"),
    )


@tool(response_format="content")
@input_error_text
async def accept_friend_request(
    initiator_uid: str, is_filtered: bool = False, config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
) -> str:
    """同意好友请求。
    Args:
        initiator_uid: 请求发起者 UID
        is_filtered: 是否是被过滤请求
    """
    require_bot_owner(config, runtime)
    await get_bot().accept_friend_request(initiator_uid=initiator_uid, is_filtered=is_filtered)
    return f"已同意好友请求 {initiator_uid}"


@tool(response_format="content")
@input_error_text
async def reject_friend_request(
    initiator_uid: str,
    is_filtered: bool = False,
    reason: str | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
) -> str:
    """拒绝好友请求。
    Args:
        initiator_uid: 请求发起者 UID
        is_filtered: 是否是被过滤请求
        reason: 可选拒绝理由
    """
    require_bot_owner(config, runtime)
    await get_bot().reject_friend_request(initiator_uid=initiator_uid, is_filtered=is_filtered, reason=reason)
    return f"已拒绝好友请求 {initiator_uid}"
