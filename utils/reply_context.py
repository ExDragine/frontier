import importlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from nonebot import logger
from nonebot.adapters.milky.event import MessageEvent

from utils.agents.message_envelope import (
    build_agent_attachment_payload,
    build_agent_message_ref_payload,
    content_for_persisted_images,
)
from utils.agents.runtime import conversation_workspace_key
from utils.configs import EnvConfig
from utils.database import MESSAGE_SOURCE_TYPE_NORMAL, MessageDatabase, resolve_message_sender_user_id
from utils.http_client import get_http_client
from utils.message_normalizer import NORMALIZED_VERSION, normalize_segments, segments_to_raw_json

_httpx_client = get_http_client("reply_context")
FORWARD_CONTEXT_MAX_DEPTH = 3
FORWARD_CONTEXT_MAX_NODES = 80
RECENT_MEDIA_LOOKBACK_MILLISECONDS = 5 * 60 * 1000
RECENT_MEDIA_MESSAGE_LIMIT = 20
_RECENT_MEDIA_FOLLOWUP_RE = re.compile(
    r"(?:分析|解析|识别|总结|读取|提取|看看|看下|看一下|处理|解释|"
    r"这张图|那张图|这个文件|那个文件|上面的|刚才的|刚刚的|上一条|"
    r"analy[sz]e|summari[sz]e|extract|read\s+(?:it|this)|take\s+a\s+look)",
    re.IGNORECASE,
)


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


def requests_recent_media(text: str) -> bool:
    """Whether a media-free message likely refers to recently sent media."""
    return bool(_RECENT_MEDIA_FOLLOWUP_RE.search(text.strip()))


async def hydrate_recent_media_context(
    bot,
    event: MessageEvent,
    *,
    user_id: int,
    group_id: int | None,
    before_time: int,
    messages_db: MessageDatabase,
    workspace_key: str,
    memory_dir: str | Path,
) -> tuple[list[bytes], bool]:
    """Lazily restore the newest same-sender image/file message.

    The explicit-reply hydration path remains the single downloader and cache
    writer. Its model-facing quote payload is intentionally discarded here;
    after hydration the original historical message is rendered again from the
    attachment index, preserving its actual platform relationship.
    """
    select_recent = getattr(messages_db, "select_recent_media_message", None)
    if not callable(select_recent):
        return [], False
    recent = await select_recent(
        user_id=user_id,
        group_id=group_id,
        before_time=before_time,
        after_time=before_time - RECENT_MEDIA_LOOKBACK_MILLISECONDS,
        limit=RECENT_MEDIA_MESSAGE_LIMIT,
    )
    if recent is None or recent.msg_id is None:
        return [], False
    _payload, images = await build_reply_context(
        bot,
        event,
        int(recent.msg_id),
        group_id,
        messages_db,
        workspace_key=workspace_key,
        memory_dir=memory_dir,
    )
    return images, True


def sender_names_from_milky_message(message) -> tuple[str, str | None, str | None]:
    """Return display name, nickname and group card for a Milky message."""
    member = getattr(message, "group_member", None)
    if member is not None:
        nickname = str(getattr(member, "nickname", "") or "").strip() or None
        card = str(getattr(member, "card", "") or "").strip() or None
        return card or nickname or str(message.sender_id), nickname, card
    friend = getattr(message, "friend", None)
    nickname = str(getattr(friend, "nickname", "") or "").strip() or None
    return nickname or str(message.sender_id), nickname, None


def _strip_resolved_image_markers(text: str, image_count: int) -> str:
    """Only remove markers when every image segment is durably accounted for."""
    return content_for_persisted_images(text, image_count)


async def _cache_complete_reply_images(
    messages_db: MessageDatabase,
    *,
    msg_time: int,
    user_id: int,
    group_id: int | None,
    images: list[bytes],
    missing_images: int,
    reply_seq: int,
) -> bool:
    """Persist only complete image sets so attachment ordinals cannot drift."""
    if not images or missing_images or not EnvConfig.IMAGE_ENABLED:
        return False
    try:
        await messages_db.insert_images(
            msg_time=msg_time,
            user_id=user_id,
            group_id=group_id,
            images=images,
        )
    except Exception as exc:
        logger.warning(
            "⚠️ 写入引用图片缓存失败 message_seq=%s: %s: %s",
            reply_seq,
            type(exc).__name__,
            exc,
        )
        return False
    return True


def _format_quote(
    *,
    message_id: int,
    role: str,
    user_id: int | None,
    display_name: str | None,
    nickname: str | None,
    card: str | None,
    text: str,
    image_count: int,
    missing_images: int,
    attachments: list[dict[str, object]] | None = None,
    missing_files: int = 0,
) -> dict[str, object]:
    handled_images = image_count + missing_images
    if handled_images:
        text = _strip_resolved_image_markers(text, handled_images)
    content_parts = []
    if text.strip():
        content_parts.append(text.strip())
    if image_count:
        content_parts.append(f"[引用消息包含图片 {image_count} 张]")
    if missing_images:
        content_parts.append(" ".join("[引用消息包含图片，但图片已失效]" for _ in range(missing_images)))
    if missing_files:
        content_parts.append(f"[引用消息有 {missing_files} 个文件已失效或无法下载]")
    content = "\n".join(content_parts) if content_parts else "[空消息]"
    return build_agent_message_ref_payload(
        message_id=message_id,
        role=role,
        user_id=user_id,
        display_name=display_name,
        nickname=nickname,
        card=card,
        content=content,
        image_count=image_count,
        missing_image_count=missing_images,
        attachments=attachments,
    )


def _raw_segments(quoted) -> list[dict] | None:
    raw_segments_json = getattr(quoted, "raw_segments_json", None)
    if not raw_segments_json:
        return None
    try:
        loaded = json.loads(raw_segments_json)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, list) else None


def _attachment_local_path(record) -> Path:
    path = Path(str(record.physical_path))
    return path if path.is_absolute() else Path.cwd() / path


def _file_attachment_ref(record) -> dict[str, object]:
    return dict(
        build_agent_attachment_payload(
            kind="file",
            mime_type=getattr(record, "mime_type", None),
            file_name=record.file_name,
            path=record.virtual_path,
        )
    )


async def _select_quoted_file_records(messages_db: MessageDatabase, msg_time: int) -> list:
    select_all = getattr(messages_db, "select_attachments_by_msg_time", None)
    if not callable(select_all):
        return []
    return [record for record in await select_all(msg_time) if getattr(record, "kind", None) == "file"]


def _refreshable_quoted_file_item(item, group_id: int | None):
    can_refresh = bool(item.file_id) and (group_id is not None or item.file_hash is not None)
    if not can_refresh:
        return item
    return _message_utils().MessageFileItem(
        file_id=item.file_id,
        file_name=item.file_name,
        file_size=item.file_size,
        file_hash=item.file_hash,
        url=None,
    )


async def _quoted_file_context(  # noqa: C901
    bot,
    event: MessageEvent,
    reply_seq: int,
    messages_db: MessageDatabase,
    quoted,
    *,
    segments: list[dict] | None = None,
    workspace_key: str | None = None,
    memory_dir: str | Path | None = None,
) -> tuple[list[dict[str, object]], int]:
    """Return readable quoted-file refs, refreshing missing files from Milky."""
    workspace_key = workspace_key or conversation_workspace_key(quoted.user_id, quoted.group_id)
    records = await _select_quoted_file_records(messages_db, quoted.time)
    now_ms = int(time.time() * 1000)
    available_records = [
        record
        for record in records
        if getattr(record, "workspace_key", workspace_key) == workspace_key
        and getattr(record, "expires_at", now_ms) >= now_ms
        and _attachment_local_path(record).is_file()
    ]
    refs = [_file_attachment_ref(record) for record in available_records]

    segments = segments or _raw_segments(quoted)
    marker_count = len(re.findall(r"\[文件:[^\]\n]*\]", str(getattr(quoted, "content", ""))))
    if segments is None and (len(available_records) < len(records) or marker_count > len(refs)):
        milky_message = await _fetch_reply_message_from_milky(bot, event, reply_seq)
        segments = list(getattr(milky_message, "segments", [])) if milky_message else None
    file_items = _message_utils().extract_message_files(segments or [])
    expected_count = len(file_items) if file_items else max(marker_count, len(records))
    available_names = Counter(str(record.file_name) for record in available_records)
    pending_items = []
    for item in file_items:
        safe_name = Path(str(item.file_name).replace("\\", "/")).name.strip() or "file"
        if available_names[safe_name]:
            available_names[safe_name] -= 1
            continue
        pending_items.append(_refreshable_quoted_file_item(item, quoted.group_id))

    if pending_items:
        resolved_memory_dir = (
            Path(memory_dir) if memory_dir is not None else Path.cwd() / "cache" / "sandbox" / "memory" / workspace_key
        )
        staged_files = await _message_utils().stage_message_files(
            bot,
            pending_items,
            memory_dir=resolved_memory_dir,
            workspace_key=workspace_key,
            message_time=quoted.time,
            user_id=quoted.user_id,
            group_id=quoted.group_id,
        )
        insert_attachment = getattr(messages_db, "insert_attachment", None)
        expires_at = now_ms + EnvConfig.MEDIA_TTL_DAYS * 86400 * 1000
        for staged_file in staged_files:
            if not callable(insert_attachment):
                _message_utils().cleanup_staged_message_files([staged_file])
                continue
            try:
                await insert_attachment(
                    msg_time=quoted.time,
                    msg_id=quoted.msg_id,
                    user_id=quoted.user_id,
                    group_id=quoted.group_id,
                    kind="file",
                    physical_path=str(staged_file.local_path),
                    virtual_path=staged_file.virtual_path,
                    file_name=staged_file.file_name,
                    mime_type=staged_file.mime_type,
                    file_size=staged_file.file_size,
                    sha256=staged_file.sha256,
                    expires_at=expires_at,
                )
            except Exception as exc:
                logger.warning(
                    "⚠️ 写入引用文件缓存失败 message_seq=%s file=%s: %s: %s",
                    reply_seq,
                    staged_file.file_name,
                    type(exc).__name__,
                    exc,
                )
                _message_utils().cleanup_staged_message_files([staged_file])
            else:
                refs.append(
                    dict(
                        build_agent_attachment_payload(
                            kind="file",
                            mime_type=staged_file.mime_type,
                            file_name=staged_file.file_name,
                            path=staged_file.virtual_path,
                        )
                    )
                )

    unique_refs = {str(ref["path"]): ref for ref in refs}
    return list(unique_refs.values()), max(0, expected_count - len(unique_refs))


def _private_peer_user_id(event: MessageEvent) -> int | None:
    peer_id = getattr(getattr(event, "data", None), "peer_id", None)
    if peer_id is None:
        get_user_id = getattr(event, "get_user_id", None)
        peer_id = get_user_id() if callable(get_user_id) else None
    try:
        return int(peer_id) if peer_id is not None else None
    except TypeError, ValueError:
        return None


def segments_directly_mention_user(segments: list[dict], user_id: int | str) -> bool:
    return any(
        segment.get("type") == "mention"
        and str(segment.get("data", {}).get("user_id", "")) == str(user_id)
        for segment in segments
    )


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
    workspace_key: str | None = None,
    memory_dir: str | Path | None = None,
) -> tuple[dict[str, object] | None, list[bytes]]:
    select_kwargs: dict[str, object] = {"msg_id": reply_seq, "group_id": group_id}
    private_peer_user_id = _private_peer_user_id(event) if group_id is None else None
    if group_id is None and private_peer_user_id is None:
        logger.warning("忽略无法确定 peer_user_id 的私聊引用 message_seq=%s", reply_seq)
        return None, []
    if private_peer_user_id is not None:
        select_kwargs["peer_user_id"] = private_peer_user_id
    quoted = await messages_db.select_by_msg_id(**select_kwargs)
    if quoted:
        if _quoted_needs_normalization_rebuild(quoted):
            quoted = await _rebuild_quoted_normalization(bot, event, quoted, reply_seq, messages_db)
        if not load_images:
            return (
                _format_quote(
                    message_id=quoted.msg_id or reply_seq,
                    role=quoted.role,
                    user_id=resolve_message_sender_user_id(quoted),
                    display_name=quoted.user_name,
                    nickname=getattr(quoted, "user_nickname", None),
                    card=getattr(quoted, "user_card", None),
                    text=quoted.content,
                    image_count=0,
                    missing_images=0,
                ),
                [],
            )

        image_records = await messages_db.select_image_attachments_by_msg_time(quoted.time)
        local_images, missing_images = messages_db.load_attachment_files(image_records)
        durable_image_count = len(local_images)
        durable_missing_images = missing_images
        fetched_images: list[bytes] = []
        fetched_missing = 0
        fetched_segments: list[dict] | None = None
        loaded_raw_segments = _raw_segments(quoted)
        raw_segments = loaded_raw_segments or []
        has_quoted_images = any(segment.get("type") == "image" for segment in raw_segments) or bool(
            re.search(r"\[图片(?::[^\]\n]*)?\]", quoted.content)
        )
        image_presence_unknown = loaded_raw_segments is None and getattr(
            quoted, "normalized_status", "legacy"
        ) == "legacy"
        # 未触发 Agent 的群图片可能只有文本占位符，需回源 Milky。
        # 纯文本或纯文件引用不应因为“没有图片索引”而额外回源。
        if (not image_records and (has_quoted_images or image_presence_unknown)) or missing_images:
            if loaded_raw_segments is not None:
                fetched_segments = loaded_raw_segments
                _quoted_text, fetched_images, fetched_missing = await _extract_segments_content(
                    bot, fetched_segments
                )
                media_source_available = True
            else:
                milky_message = await _fetch_reply_message_from_milky(bot, event, reply_seq)
                media_source_available = milky_message is not None
                if milky_message:
                    fetched_segments = list(getattr(milky_message, "segments", []))
                    _quoted_text, fetched_images, fetched_missing = await _extract_milky_message_content(
                        bot, milky_message
                    )
            if media_source_available:
                if not image_records:
                    durable_missing_images = fetched_missing
                    cached = await _cache_complete_reply_images(
                        messages_db,
                        msg_time=quoted.time,
                        user_id=quoted.user_id,
                        group_id=quoted.group_id,
                        images=fetched_images,
                        missing_images=fetched_missing,
                        reply_seq=reply_seq,
                    )
                    durable_image_count = len(fetched_images) if cached else 0
                else:
                    # Existing partial rows keep their original ordinals. Do
                    # not overwrite them with a compacted successful subset.
                    durable_missing_images = max(durable_missing_images, fetched_missing)
            elif not image_records:
                durable_missing_images = len(re.findall(r"\[图片(?::[^\]\n]*)?\]", quoted.content))
        if fetched_images:
            # 回源会返回引用消息中的完整图片集合，不能再与部分本地缓存拼接，
            # 否则已有图片会重复传给模型。
            images = fetched_images
        else:
            images = local_images
        file_refs, missing_files = await _quoted_file_context(
            bot,
            event,
            reply_seq,
            messages_db,
            quoted,
            segments=fetched_segments,
            workspace_key=workspace_key,
            memory_dir=memory_dir,
        )
        return (
            _format_quote(
                message_id=quoted.msg_id or reply_seq,
                role=quoted.role,
                user_id=resolve_message_sender_user_id(quoted),
                display_name=quoted.user_name,
                nickname=getattr(quoted, "user_nickname", None),
                card=getattr(quoted, "user_card", None),
                text=quoted.content,
                image_count=durable_image_count,
                missing_images=durable_missing_images,
                attachments=file_refs,
                missing_files=missing_files,
            ),
            images,
        )

    milky_message = await _fetch_reply_message_from_milky(bot, event, reply_seq)
    if not milky_message:
        return None, []

    normalized = await normalize_segments(bot, milky_message.segments)
    quoted_text = normalized.content
    if load_images:
        _image_text, images, missing_images = await _extract_milky_message_content(bot, milky_message)
    else:
        images, missing_images = [], 0
    sender_user_id = int(milky_message.sender_id)
    role = "assistant" if str(sender_user_id) == str(event.self_id) else "user"
    if group_id is None and role == "assistant":
        display_name, nickname, card = EnvConfig.BOT_NAME, None, None
    else:
        display_name, nickname, card = sender_names_from_milky_message(milky_message)
    quoted_time = milky_message.time * 1000 if milky_message.time < 10_000_000_000 else milky_message.time
    scope_user_id = private_peer_user_id if private_peer_user_id is not None else sender_user_id
    quoted_record_persisted = False
    try:
        await messages_db.insert(
            time=quoted_time,
            msg_id=milky_message.message_seq,
            user_id=scope_user_id,
            group_id=group_id,
            user_name=display_name,
            user_nickname=nickname,
            user_card=card,
            sender_user_id=sender_user_id,
            bot_user_id=int(event.self_id),
            directly_mentions_bot=segments_directly_mention_user(milky_message.segments, event.self_id),
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
                user_id=scope_user_id,
                group_id=group_id,
                role=role,
                derived_messages=normalized.derived_messages,
                normalized_version=NORMALIZED_VERSION,
            )
        quoted_record_persisted = True
    except Exception as e:
        logger.warning(f"⚠️ 写入引用消息记录失败 message_seq={reply_seq}: {type(e).__name__}: {e}")
    images_cached = quoted_record_persisted and await _cache_complete_reply_images(
        messages_db,
        msg_time=quoted_time,
        user_id=scope_user_id,
        group_id=group_id,
        images=images if load_images else [],
        missing_images=missing_images,
        reply_seq=reply_seq,
    )
    file_refs: list[dict[str, object]] = []
    missing_files = 0
    if load_images and quoted_record_persisted:
        quoted_source = SimpleNamespace(
            time=quoted_time,
            msg_id=milky_message.message_seq,
            user_id=scope_user_id,
            group_id=group_id,
            content=quoted_text,
            raw_segments_json=normalized.raw_segments_json,
        )
        file_refs, missing_files = await _quoted_file_context(
            bot,
            event,
            reply_seq,
            messages_db,
            quoted_source,
            segments=list(milky_message.segments),
            workspace_key=workspace_key,
            memory_dir=memory_dir,
        )
    return (
        _format_quote(
            message_id=milky_message.message_seq,
            role=role,
            user_id=sender_user_id,
            display_name=display_name,
            nickname=nickname,
            card=card,
            text=quoted_text,
            image_count=len(images) if images_cached else 0,
            missing_images=missing_images,
            attachments=file_refs,
            missing_files=missing_files,
        ),
        images,
    )
