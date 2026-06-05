from typing import Any, Literal

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from nonebot import get_bot

from utils.milky_tools import binary_kwargs_from_uri, dump_model, resolve_group_id, truncate_text

_GROUP_REQUEST_TYPES = {"join_request", "invited_join_request"}
_REACTION_TYPES = {"face", "emoji"}
_GROUP_ADMIN_ROLES = {"admin", "owner"}
_GROUP_ADMIN_REQUIRED_MESSAGE = "只有目标群的群主或管理员才能执行此群管理操作。"


def _configurable(config: RunnableConfig | None) -> dict:
    return (config or {}).get("configurable", {})


def _role_from_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        value = value.get("role")
    else:
        value = getattr(value, "role", value)
    if value in (None, ""):
        return None
    return str(value)


def _group_member_role(config: RunnableConfig | None) -> str | None:
    cfg = _configurable(config)
    return _role_from_value(cfg.get("group_member_role")) or _role_from_value(cfg.get("group_member"))


def _config_group_id(config: RunnableConfig | None) -> int | None:
    raw_group_id = _configurable(config).get("group_id")
    if raw_group_id in (None, ""):
        return None
    try:
        return int(raw_group_id)
    except (TypeError, ValueError):
        return None


def _require_group_admin_or_owner(group_id: int, config: RunnableConfig | None) -> str | None:
    if _config_group_id(config) != group_id:
        return _GROUP_ADMIN_REQUIRED_MESSAGE
    if _group_member_role(config) not in _GROUP_ADMIN_ROLES:
        return _GROUP_ADMIN_REQUIRED_MESSAGE
    return None


def _resolve_admin_group(group_id: int | None, config: RunnableConfig | None) -> tuple[int | None, str | None]:
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return None, error
    permission_error = _require_group_admin_or_owner(resolved_group_id, config)
    if permission_error:
        return None, permission_error
    return resolved_group_id, None


def _format_announcements(group_id: int, announcements: list[Any]) -> str:
    if not announcements:
        return f"群 {group_id} 暂无公告。"

    lines = [f"群 {group_id} 公告（{len(announcements)} 条）："]
    for announcement in announcements:
        data = dump_model(announcement)
        parts = [
            f"id={data.get('announcement_id', '')}",
            f"user_id={data.get('user_id', '')}",
            f"time={data.get('time', '')}",
            f"content={truncate_text(data.get('content', ''))}",
        ]
        image_url = data.get("image_url")
        if image_url:
            parts.append(f"image_url={image_url}")
        lines.append("- " + " ".join(parts))
    return "\n".join(lines)


def _format_essence_messages(group_id: int, response: Any, page_index: int) -> str:
    data = dump_model(response)
    messages = data.get("messages") or []
    is_end = data.get("is_end")
    if not messages:
        return f"群 {group_id} 第 {page_index} 页暂无精华消息。is_end={is_end}"

    lines = [f"群 {group_id} 精华消息（第 {page_index} 页，{len(messages)} 条，is_end={is_end}）："]
    for message in messages:
        item = dump_model(message)
        lines.append(
            "- "
            f"message_seq={item.get('message_seq', '')} "
            f"sender={item.get('sender_name', '')}({item.get('sender_id', '')}) "
            f"operator={item.get('operator_name', '')}({item.get('operator_id', '')}) "
            f"operation_time={item.get('operation_time', '')}"
        )
    return "\n".join(lines)


def _format_notification(notification: Any) -> str:
    data = dump_model(notification)
    preferred = [
        "type",
        "group_id",
        "notification_seq",
        "state",
        "initiator_id",
        "target_user_id",
        "operator_id",
        "is_set",
        "is_filtered",
        "comment",
    ]
    parts = [f"{key}={truncate_text(data[key])}" for key in preferred if data.get(key) is not None]
    for key, value in data.items():
        if key not in preferred and value is not None:
            parts.append(f"{key}={truncate_text(value)}")
    return "- " + " ".join(parts)


def _format_notifications(notifications: list[Any], next_notification_seq: int | None) -> str:
    if not notifications:
        return f"未获取到群通知。next_notification_seq={next_notification_seq}"
    lines = [f"群通知（{len(notifications)} 条，next_notification_seq={next_notification_seq}）："]
    lines.extend(_format_notification(notification) for notification in notifications)
    return "\n".join(lines)


def _normalize_group_request_type(notification_type: str) -> str | None:
    return notification_type if notification_type in _GROUP_REQUEST_TYPES else None


def _normalize_reaction_type(reaction_type: str) -> str | None:
    return reaction_type if reaction_type in _REACTION_TYPES else None


@tool(response_format="content")
async def set_group_name(
    new_group_name: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置群名称。
    Args:
        new_group_name: 新群名称
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_name(group_id=resolved_group_id, new_group_name=new_group_name)
    return f"已将群 {resolved_group_id} 的名称设置为：{new_group_name}"


@tool(response_format="content")
async def set_group_avatar(
    image_uri: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置群头像，支持 file://、http(s)://、base64:// 或本地文件路径。
    Args:
        image_uri: 头像文件 URI
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_avatar(group_id=resolved_group_id, **binary_kwargs_from_uri(image_uri))
    return f"已更新群 {resolved_group_id} 的头像"


@tool(response_format="content")
async def set_group_member_card(
    user_id: int,
    card: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置群成员名片。
    Args:
        user_id: 被设置的群成员 QQ 号
        card: 新群名片
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_member_card(group_id=resolved_group_id, user_id=user_id, card=card)
    return f"已将群 {resolved_group_id} 内用户 {user_id} 的群名片设置为：{card}"


@tool(response_format="content")
async def set_group_member_special_title(
    user_id: int,
    special_title: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置群成员专属头衔。
    Args:
        user_id: 被设置的群成员 QQ 号
        special_title: 新专属头衔
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_member_special_title(
        group_id=resolved_group_id,
        user_id=user_id,
        special_title=special_title,
    )
    return f"已将群 {resolved_group_id} 内用户 {user_id} 的专属头衔设置为：{special_title}"


@tool(response_format="content")
async def set_group_member_admin(
    user_id: int,
    is_set: bool = True,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置或取消群管理员。
    Args:
        user_id: 被设置的 QQ 号
        is_set: True 设置为管理员，False 取消管理员
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_member_admin(group_id=resolved_group_id, user_id=user_id, is_set=is_set)
    action = "设置为管理员" if is_set else "取消管理员"
    return f"已将群 {resolved_group_id} 内用户 {user_id} {action}"


@tool(response_format="content")
async def set_group_member_mute(
    user_id: int,
    duration: int = 0,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置群成员禁言，duration 为 0 时取消禁言。
    Args:
        user_id: 被设置的 QQ 号
        duration: 禁言持续时间，单位秒；0 表示取消禁言
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    if duration < 0:
        return "禁言时长不能为负数。"
    await get_bot().set_group_member_mute(group_id=resolved_group_id, user_id=user_id, duration=duration)
    if duration == 0:
        return f"已取消群 {resolved_group_id} 内用户 {user_id} 的禁言"
    return f"已将群 {resolved_group_id} 内用户 {user_id} 禁言 {duration} 秒"


@tool(response_format="content")
async def set_group_whole_mute(
    is_mute: bool = True,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置或取消群全员禁言。
    Args:
        is_mute: True 开启全员禁言，False 取消全员禁言
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_whole_mute(group_id=resolved_group_id, is_mute=is_mute)
    action = "开启" if is_mute else "取消"
    return f"已{action}群 {resolved_group_id} 的全员禁言"


@tool(response_format="content")
async def kick_group_member(
    user_id: int,
    reject_add_request: bool = False,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """踢出群成员。
    Args:
        user_id: 被踢的 QQ 号
        reject_add_request: 是否拒绝后续加群申请
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().kick_group_member(
        group_id=resolved_group_id,
        user_id=user_id,
        reject_add_request=reject_add_request,
    )
    suffix = "，并拒绝后续加群申请" if reject_add_request else ""
    return f"已将用户 {user_id} 移出群 {resolved_group_id}{suffix}"


@tool(response_format="content")
async def get_group_announcements(
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """获取群公告列表。
    Args:
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    announcements = await get_bot().get_group_announcements(group_id=resolved_group_id)
    return _format_announcements(resolved_group_id, announcements)


@tool(response_format="content")
async def send_group_announcement(
    content: str,
    image_uri: str | None = None,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """发送群公告，可附带图片。
    Args:
        content: 公告内容
        image_uri: 可选公告图片 URI，支持 file://、http(s)://、base64:// 或本地文件路径
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().send_group_announcement(
        group_id=resolved_group_id,
        content=content,
        **binary_kwargs_from_uri(image_uri),
    )
    return f"已向群 {resolved_group_id} 发送群公告"


@tool(response_format="content")
async def delete_group_announcement(
    announcement_id: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """删除群公告。
    Args:
        announcement_id: 公告 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().delete_group_announcement(group_id=resolved_group_id, announcement_id=announcement_id)
    return f"已删除群 {resolved_group_id} 的公告 {announcement_id}"


@tool(response_format="content")
async def get_group_essence_messages(
    page_index: int = 0,
    page_size: int = 20,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """获取群精华消息列表。
    Args:
        page_index: 页码索引，从 0 开始
        page_size: 每页数量，范围 1-100
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    if page_index < 0:
        return "页码索引不能为负数。"
    page_size = max(1, min(page_size, 100))
    response = await get_bot().get_group_essence_messages(
        group_id=resolved_group_id,
        page_index=page_index,
        page_size=page_size,
    )
    return _format_essence_messages(resolved_group_id, response, page_index)


@tool(response_format="content")
async def set_group_essence_message(
    message_seq: int,
    is_set: bool = True,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """设置或取消群精华消息。
    Args:
        message_seq: 消息序列号
        is_set: True 设置精华，False 取消精华
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().set_group_essence_message(group_id=resolved_group_id, message_seq=message_seq, is_set=is_set)
    action = "设为精华" if is_set else "取消精华"
    return f"已将群 {resolved_group_id} 的消息 {message_seq} {action}"


@tool(response_format="content")
async def quit_group(
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """退出群聊。
    Args:
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    await get_bot().quit_group(group_id=resolved_group_id)
    return f"已退出群 {resolved_group_id}"


@tool(response_format="content")
async def send_group_message_reaction(
    message_seq: int,
    reaction: str,
    reaction_type: Literal["face", "emoji"] = "face",
    is_add: bool = True,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """发送或移除群消息表情回应。
    Args:
        message_seq: 要回应的消息序列号
        reaction: 表情 ID
        reaction_type: face 或 emoji
        is_add: True 添加回应，False 移除回应
        group_id: 可选群号，未传时使用当前群聊
    """
    normalized_reaction_type = _normalize_reaction_type(reaction_type)
    if normalized_reaction_type is None:
        return "reaction_type 仅支持 face 或 emoji。"
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().send_group_message_reaction(
        group_id=resolved_group_id,
        message_seq=message_seq,
        reaction=reaction,
        reaction_type=normalized_reaction_type,
        is_add=is_add,
    )
    action = "添加" if is_add else "移除"
    return f"已{action}群 {resolved_group_id} 消息 {message_seq} 的 {normalized_reaction_type} 表情回应 {reaction}"


@tool(response_format="content")
async def send_group_nudge(
    user_id: int,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """发送群戳一戳。
    Args:
        user_id: 被戳的群成员 QQ 号
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().send_group_nudge(group_id=resolved_group_id, user_id=user_id)
    return f"已向群 {resolved_group_id} 内用户 {user_id} 发送戳一戳"


@tool(response_format="content")
async def get_group_notifications(
    start_notification_seq: int | None = None,
    is_filtered: bool = False,
    limit: int = 20,
) -> str:
    """获取群通知列表。
    Args:
        start_notification_seq: 可选起始通知序列号
        is_filtered: True 只获取被过滤通知，False 只获取未过滤通知
        limit: 获取数量上限，范围 1-100
    """
    limit = max(1, min(limit, 100))
    notifications, next_notification_seq = await get_bot().get_group_notifications(
        start_notification_seq=start_notification_seq,
        is_filtered=is_filtered,
        limit=limit,
    )
    return _format_notifications(notifications, next_notification_seq)


@tool(response_format="content")
async def accept_group_request(
    notification_seq: int,
    notification_type: str,
    group_id: int,
    is_filtered: bool = False,
    config: RunnableConfig = None,
) -> str:
    """同意入群或邀请他人入群请求。
    Args:
        notification_seq: 请求对应的通知序列号
        notification_type: join_request 或 invited_join_request
        group_id: 请求所在群号
        is_filtered: 是否是被过滤请求
        config: 工具调用上下文
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    normalized_type = _normalize_group_request_type(notification_type)
    if normalized_type is None:
        return "notification_type 仅支持 join_request 或 invited_join_request。"
    await get_bot().accept_group_request(
        notification_seq=notification_seq,
        notification_type=normalized_type,
        group_id=resolved_group_id,
        is_filtered=is_filtered,
    )
    return f"已同意群 {resolved_group_id} 的 {normalized_type} 请求 {notification_seq}"


@tool(response_format="content")
async def reject_group_request(
    notification_seq: int,
    notification_type: str,
    group_id: int,
    is_filtered: bool = False,
    reason: str | None = None,
    config: RunnableConfig = None,
) -> str:
    """拒绝入群或邀请他人入群请求。
    Args:
        notification_seq: 请求对应的通知序列号
        notification_type: join_request 或 invited_join_request
        group_id: 请求所在群号
        is_filtered: 是否是被过滤请求
        reason: 可选拒绝理由
        config: 工具调用上下文
    """
    resolved_group_id, error = _resolve_admin_group(group_id, config)
    if error:
        return error
    normalized_type = _normalize_group_request_type(notification_type)
    if normalized_type is None:
        return "notification_type 仅支持 join_request 或 invited_join_request。"
    await get_bot().reject_group_request(
        notification_seq=notification_seq,
        notification_type=normalized_type,
        group_id=resolved_group_id,
        is_filtered=is_filtered,
        reason=reason,
    )
    return f"已拒绝群 {resolved_group_id} 的 {normalized_type} 请求 {notification_seq}"


@tool(response_format="content")
async def accept_group_invitation(group_id: int, invitation_seq: int) -> str:
    """同意他人邀请自身入群。
    Args:
        group_id: 群号
        invitation_seq: 邀请序列号
    """
    await get_bot().accept_group_invitation(group_id=group_id, invitation_seq=invitation_seq)
    return f"已同意加入群 {group_id} 的邀请 {invitation_seq}"


@tool(response_format="content")
async def reject_group_invitation(group_id: int, invitation_seq: int) -> str:
    """拒绝他人邀请自身入群。
    Args:
        group_id: 群号
        invitation_seq: 邀请序列号
    """
    await get_bot().reject_group_invitation(group_id=group_id, invitation_seq=invitation_seq)
    return f"已拒绝加入群 {group_id} 的邀请 {invitation_seq}"
