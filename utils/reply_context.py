import importlib
import json
import re

from nonebot import logger
from nonebot.adapters.milky.event import MessageEvent

from utils.configs import EnvConfig
from utils.database import MESSAGE_SOURCE_TYPE_NORMAL, MessageDatabase
from utils.http_client import get_http_client
from utils.message_normalizer import NORMALIZED_VERSION, normalize_segments, segments_to_raw_json

_httpx_client = get_http_client("reply_context")
FORWARD_CONTEXT_MAX_DEPTH = 3
FORWARD_CONTEXT_MAX_NODES = 80


def _message_utils():
    return importlib.import_module("utils.message")


def reply_seq_from_segments(segments: list[dict]) -> int | None:
    for segment in segments:
        if segment.get("type") != "reply":
            continue
        message_seq = segment.get("data", {}).get("message_seq")
        try:
            return int(message_seq)
        except TypeError, ValueError:
            return None
    return None


def strip_reply_marker(text: str, reply_seq: int) -> str:
    marker = f"[回复消息:{reply_seq}]"
    if text.startswith(marker):
        return text[len(marker) :].lstrip()
    return text.replace(marker, "", 1).lstrip()


def _sender_name_from_milky_message(message) -> str:
    if getattr(message, "group_member", None) and message.group_member.nickname:
        return message.group_member.nickname
    if getattr(message, "friend", None) and message.friend.nickname:
        return message.friend.nickname
    return str(message.sender_id)


def _strip_resolved_image_markers(text: str, image_count: int) -> str:
    """移除已经作为多模态内容附加的图片标记。"""
    cleaned = re.sub(r"\[图片(?::[^\]\n]*)?\]", "", text, count=image_count)
    return "\n".join(line.rstrip() for line in cleaned.splitlines() if line.strip()).strip()


def _format_quote(role: str, name: str | None, text: str, image_count: int, missing_images: int) -> str:
    handled_images = image_count + missing_images
    if handled_images:
        text = _strip_resolved_image_markers(text, handled_images)
    content_parts = []
    if text.strip():
        content_parts.append(text.strip())
    if image_count:
        content_parts.append(f"[下方已附加引用图片 {image_count} 张]")
    if missing_images:
        content_parts.append(" ".join("[引用消息包含图片，但图片已失效]" for _ in range(missing_images)))
    content = "\n".join(content_parts) if content_parts else "[空消息]"
    role_label = "助手" if role == "assistant" else "用户"
    return f"\n\n[引用消息]\n{role_label}({name or '未知'}): {content}"


async def _fetch_reply_message_from_milky(bot, event: MessageEvent, reply_seq: int):
    event_reply = getattr(event, "reply", None)
    if event_reply and getattr(event_reply, "message_seq", None) == reply_seq:
        return event_reply
    try:
        return await bot.get_message(
            message_scene=event.data.message_scene,
            peer_id=event.data.peer_id,
            message_seq=reply_seq,
        )
    except Exception as e:
        logger.warning(f"⚠️ 拉取引用消息失败 message_seq={reply_seq}: {type(e).__name__}: {e}")
        return None


async def _download_image_from_url(url: str) -> bytes | None:
    """下载引用消息中的图片，失败返回 None。"""
    try:
        return (await _httpx_client.get(url)).content
    except Exception as e:
        logger.warning(f"⚠️ 下载引用图片失败 url={url}: {type(e).__name__}: {e}")
        return None


async def _download_milky_image(bot, segment: dict) -> bytes | None:
    data = segment.get("data", {})
    tried_urls: set[str] = set()
    if temp_url := data.get("temp_url"):
        tried_urls.add(temp_url)
        if image := await _download_image_from_url(temp_url):
            return image

    resource_id = data.get("resource_id")
    if not resource_id:
        return None
    try:
        resource_url = await bot.get_resource_temp_url(resource_id=resource_id)
    except Exception as e:
        logger.warning(f"⚠️ 刷新引用图片链接失败 resource_id={resource_id}: {type(e).__name__}: {e}")
        return None
    if resource_url in tried_urls:
        return None
    return await _download_image_from_url(resource_url)


def _forward_marker(data: dict) -> str:
    title = data.get("title", "")
    summary = data.get("summary", "")
    if title or summary:
        return f"[合并转发:{title} - {summary}]"
    return "[合并转发]"


async def _extract_forward_segment_content(bot, segment: dict, depth: int) -> tuple[str, list[bytes], int]:
    data = segment.get("data", {})
    marker = _forward_marker(data)
    forward_id = data.get("forward_id")
    if not forward_id:
        return marker, [], 0
    if depth >= FORWARD_CONTEXT_MAX_DEPTH:
        return f"{marker}\n[合并转发展开已达到深度限制]", [], 0

    try:
        nodes = await bot.get_forwarded_messages(forward_id=forward_id)
    except Exception as e:
        logger.warning(f"⚠️ 拉取合并转发失败 forward_id={forward_id}: {type(e).__name__}: {e}")
        return f"{marker}\n[合并转发内容拉取失败]", [], 0

    lines = [marker]
    images: list[bytes] = []
    missing_images = 0
    for node in list(nodes)[:FORWARD_CONTEXT_MAX_NODES]:
        node_text, node_images, node_missing = await _extract_segments_content(
            bot,
            getattr(node, "segments", []),
            depth=depth + 1,
        )
        images.extend(node_images)
        missing_images += node_missing
        sender_name = getattr(node, "sender_name", None) or "未知"
        content = node_text.strip() or "[空消息]"
        lines.append(f"{sender_name}: {content}")
    if len(nodes) > FORWARD_CONTEXT_MAX_NODES:
        lines.append(f"[合并转发还有 {len(nodes) - FORWARD_CONTEXT_MAX_NODES} 条，已省略]")
    return "\n".join(lines), images, missing_images


async def _extract_segments_content(bot, segments: list[dict], *, depth: int = 0) -> tuple[str, list[bytes], int]:
    text_parts: list[str] = []
    images: list[bytes] = []
    missing_images = 0

    for segment in segments:
        segment_type = segment.get("type")
        if segment_type == "image":
            if image := await _download_milky_image(bot, segment):
                images.append(image)
            else:
                missing_images += 1
            continue
        if segment_type == "forward":
            forward_text, forward_images, forward_missing = await _extract_forward_segment_content(bot, segment, depth)
            text_parts.append(forward_text)
            images.extend(forward_images)
            missing_images += forward_missing
            continue
        if segment_type == "record":
            duration = segment.get("data", {}).get("duration", 0)
            text_parts.append(f"[语音:{duration}秒]")
            continue
        if segment_type == "video":
            duration = segment.get("data", {}).get("duration", 0)
            text_parts.append(f"[视频:{duration}秒]")
            continue

        text, *_ = await _message_utils().message_extract([segment])
        if text:
            text_parts.append(text)

    return "\n".join(part for part in text_parts if part), images, missing_images


async def _extract_milky_message_content(bot, message) -> tuple[str, list[bytes], int]:
    return await _extract_segments_content(bot, message.segments)


def _quoted_needs_normalization_rebuild(quoted) -> bool:
    status = getattr(quoted, "normalized_status", "legacy")
    if getattr(quoted, "normalized_version", 0) >= NORMALIZED_VERSION and status == "complete":
        return False
    if getattr(quoted, "raw_segments_json", None):
        return True
    content = getattr(quoted, "content", "") or ""
    if "[合并转发:" in content or "[合并转发]" in content:
        return True
    return status not in ("complete", "legacy")


async def _rebuild_quoted_normalization(
    bot, event: MessageEvent, quoted, reply_seq: int, messages_db: MessageDatabase
):
    raw_segments_json = getattr(quoted, "raw_segments_json", None)
    segments = None
    if raw_segments_json:
        try:
            loaded = json.loads(raw_segments_json)
            if isinstance(loaded, list):
                segments = loaded
        except json.JSONDecodeError:
            segments = None

    milky_message = None
    if segments is None:
        milky_message = await _fetch_reply_message_from_milky(bot, event, reply_seq)
        if not milky_message:
            return quoted
        segments = milky_message.segments
        raw_segments_json = segments_to_raw_json(segments)

    normalized = await normalize_segments(bot, segments)
    await messages_db.update_message_normalization(
        time=quoted.time,
        content=normalized.content,
        raw_segments_json=raw_segments_json,
        normalized_version=normalized.normalized_version,
        normalized_status=normalized.status,
    )
    await messages_db.replace_derived_messages(
        parent_msg_time=quoted.time,
        parent_msg_id=quoted.msg_id,
        user_id=quoted.user_id,
        group_id=quoted.group_id,
        role=quoted.role,
        derived_messages=normalized.derived_messages,
        normalized_version=NORMALIZED_VERSION,
    )
    quoted.content = normalized.content
    quoted.raw_segments_json = raw_segments_json
    quoted.normalized_version = normalized.normalized_version
    quoted.normalized_status = normalized.status
    quoted.source_type = MESSAGE_SOURCE_TYPE_NORMAL
    return quoted


async def build_reply_context(  # noqa: C901
    bot,
    event: MessageEvent,
    reply_seq: int,
    group_id: int | None,
    messages_db: MessageDatabase,
    *,
    load_images: bool = True,
) -> tuple[str, list[bytes]]:
    quoted = await messages_db.select_by_msg_id(msg_id=reply_seq, group_id=group_id)
    if quoted:
        if _quoted_needs_normalization_rebuild(quoted):
            quoted = await _rebuild_quoted_normalization(bot, event, quoted, reply_seq, messages_db)
        if not load_images:
            return _format_quote(quoted.role, quoted.user_name or str(quoted.user_id), quoted.content, 0, 0), []

        image_records = await messages_db.select_image_attachments_by_msg_time(quoted.time)
        local_images, missing_images = messages_db.load_attachment_files(image_records)
        fetched_images: list[bytes] = []
        fetched_missing = 0
        # 没有附件记录不代表引用消息没有图片：未触发 Agent 的群消息只会
        # 存储文本占位符，因此仍需回源 Milky。损坏缓存同样以远端消息为准。
        if not image_records or missing_images:
            milky_message = await _fetch_reply_message_from_milky(bot, event, reply_seq)
            if milky_message:
                _quoted_text, fetched_images, fetched_missing = await _extract_milky_message_content(bot, milky_message)
                if fetched_images and EnvConfig.IMAGE_ENABLED:
                    try:
                        await messages_db.insert_images(
                            msg_time=quoted.time,
                            user_id=quoted.user_id,
                            group_id=quoted.group_id,
                            images=fetched_images,
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ 重建引用图片缓存失败 message_seq={reply_seq}: {type(e).__name__}: {e}")
            elif not image_records:
                missing_images = len(re.findall(r"\[图片(?::[^\]\n]*)?\]", quoted.content))
        if fetched_images:
            # 回源会返回引用消息中的完整图片集合，不能再与部分本地缓存拼接，
            # 否则已有图片会重复传给模型。
            images = fetched_images
            missing_images = fetched_missing
        else:
            images = local_images
            missing_images += fetched_missing
        return (
            _format_quote(
                quoted.role, quoted.user_name or str(quoted.user_id), quoted.content, len(images), missing_images
            ),
            images,
        )

    milky_message = await _fetch_reply_message_from_milky(bot, event, reply_seq)
    if not milky_message:
        return "", []

    normalized = await normalize_segments(bot, milky_message.segments)
    quoted_text = normalized.content
    if load_images:
        _image_text, images, missing_images = await _extract_milky_message_content(bot, milky_message)
    else:
        images, missing_images = [], 0
    role = "assistant" if str(milky_message.sender_id) == str(event.self_id) else "user"
    name = _sender_name_from_milky_message(milky_message)
    quoted_time = milky_message.time * 1000 if milky_message.time < 10_000_000_000 else milky_message.time
    try:
        await messages_db.insert(
            time=quoted_time,
            msg_id=milky_message.message_seq,
            user_id=int(milky_message.sender_id),
            group_id=group_id,
            user_name=name,
            role=role,
            content=quoted_text,
            raw_segments_json=normalized.raw_segments_json,
            normalized_version=normalized.normalized_version,
            normalized_status=normalized.status,
        )
        if normalized.derived_messages:
            await messages_db.replace_derived_messages(
                parent_msg_time=quoted_time,
                parent_msg_id=milky_message.message_seq,
                user_id=int(milky_message.sender_id),
                group_id=group_id,
                role=role,
                derived_messages=normalized.derived_messages,
                normalized_version=NORMALIZED_VERSION,
            )
    except Exception as e:
        logger.warning(f"⚠️ 写入引用消息记录失败 message_seq={reply_seq}: {type(e).__name__}: {e}")
    if load_images and images and EnvConfig.IMAGE_ENABLED:
        try:
            await messages_db.insert_images(
                msg_time=quoted_time,
                user_id=int(milky_message.sender_id),
                group_id=group_id,
                images=images,
            )
        except Exception as e:
            logger.warning(f"⚠️ 写入引用图片缓存失败 message_seq={reply_seq}: {type(e).__name__}: {e}")
    return _format_quote(role, name, quoted_text, len(images), missing_images), images
