import json
from typing import Literal, cast

from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot
from nonebot.adapters.milky.message import Message, MessageSegment
from pydantic import BaseModel, Field

from utils.agent_context import FrontierRuntimeContext
from utils.agents.runtime import conversation_workspace_key
from utils.configs import EnvConfig
from utils.milky_tools import (
    ToolInputError,
    configurable,
    format_forwarded_messages,
    format_message,
    input_error_text,
    require_group_id,
    require_peer,
    require_user_id,
)

_DEFAULT_CONFIG = cast(RunnableConfig, None)
_DEFAULT_RUNTIME = cast(ToolRuntime[FrontierRuntimeContext, dict], None)


def _tool_text_message(bot: object, text: str) -> Message | str:
    """Wrap tool-sent long text in an expandable QQ forward, preserving source text."""
    threshold = EnvConfig.TOOL_LONG_TEXT_FORWARD_THRESHOLD
    if threshold == 0 or len(text) < threshold:
        return text

    try:
        sender_id = int(getattr(bot, "self_id", None))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ToolInputError("无法确认机器人 QQ 号，长文本未发送。") from exc
    if sender_id <= 0:
        raise ToolInputError("机器人 QQ 号无效，长文本未发送。")

    node = MessageSegment.node(sender_id, EnvConfig.BOT_NAME, Message(text))
    return Message(MessageSegment.forward([node], title="长文本", summary="查看完整内容"))


class ForwardMessageNode(BaseModel):
    user_id: int = Field(gt=0, description="原消息发送者 QQ 号")
    sender_name: str = Field(min_length=1, description="原消息发送者名称")
    text: str = Field(min_length=1, description="转发节点的文本内容")
    time: int | None = Field(default=None, ge=0, description="原消息 Unix 秒时间戳，未知时省略")


@tool(response_format="content")
@input_error_text
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
    resolved_peer_id = require_peer(message_scene, peer_id, config)
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
@input_error_text
async def send_plain_text(
    text: str,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """立即向当前 QQ 会话发送纯文本，不渲染 Markdown、不转图片。

    用于用户要求可复制的文字、代码、链接或明确要求不要图片的最终内容。
    保留原文和换行，Markdown 标记也按文字发送；不要用来发送思考或过程状态。
    目标由运行时会话决定，不能指定其他群或用户。成功后不要在最终回复中重复正文。
    长文本达到配置阈值时自动使用可展开的合并转发消息，仍保留原文；失败不自动重试。

    Args:
        text: 要发送的完整纯文本正文
    """
    if not text.strip():
        raise ToolInputError("纯文本消息不能为空。")
    context = configurable(config)
    is_group = context.get("group_id") not in (None, "", 0, "0")
    target = require_group_id(config=config) if is_group else require_user_id(config=config)
    if target <= 0:
        raise ToolInputError("当前会话 ID 必须为正整数。")

    from utils.message import sanitize_outgoing_text

    content = await sanitize_outgoing_text(text)
    if not content or not content.strip():
        raise ToolInputError("纯文本消息经内容检查后为空，未发送。")
    bot = get_bot()
    outgoing = _tool_text_message(bot, content)
    message = [MessageSegment.text(content)] if isinstance(outgoing, str) else outgoing
    response = (
        await bot.send_group_message(group_id=target, message=message)
        if is_group
        else await bot.send_private_message(user_id=target, message=message)
    )
    label = "合并转发长文本" if not isinstance(outgoing, str) else "纯文本"
    return f"已向当前会话发送{label}消息，{_format_message_response(response)}。不要重复发送正文。"


@tool(response_format="content")
@input_error_text
async def send_private_message(
    message_text: str,
    user_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """发送私聊文本消息；长文本自动包装为可展开的合并转发。
    Args:
        message_text: 消息文本
        user_id: 可选好友 QQ 号，未传时使用当前用户上下文
    """
    resolved_user_id = require_user_id(user_id, config)
    bot = get_bot()
    response = await bot.send_private_message(user_id=resolved_user_id, message=_tool_text_message(bot, message_text))
    return _format_message_response(response)


@tool(response_format="content")
@input_error_text
async def send_group_message(
    message_text: str,
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """发送群文本消息；长文本自动包装为可展开的合并转发。
    Args:
        message_text: 消息文本
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    bot = get_bot()
    response = await bot.send_group_message(group_id=resolved_group_id, message=_tool_text_message(bot, message_text))
    return _format_message_response(response)


@tool(response_format="content")
@input_error_text
async def get_message(
    message_scene: str,
    message_seq: int,
    peer_id: int | None = None,
    include_attachments: bool = False,
    attachment_index: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
) -> str:
    """获取单条消息，可按需恢复当前会话历史图片和文件，再用 read_file 读取返回的路径。

    先通过历史查询确定消息及发送者；附件可来自同群其他成员，不限当前用户。
    不确定用户指哪一张时先澄清，不自动拿最近附件替代。每次最多加载 4 项。

    Args:
        message_scene: 消息场景，friend、group 或 temp
        message_seq: 消息序列号
        peer_id: 可选会话 ID，未传时按场景从当前上下文推断
        include_attachments: 是否恢复历史附件，默认只读消息文本和附件编号
        attachment_index: 可选原消息段的零基 segment_index；不是第几张成功下载的图片
    """
    if include_attachments:
        return await _message_with_attachments(message_scene, message_seq, peer_id, attachment_index, config, runtime)
    if attachment_index is not None:
        raise ToolInputError("指定 attachment_index 时需设置 include_attachments=true。")
    resolved_peer_id = require_peer(message_scene, peer_id, config)
    message = await get_bot().get_message(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        message_seq=message_seq,
    )
    return format_message(message)


async def _message_with_attachments(message_scene, message_seq, peer_id, attachment_index, config, runtime):
    from plugins.agent.historical_attachments import load_historical_attachments
    from plugins.agent.reply_context import MessageSource
    from utils.database import MessageDatabase

    cfg = configurable(config)
    context = getattr(runtime, "context", None)
    identity = (
        {"configurable": {"group_id": context.group_id, "user_id": context.user_id}}
        if context is not None else config
    )
    group_id = configurable(identity).get("group_id")
    current_scene = "group" if group_id not in (None, "", 0, "0") else "friend"
    current_peer = require_peer(current_scene, None, identity)
    if message_scene != current_scene or (peer_id is not None and peer_id != current_peer):
        raise ToolInputError("历史附件只能在当前会话内读取，请使用当前群聊或私聊。")
    if message_seq < 0 or (attachment_index is not None and attachment_index < 0):
        raise ToolInputError("消息序列号和 attachment_index 不能为负数。")
    workspace_key = conversation_workspace_key(current_peer, current_peer if current_scene == "group" else None)
    memory_dir = (cfg.get("virtual_roots") or {}).get(f"/memory/{workspace_key}/")
    if not memory_dir:
        raise ToolInputError("当前会话未挂载附件目录，无法读取历史附件。")
    conversation = getattr(context, "conversation", None)
    if conversation is not None and (
        conversation.platform != "qq" or conversation.conversation_id != str(current_peer)
        or conversation.kind != ("group" if current_scene == "group" else "private")
    ):
        raise ToolInputError("当前运行时会话与 QQ 目标不匹配。")
    bot = get_bot(conversation.account_id) if conversation is not None else get_bot()
    result = await load_historical_attachments(
        bot, MessageSource(str(bot.self_id), current_scene, current_peer), message_seq, MessageDatabase(),
        workspace_key=workspace_key, memory_dir=memory_dir, attachment_index=attachment_index,
    )
    return json.dumps(result, ensure_ascii=False)


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
@input_error_text
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
    resolved_user_id = require_user_id(user_id, config)
    await get_bot().recall_private_message(user_id=resolved_user_id, message_seq=message_seq)
    return f"已撤回私聊 {resolved_user_id} 的消息 {message_seq}"


@tool(response_format="content")
@input_error_text
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
    resolved_group_id = require_group_id(group_id, config)
    await get_bot().recall_group_message(group_id=resolved_group_id, message_seq=message_seq)
    return f"已撤回群 {resolved_group_id} 的消息 {message_seq}"


@tool(response_format="content")
@input_error_text
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
    resolved_peer_id = require_peer(message_scene, peer_id, config)
    await get_bot().mark_message_as_read(
        message_scene=message_scene,
        peer_id=resolved_peer_id,
        message_seq=message_seq,
    )
    return f"已将 {message_scene} 会话 {resolved_peer_id} 中消息 {message_seq} 及之前消息标为已读"
