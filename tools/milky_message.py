from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from nonebot import get_bot

from utils.milky_tools import (
    format_forwarded_messages,
    format_message,
    format_messages,
    resolve_group_id,
    resolve_peer,
    resolve_user_id,
)


def _format_message_response(response) -> str:
    return f"message_seq={response.message_seq} time={response.time}"


@tool(response_format="content")
async def send_private_message(
    message_text: str,
    user_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """发送私聊文本消息。
    Args:
        message_text: 消息文本
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id, error = resolve_user_id(user_id, config)
    if error:
        return error
    response = await get_bot().send_private_message(user_id=resolved_user_id, message=message_text)
    return _format_message_response(response)


@tool(response_format="content")
async def send_group_message(
    message_text: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """发送群文本消息。
    Args:
        message_text: 消息文本
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    response = await get_bot().send_group_message(group_id=resolved_group_id, message=message_text)
    return _format_message_response(response)


@tool(response_format="content")
async def get_message(
    message_scene: str,
    message_seq: int,
    peer_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """获取单条消息。
    Args:
        message_scene: 消息场景，friend、group 或 temp
        message_seq: 消息序列号
        peer_id: 可选会话 ID，未传时按场景从当前上下文推断
    """
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, config)
    if error:
        return error
    message = await get_bot().get_message(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        message_seq=message_seq,
    )
    return format_message(message)


@tool(response_format="content")
async def get_history_messages(
    message_scene: str,
    peer_id: int | None = None,
    start_message_seq: int | None = None,
    limit: int = 20,
    config: RunnableConfig = None,
) -> str:
    """获取历史消息列表。
    Args:
        message_scene: 消息场景，friend、group 或 temp
        peer_id: 可选会话 ID，未传时按场景从当前上下文推断
        start_message_seq: 可选起始消息序列号
        limit: 获取数量上限，最大 30
    """
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, config)
    if error:
        return error
    limit = max(1, min(limit, 30))
    messages, next_message_seq = await get_bot().get_history_messages(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        start_message_seq=start_message_seq,
        limit=limit,
    )
    return format_messages("历史消息", messages, next_message_seq)


@tool(response_format="content")
async def get_resource_temp_url(resource_id: str) -> str:
    """获取资源临时下载链接。
    Args:
        resource_id: 资源 ID
    """
    return await get_bot().get_resource_temp_url(resource_id=resource_id)


@tool(response_format="content")
async def get_forwarded_messages(forward_id: str) -> str:
    """获取合并转发消息内容。
    Args:
        forward_id: 合并转发 ID
    """
    messages = await get_bot().get_forwarded_messages(forward_id=forward_id)
    return format_forwarded_messages(messages)


@tool(response_format="content")
async def recall_private_message(
    message_seq: int,
    user_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """撤回私聊消息。
    Args:
        message_seq: 消息序列号
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id, error = resolve_user_id(user_id, config)
    if error:
        return error
    await get_bot().recall_private_message(user_id=resolved_user_id, message_seq=message_seq)
    return f"已撤回私聊 {resolved_user_id} 的消息 {message_seq}"


@tool(response_format="content")
async def recall_group_message(
    message_seq: int,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """撤回群消息。
    Args:
        message_seq: 消息序列号
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    await get_bot().recall_group_message(group_id=resolved_group_id, message_seq=message_seq)
    return f"已撤回群 {resolved_group_id} 的消息 {message_seq}"


@tool(response_format="content")
async def mark_message_as_read(
    message_scene: str,
    message_seq: int,
    peer_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """标记消息为已读。
    Args:
        message_scene: 消息场景，friend、group 或 temp
        message_seq: 消息序列号，该消息及更早消息会被标为已读
        peer_id: 可选会话 ID，未传时按场景从当前上下文推断
    """
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, config)
    if error:
        return error
    await get_bot().mark_message_as_read(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        message_seq=message_seq,
    )
    return f"已将 {message_scene} 会话 {resolved_peer_id} 中消息 {message_seq} 及之前消息标为已读"
