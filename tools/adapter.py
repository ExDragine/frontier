from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlparse

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot, logger
from nonebot.adapters.milky.message import MessageSegment

from utils.alconna import UniMessage
from utils.milky_tools import (
    configurable,
    input_error_text,
    require_group_id,
    require_user_id,
    resolve_local_path,
    resolve_virtual_path,
    validate_url,
)

_DEFAULT_CONFIG = cast(RunnableConfig, None)
_MEDIA_SOURCE_ERROR = (
    "媒体消息未加入回复：路径不存在、超出当前会话挂载范围，或不是有效的 HTTP(S) URL。"
    "请使用已确认存在的虚拟路径或 URL；若生成工具已返回工件，无需再次发送，直接完成最终回复。"
)


def _resolve_message_source(source: str, config: RunnableConfig) -> tuple[Path | None, str | None]:
    """Validate a source before constructing an artifact; no platform write occurs here."""
    try:
        validate_url(source)
    except ValueError:
        if "://" in source or source.startswith(("//", "\\\\")):
            return None, None
    else:
        return None, source
    settings = configurable(dict(config or {}))
    virtual_roots = settings.get("virtual_roots")
    workspace_dir = settings.get("workspace_dir")
    try:
        if isinstance(virtual_roots, dict):
            path = resolve_virtual_path(source, virtual_roots)
        elif workspace_dir is not None:
            path = resolve_virtual_path(source, {"/": workspace_dir})
        else:
            path = resolve_local_path(source)
            if path is None:
                direct_path = Path(source)
                path = direct_path if direct_path.is_file() else None
    except (OSError, ValueError):
        path = None
    return path, None


@tool(response_format="content_and_artifact")
async def send_image(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage | None]:
    """将已有图片加入本轮最终回复，由系统在本轮结束后自动发送。

    get_paint 已返回的图片工件会自动发送，无需再调用本工具，也不要编造图片路径。

    Args:
        source: 已存在的 Agent 虚拟路径（如 /photo.png、/memory/...）或 HTTP(S) URL
    """
    path, url = _resolve_message_source(source, config)
    if path is None and url is None:
        return _MEDIA_SOURCE_ERROR, None
    return "构建了一个图片消息，将在本轮结束后自动发送", UniMessage.image(path=path, url=url)


@tool(response_format="content_and_artifact")
async def send_audio(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage | None]:
    """将已有音频加入本轮最终回复（以文件形式呈现），由系统在本轮结束后自动发送。

    Args:
        source: 已存在的 Agent 虚拟路径（如 /music.mp3、/memory/...）或 HTTP(S) URL
    """
    path, url = _resolve_message_source(source, config)
    if path is None and url is None:
        return _MEDIA_SOURCE_ERROR, None
    return "构建了一个音频消息，将在本轮结束后自动发送", UniMessage.audio(path=path, url=url)


@tool(response_format="content_and_artifact")
async def send_voice(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage | None]:
    """将已有语音加入本轮最终回复（以语音条呈现），由系统在本轮结束后自动发送。

    Args:
        source: 已存在的 Agent 虚拟路径（如 /voice.wav、/memory/...）或 HTTP(S) URL
    """
    path, url = _resolve_message_source(source, config)
    if path is None and url is None:
        return _MEDIA_SOURCE_ERROR, None
    return "构建了一个语音消息，将在本轮结束后自动发送", UniMessage.voice(path=path, url=url)


@tool(response_format="content_and_artifact")
async def send_video(source: str, config: RunnableConfig = _DEFAULT_CONFIG) -> tuple[str, UniMessage | None]:
    """将已有视频加入本轮最终回复，由系统在本轮结束后自动发送。

    get_video 已返回的视频工件会自动发送，无需再调用本工具，也不要编造视频路径。

    Args:
        source: 已存在的 Agent 虚拟路径（如 /clip.mp4、/memory/...）或 HTTP(S) URL
    """
    path, url = _resolve_message_source(source, config)
    if path is None and url is None:
        return _MEDIA_SOURCE_ERROR, None
    return "构建了一个视频消息，将在本轮结束后自动发送", UniMessage.video(path=path, url=url)


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
@input_error_text
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
    configurable_section = configurable(config_dict)
    virtual_roots = configurable_section.get("virtual_roots")
    if not isinstance(virtual_roots, dict):
        workspace_dir = configurable_section.get("workspace_dir")
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
        raw_group_id = configurable_section.get("group_id")
        if raw_group_id not in (None, ""):
            group_id = require_group_id(config=config_dict)
            file_id = await bot.upload_group_file(
                group_id=group_id,
                **upload_kwargs,
                file_name=file_name,
            )
            return f"已发送群文件 {file_name}，file_id={file_id}"

        user_id = require_user_id(config=config_dict)
        file_id = await bot.upload_private_file(
            user_id=user_id,
            **upload_kwargs,
            file_name=file_name,
        )
        return f"已发送私聊文件 {file_name}，file_id={file_id}"
    except Exception as exc:
        logger.warning("发送文件失败: {}", type(exc).__name__)
        return "文件发送失败：平台上传未成功，请检查文件是否仍存在以及机器人权限。"


def _message_seq(response) -> str:
    seq = getattr(response, "message_seq", None)
    if seq is None and isinstance(response, dict):
        seq = response.get("message_seq")
    return f"，message_seq={seq}" if seq is not None else ""


def _mention(user_id: str | int) -> MessageSegment:
    return MessageSegment.mention(int(user_id))


@tool(response_format="content")
@input_error_text
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
    resolved_group_id = require_group_id(group_id, config)
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[_mention(user_id)],
    )
    return f"已在群 {resolved_group_id} @ {user_id}{_message_seq(response)}"


@tool(response_format="content")
@input_error_text
async def send_at_all(
    group_id: int | None = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
) -> str:
    """@ 全体成员
    Args:
        group_id: 可选群号，未传时使用当前群聊
    """
    resolved_group_id = require_group_id(group_id, config)
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[MessageSegment.mention_all()],
    )
    return f"已在群 {resolved_group_id} @全体成员{_message_seq(response)}"


@tool(response_format="content")
@input_error_text
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
    resolved_group_id = require_group_id(group_id, config)
    response = await get_bot().send_group_message(
        group_id=resolved_group_id,
        message=[_mention(user_id), MessageSegment.text(f" {text}")],
    )
    return f"已在群 {resolved_group_id} @ {user_id} 并发送消息{_message_seq(response)}"
