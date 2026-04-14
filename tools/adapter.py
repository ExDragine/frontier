from pathlib import Path
from urllib.parse import urlparse

from langchain.tools import tool
from nonebot import require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402


def _is_local(source: str) -> bool:
    return Path(source).is_file()


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"无效的 URL：{url!r}，仅支持 http/https")


@tool(response_format="content_and_artifact")
async def send_image(source: str) -> tuple[str, UniMessage]:
    """发送图片工具，支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/photo.png）或远程 URL
    """
    if _is_local(source):
        return "构建了一个图片消息", UniMessage.image(path=Path(source))
    _validate_url(source)
    return "构建了一个图片消息", UniMessage.image(url=source)


@tool(response_format="content_and_artifact")
async def send_audio(source: str) -> tuple[str, UniMessage]:
    """发送音频文件工具（以文件形式呈现，区别于语音），支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/music.mp3）或远程 URL
    """
    if _is_local(source):
        return "构建了一个音频消息", UniMessage.audio(path=Path(source))
    _validate_url(source)
    return "构建了一个音频消息", UniMessage.audio(url=source)


@tool(response_format="content_and_artifact")
async def send_voice(source: str) -> tuple[str, UniMessage]:
    """发送语音消息工具（以对讲/语音条形式呈现），支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/voice.wav）或远程 URL
    """
    if _is_local(source):
        return "构建了一个语音消息", UniMessage.voice(path=Path(source))
    _validate_url(source)
    return "构建了一个语音消息", UniMessage.voice(url=source)


@tool(response_format="content_and_artifact")
async def send_video(source: str) -> tuple[str, UniMessage]:
    """发送视频工具，支持本地路径或远程 URL
    Args:
        source: 本地文件的绝对路径（如 /tmp/clip.mp4）或远程 URL
    """
    if _is_local(source):
        return "构建了一个视频消息", UniMessage.video(path=Path(source))
    _validate_url(source)
    return "构建了一个视频消息", UniMessage.video(url=source)


@tool(response_format="content_and_artifact")
async def send_emoji(emoji_id: str) -> tuple[str, UniMessage]:
    """发送 QQ 表情工具
    Args:
        emoji_id: 表情ID
    """
    return "构建了一个表情消息", UniMessage.emoji(id=emoji_id)


@tool(response_format="content_and_artifact")
async def send_file(path_or_url: str, name: str) -> tuple[str, UniMessage]:
    """发送文件工具，支持本地路径或远程 URL
    Args:
        path_or_url: 本地文件的绝对路径（如 /tmp/report.pdf）或远程 URL
        name: 文件显示名称（含扩展名，如 report.pdf）
    """
    if _is_local(path_or_url):
        return f"构建了一个文件消息：{name}", UniMessage.file(path=Path(path_or_url), name=name)
    _validate_url(path_or_url)
    return f"构建了一个文件消息：{name}", UniMessage.file(url=path_or_url, name=name)


@tool(response_format="content_and_artifact")
async def send_at(user_id: str) -> tuple[str, UniMessage]:
    """@ 某个用户
    Args:
        user_id: 目标用户的 QQ 号或用户 ID
    """
    return f"构建了一个 @{user_id} 消息", UniMessage.at(user_id)


@tool(response_format="content_and_artifact")
async def send_at_all() -> tuple[str, UniMessage]:
    """@ 全体成员"""
    return "构建了一个 @全体成员 消息", UniMessage.at_all()


@tool(response_format="content_and_artifact")
async def send_text_with_at(user_id: str, text: str) -> tuple[str, UniMessage]:
    """@ 某个用户并附带文字内容，适合回复或提醒特定用户
    Args:
        user_id: 目标用户的 QQ 号或用户 ID
        text: 附带的文字内容
    """
    msg: UniMessage = UniMessage.at(user_id)
    msg.extend(UniMessage.text(f" {text}"))
    return f"构建了一条 @{user_id} 的消息", msg
