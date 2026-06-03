from pathlib import Path

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from nonebot import get_bot
from nonebot.adapters.milky.message import MessageSegment

from utils.alconna import UniMessage
from utils.milky_tools import resolve_group_id, resolve_local_path, validate_url


def _resolve_message_local_path(source: str, workspace_dir: str | None):
    path = resolve_local_path(source, workspace_dir)
    if path is not None or workspace_dir is not None:
        return path
    direct_path = Path(source)
    return direct_path if direct_path.is_file() else None


@tool(response_format="content_and_artifact")
async def send_image(source: str, config: RunnableConfig = None) -> tuple[str, UniMessage]:
    """发送图片工具，支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/photo.png）或远程 URL
    """
    workspace_dir = ((config or {}).get("configurable") or {}).get("workspace_dir")
    if path := _resolve_message_local_path(source, workspace_dir):
        return "构建了一个图片消息", UniMessage.image(path=path)
    validate_url(source)
    return "构建了一个图片消息", UniMessage.image(url=source)


@tool(response_format="content_and_artifact")
async def send_audio(source: str, config: RunnableConfig = None) -> tuple[str, UniMessage]:
    """发送音频文件工具（以文件形式呈现，区别于语音），支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/music.mp3）或远程 URL
    """
    workspace_dir = ((config or {}).get("configurable") or {}).get("workspace_dir")
    if path := _resolve_message_local_path(source, workspace_dir):
        return "构建了一个音频消息", UniMessage.audio(path=path)
    validate_url(source)
    return "构建了一个音频消息", UniMessage.audio(url=source)


@tool(response_format="content_and_artifact")
async def send_voice(source: str, config: RunnableConfig = None) -> tuple[str, UniMessage]:
    """发送语音消息工具（以对讲/语音条形式呈现），支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/voice.wav）或远程 URL
    """
    workspace_dir = ((config or {}).get("configurable") or {}).get("workspace_dir")
    if path := _resolve_message_local_path(source, workspace_dir):
        return "构建了一个语音消息", UniMessage.voice(path=path)
    validate_url(source)
    return "构建了一个语音消息", UniMessage.voice(url=source)


@tool(response_format="content_and_artifact")
async def send_video(source: str, config: RunnableConfig = None) -> tuple[str, UniMessage]:
    """发送视频工具，支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/clip.mp4）或远程 URL
    """
    workspace_dir = ((config or {}).get("configurable") or {}).get("workspace_dir")
    if path := _resolve_message_local_path(source, workspace_dir):
        return "构建了一个视频消息", UniMessage.video(path=path)
    validate_url(source)
    return "构建了一个视频消息", UniMessage.video(url=source)


@tool(response_format="content_and_artifact")
async def send_emoji(emoji_id: str) -> tuple[str, UniMessage]:
    """发送 QQ 表情工具
    Args:
        emoji_id: 表情ID
    """
    return "构建了一个表情消息", UniMessage.emoji(id=emoji_id)


@tool(response_format="content_and_artifact")
async def send_file(path_or_url: str, name: str, config: RunnableConfig = None) -> tuple[str, UniMessage]:
    """发送文件工具，支持本地路径或远程 URL
    Args:
        path_or_url: 本地文件的绝对路径（如 /tmp/report.pdf）或远程 URL
        name: 文件显示名称（含扩展名，如 report.pdf）
    """
    workspace_dir = ((config or {}).get("configurable") or {}).get("workspace_dir")
    if path := _resolve_message_local_path(path_or_url, workspace_dir):
        return f"构建了一个文件消息：{name}", UniMessage.file(path=path, name=name)
    validate_url(path_or_url)
    return f"构建了一个文件消息：{name}", UniMessage.file(url=path_or_url, name=name)


def _message_seq(response) -> str:
    seq = getattr(response, "message_seq", None)
    if seq is None and isinstance(response, dict):
        seq = response.get("message_seq")
    return f"，message_seq={seq}" if seq is not None else ""


def _mention(user_id: str | int) -> MessageSegment:
    return MessageSegment.mention(int(user_id))


@tool(response_format="content")
async def send_at(
    user_id: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """@ 某个用户
    Args:
        user_id: 目标用户的 QQ 号或用户 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[_mention(user_id)],
    )
    return f"已在群 {resolved_group_id} @ {user_id}{_message_seq(response)}"


@tool(response_format="content")
async def send_at_all(
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """@ 全体成员
    Args:
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[MessageSegment.mention_all()],
    )
    return f"已在群 {resolved_group_id} @全体成员{_message_seq(response)}"


@tool(response_format="content")
async def send_text_with_at(
    user_id: str,
    text: str,
    group_id: int | None = None,
    config: RunnableConfig = None,
) -> str:
    """@ 某个用户并附带文字内容，适合回复或提醒特定用户
    Args:
        user_id: 目标用户的 QQ 号或用户 ID
        text: 附带的文字内容
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        return error
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[_mention(user_id), MessageSegment.text(f" {text}")],
    )
    return f"已在群 {resolved_group_id} @ {user_id} 并发送消息{_message_seq(response)}"
