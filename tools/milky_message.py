from typing import Literal, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot
from nonebot.adapters.milky.message import Message, MessageSegment
from pydantic import BaseModel, Field

from utils.milky_tools import (
    format_forwarded_messages,
    format_message,
    resolve_group_id,
    resolve_peer,
    resolve_user_id,
)

_DEFAULT_CONFIG = cast(RunnableConfig, None)


class ForwardMessageNode(BaseModel):
    user_id: int = Field(gt=0, description="原消息发送者 QQ 号")
    sender_name: str = Field(min_length=1, description="原消息发送者名称")
    text: str = Field(min_length=1, description="转发节点的文本内容")
    time: int | None = Field(default=None, ge=0, description="原消息 Unix 秒时间戳，未知时省略")


@tool(response_format="content")
async def send_forwarded_message(
    messages: list[ForwardMessageNode],
    message_scene: Literal["friend", "group"],
    peer_id: int | None = None,
    title: str | None = None,
    summary: str | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """发送文本合并转发，可保留每个节点的原始发送时间（Milky 1.3）。

    Args:
        messages: 原始消息节点，包含 user_id、sender_name、text 和可选的 time（秒）；不要编造来源或时间
        message_scene: friend 为私聊，group 为群聊
        peer_id: 目标会话 ID，省略时使用当前对应会话
        title: 可选转发标题
        summary: 可选转发摘要
    """
    if not messages:
        return "合并转发至少需要一条消息。"
    if message_scene not in {"friend", "group"}:
        return "合并转发仅支持 friend 或 group。"
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, dict(config or {}))
    if error:
        return error
    nodes = [ForwardMessageNode.model_validate(node) for node in messages]
    outgoing = Message(MessageSegment.forward([
        MessageSegment.node(node.user_id, node.sender_name, Message(node.text), time=node.time)
        for node in nodes
    ], title=title, summary=summary))
    bot = get_bot()
    response = (
        await bot.send_group_message(group_id=resolved_peer_id, message=outgoing)
        if message_scene == "group"
        else await bot.send_private_message(user_id=resolved_peer_id, message=outgoing)
    )
    return _format_message_response(response)


def _format_message_response(response) -> str:
    return f"message_seq={response.message_seq} time={response.time}"


@tool(response_format="content")
async def send_private_message(
    message_text: str,
    user_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """发送私聊文本消息。
    Args:
        message_text: 消息文本
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id, error = resolve_user_id(user_id, dict(config or {}))
    if error:
        return error
    response = await get_bot().send_private_message(user_id=resolved_user_id, message=message_text)
    return _format_message_response(response)


@tool(response_format="content")
async def send_group_message(
    message_text: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """发送群文本消息。
    Args:
        message_text: 消息文本
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, dict(config or {}))
    if error:
        return error
    response = await get_bot().send_group_message(group_id=resolved_group_id, message=message_text)
    return _format_message_response(response)


@tool(response_format="content")
async def get_message(
    message_scene: str,
    message_seq: int,
    peer_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """获取单条消息。
    Args:
        message_scene: 消息场景，friend、group 或 temp
        message_seq: 消息序列号
        peer_id: 可选会话 ID，未传时按场景从当前上下文推断
    """
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, dict(config or {}))
    if error:
        return error
    message = await get_bot().get_message(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        message_seq=message_seq,
    )
    return format_message(message)


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
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """撤回私聊消息。
    Args:
        message_seq: 消息序列号
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id, error = resolve_user_id(user_id, dict(config or {}))
    if error:
        return error
    await get_bot().recall_private_message(user_id=resolved_user_id, message_seq=message_seq)
    return f"已撤回私聊 {resolved_user_id} 的消息 {message_seq}"


@tool(response_format="content")
async def recall_group_message(
    message_seq: int,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """撤回群消息。
    Args:
        message_seq: 消息序列号
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, dict(config or {}))
    if error:
        return error
    await get_bot().recall_group_message(group_id=resolved_group_id, message_seq=message_seq)
    return f"已撤回群 {resolved_group_id} 的消息 {message_seq}"


@tool(response_format="content")
async def mark_message_as_read(
    message_scene: str,
    message_seq: int,
    peer_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """标记消息为已读。
    Args:
        message_scene: 消息场景，friend、group 或 temp
        message_seq: 消息序列号，该消息及更早消息会被标为已读
        peer_id: 可选会话 ID，未传时按场景从当前上下文推断
    """
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, dict(config or {}))
    if error:
        return error
    await get_bot().mark_message_as_read(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        message_seq=message_seq,
    )
    return f"已将 {message_scene} 会话 {resolved_peer_id} 中消息 {message_seq} 及之前消息标为已读"
