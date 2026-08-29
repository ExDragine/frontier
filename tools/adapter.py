from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlparse

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot, logger
from nonebot.adapters.milky.message import MessageSegment

from utils.alconna import UniMessage
from utils.milky_tools import (
    resolve_group_id,
    resolve_local_path,
    resolve_user_id,
    resolve_virtual_path,
    validate_url,
)

_DEFAULT_CONFIG = cast(RunnableConfig, None)


def _resolve_message_local_path(source: str, workspace_dir: str | None):
    path = resolve_local_path(source, workspace_dir)
    if path is not None or workspace_dir is not None:
        return path
    direct_path = Path(source)
    return direct_path if direct_path.is_file() else None


@tool(response_format="content_and_artifact")
async def send_image(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage]:
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
async def send_audio(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage]:
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
async def send_voice(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage]:
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
async def send_video(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage]:
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


def _safe_file_name(name: str | None, path_or_url: str, local_path: Path | None) -> str:
    candidate = (name or "").strip()
    if not candidate and local_path is not None:
        candidate = local_path.name
    if not candidate:
        candidate = Path(unquote(urlparse(path_or_url).path)).name
    return Path(candidate.replace("\\", "/")).name or "attachment"


@tool(response_format="content")
async def send_file(
    path_or_url: str,
    name: str | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """向当前 QQ 会话上传文件，并在平台确认成功后返回结果。

    Args:
        path_or_url: Agent 工作区虚拟路径（含 /memory/...）或远程 HTTP(S) URL
        name: 可选文件显示名称；默认从路径或 URL 提取
    """
    config_dict = dict(config or {})
    configurable = config_dict.get("configurable") or {}
    virtual_roots = configurable.get("virtual_roots")
    if not isinstance(virtual_roots, dict):
        workspace_dir = configurable.get("workspace_dir")
        virtual_roots = {"/": workspace_dir} if workspace_dir else {}

    local_path = resolve_virtual_path(path_or_url, virtual_roots) if virtual_roots else None
    upload_kwargs: dict[str, str]
    if local_path is not None:
        upload_kwargs = {"path": str(local_path)}
    else:
        try:
            validate_url(path_or_url)
        except ValueError:
            return "文件发送失败：路径不存在、超出当前工作区，或不是有效的 HTTP(S) URL。"
        upload_kwargs = {"url": path_or_url}

    file_name = _safe_file_name(name, path_or_url, local_path)
    try:
        bot = get_bot()
        raw_group_id = configurable.get("group_id")
        if raw_group_id not in (None, ""):
            group_id, error = resolve_group_id(config=config_dict)
            if error:
                return error
            file_id = await bot.upload_group_file(
                group_id=group_id,
                **upload_kwargs,
                file_name=file_name,
            )
            return f"已发送群文件 {file_name}，file_id={file_id}"

        user_id, error = resolve_user_id(config=config_dict)
        if error:
            return error
        file_id = await bot.upload_private_file(
            user_id=user_id,
            **upload_kwargs,
            file_name=file_name,
        )
        return f"已发送私聊文件 {file_name}，file_id={file_id}"
    except Exception as exc:
        logger.warning("发送文件失败: %s", type(exc).__name__)
        return "文件发送失败：平台上传未成功，请检查文件是否仍存在以及机器人权限。"


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
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """@ 某个用户
    Args:
        user_id: 目标用户的 QQ 号或用户 ID
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, dict(config or {}))
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
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """@ 全体成员
    Args:
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, dict(config or {}))
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
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """@ 某个用户并附带文字内容，适合回复或提醒特定用户
    Args:
        user_id: 目标用户的 QQ 号或用户 ID
        text: 附带的文字内容
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id, error = resolve_group_id(group_id, dict(config or {}))
    if error:
        return error
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[_mention(user_id), MessageSegment.text(f" {text}")],
    )
    return f"已在群 {resolved_group_id} @ {user_id} 并发送消息{_message_seq(response)}"
