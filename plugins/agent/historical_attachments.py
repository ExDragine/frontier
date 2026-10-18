"""Resolve original message segments into scoped, TTL-managed readable files."""

import asyncio
import json
import re
import time
from pathlib import Path

from nonebot import logger

from utils.attachment_refs import attachment_metadata, attachment_refs, message_segments
from utils.configs import EnvConfig
from utils.database import MessageDatabase, resolve_message_sender_user_id
from utils.media import normalize_image_for_model

from . import attachments, reply_context
from .reply_context import MessageSource

_MAX_ATTACHMENTS_PER_READ = 4


def _cached_record(ref: dict, refs: list[dict], records: list, segments: list):
    """Old compacted caches are reusable only when their mapping is unambiguous."""
    for record in reversed(records):
        if record.kind == ref["kind"] and attachment_metadata(record).get("segment_index") == ref["segment_index"]:
            return record
    legacy = [record for record in records if record.kind == ref["kind"] and "segment_index" not in attachment_metadata(record)]
    same_kind = [item for item in refs if item["kind"] == ref["kind"]]
    if ref["kind"] == "file":
        name = Path(str(ref.get("file_name", "")).replace("\\", "/")).name
        matches = [record for record in legacy if record.file_name == name]
        names = [Path(str(item.get("file_name", "")).replace("\\", "/")).name for item in same_kind]
        if len(matches) == 1 and names.count(name) == 1:
            return matches[0]
    elif len(legacy) == len(same_kind) and not any(
        isinstance(segment, dict) and segment.get("type") == "forward" for segment in segments
    ):
        ordinals = [re.search(r"_(\d+)\.[^.]+$", record.file_name) for record in legacy]
        if all(ordinals) and len({match[1] for match in ordinals}) == len(legacy):
            ordered = sorted(zip(legacy, ordinals, strict=True), key=lambda pair: int(pair[1][1]))
            return ordered[same_kind.index(ref)][0]
    return None


def _readable(record, *, workspace_key: str, memory_dir: Path) -> bool:
    if record.workspace_key != workspace_key or record.expires_at < int(time.time() * 1000):
        return False
    prefix = f"/memory/{workspace_key}/"
    if not record.virtual_path.startswith(prefix):
        return False
    expected = (memory_dir / record.virtual_path[len(prefix):]).resolve()
    actual = Path(record.physical_path).resolve()
    return expected.is_relative_to(memory_dir.resolve()) and expected == actual and actual.is_file()


async def _download(bot, source: MessageSource, message, ref: dict, segment: dict, *, workspace_key, memory_dir, cached=None):
    options = {
        "memory_dir": memory_dir, "workspace_key": workspace_key,
        "message_time": message.time, "message_id": message.id,
    }
    if ref["kind"] == "image":
        data = (
            await asyncio.to_thread(Path(cached.physical_path).read_bytes)
            if cached is not None else await reply_context._download_milky_image(bot, segment)
        )
        if not data:
            return None
        media = await asyncio.to_thread(normalize_image_for_model, data)
        if media is None:
            return None
        return await attachments.stage_message_bytes(
            media.data, f"image-{ref['segment_index']}{media.extension}", **options,
        )
    items = [reply_context._refreshable_quoted_file_item(item, source.group_id)
             for item in attachments.extract_message_files([segment])]
    files = await attachments.stage_message_files(
        bot, items, **options, user_id=source.peer_id, group_id=source.group_id,
        is_self_send=str(resolve_message_sender_user_id(message)) == source.bot_user_id,
    )
    return files[0] if files else None


async def _prepare_one(bot, source, message, ref, segments, records, refs, db, *, workspace_key, memory_dir):
    cached = _cached_record(ref, refs, records, segments)
    if cached is not None and not _readable(cached, workspace_key=workspace_key, memory_dir=memory_dir):
        cached = None
    needs_conversion = cached is not None and ref["kind"] == "image" and Path(cached.file_name).suffix.lower() not in {
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
    }
    if cached is not None and not needs_conversion:
        return {**ref, "status": "ready", "path": cached.virtual_path, "mime_type": cached.mime_type}
    staged = await _download(
        bot, source, message, ref, segments[ref["segment_index"]],
        workspace_key=workspace_key, memory_dir=memory_dir, cached=cached,
    )
    if staged is None:
        return {**ref, "status": "unavailable", "reason": "附件已失效或下载失败，可请用户重发。"}
    metadata = {"segment_index": ref["segment_index"]}
    if cached is not None:
        metadata["supersedes_attachment_id"] = cached.id
    try:
        await db.insert_attachment(
            msg_time=message.time, message_id=message.id, msg_id=message.msg_id,
            user_id=message.user_id, group_id=message.group_id, kind=ref["kind"],
            physical_path=str(staged.local_path), virtual_path=staged.virtual_path,
            file_name=staged.file_name, mime_type=staged.mime_type,
            file_size=staged.file_size, sha256=staged.sha256,
            expires_at=int(time.time() * 1000) + EnvConfig.MEDIA_TTL_DAYS * 86400 * 1000,
            metadata_json=json.dumps(metadata),
        )
    except BaseException:
        attachments.cleanup_staged_message_files([staged])
        raise
    return {**ref, "status": "ready", "path": staged.virtual_path, "mime_type": staged.mime_type}


async def load_historical_attachments(
    bot,
    source: MessageSource,
    message_seq: int,
    db: MessageDatabase,
    *,
    workspace_key: str,
    memory_dir: str | Path,
    attachment_index: int | None = None,
) -> dict:
    """Stage selected files; paths are references, not evidence of model perception."""
    lookup = {"msg_id": message_seq, "group_id": source.group_id}
    if source.group_id is None:
        lookup["peer_user_id"] = source.peer_id
    message = await db.select_by_msg_id(**lookup)
    if message is not None and getattr(message, "bot_user_id", None) not in (None, int(source.bot_user_id)):
        return {"error": "该消息不属于当前机器人账号。"}
    if message is None or not message.raw_segments_json:
        await reply_context.load_message_context(bot, source, message_seq, db, load_images=False, refresh_segments=True)
        message = await db.select_by_msg_id(**lookup)
    if message is None:
        return {"error": "找不到该消息，平台历史可能已失效。"}
    segments = message_segments(message.raw_segments_json)
    refs = attachment_refs(segments)
    if attachment_index is not None and not any(ref["segment_index"] == attachment_index for ref in refs):
        return {"error": "attachment_index 不是该消息的图片或文件编号。", "attachment_refs": refs}
    selected = (
        [ref for ref in refs if ref["segment_index"] == attachment_index]
        if attachment_index is not None else refs[:_MAX_ATTACHMENTS_PER_READ]
    )
    records = await db.select_attachments_by_msg_time(message.time, message_id=message.id)
    results = []
    for ref in selected:
        try:
            result = await _prepare_one(
                bot, source, message, ref, segments, records, refs, db,
                workspace_key=workspace_key, memory_dir=Path(memory_dir),
            )
        except Exception as exc:
            logger.warning("历史附件读取失败 message_seq={} segment_index={}: {}", message_seq, ref["segment_index"], type(exc).__name__)
            result = {**ref, "status": "unavailable", "reason": "附件读取失败，可请用户重发。"}
        results.append(result)
    return {
        "message_scene": source.message_scene, "peer_id": source.peer_id,
        "message_seq": message_seq, "sender_user_id": resolve_message_sender_user_id(message),
        "content": message.content, "attachment_refs": refs, "attachments": results,
        "instruction": "ready 只表示文件已保存；使用 read_file 读取 path 后再判断内容。未加载项可指定 attachment_index 继续读取。",
    }
