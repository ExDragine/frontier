import json
from dataclasses import dataclass
from typing import Any

from nonebot import logger

NORMALIZED_VERSION = 2
FORWARD_MAX_DEPTH = 3
FORWARD_MAX_NODES = 80


@dataclass(slots=True)
class DerivedMessage:
    sender_name: str
    content: str
    raw_segments_json: str
    forward_id: str | None
    time_ms: int | None = None


@dataclass(slots=True)
class NormalizedMessage:
    content: str
    raw_segments_json: str
    derived_messages: list[DerivedMessage]
    normalized_version: int = NORMALIZED_VERSION
    status: str = "complete"


def segments_to_raw_json(segments: list[dict]) -> str:
    return json.dumps(segments, ensure_ascii=False, default=str)


def _forward_marker(data: dict) -> str:
    title = data.get("title", "")
    summary = data.get("summary", "")
    if title or summary:
        return f"[合并转发:{title} - {summary}]"
    return "[合并转发]"


def _node_time_ms(node: Any) -> int | None:
    node_time = getattr(node, "time", None)
    if node_time is None:
        return None
    try:
        value = int(node_time)
    except (TypeError, ValueError):
        return None
    return value * 1000 if value < 10_000_000_000 else value


async def _normalize_forward_segment(bot, segment: dict, *, depth: int) -> tuple[str, list[DerivedMessage], str]:
    data = segment.get("data", {})
    marker = _forward_marker(data)
    forward_id = data.get("forward_id")
    if not forward_id:
        return marker, [], "complete"
    if depth >= FORWARD_MAX_DEPTH:
        return f"{marker}\n[合并转发展开已达到深度限制]", [], "partial"

    try:
        nodes = await bot.get_forwarded_messages(forward_id)
    except Exception as exc:
        logger.warning(f"拉取合并转发失败 forward_id={forward_id}: {type(exc).__name__}: {exc}")
        return f"{marker}\n[合并转发内容拉取失败]", [], "partial"

    lines = [marker]
    derived: list[DerivedMessage] = []
    status = "complete"
    for node in list(nodes)[:FORWARD_MAX_NODES]:
        node_segments = getattr(node, "segments", [])
        node_result = await _normalize_segments(bot, node_segments, depth=depth + 1)
        if node_result.status != "complete":
            status = "partial"
        sender_name = str(getattr(node, "sender_name", None) or "未知")
        content = node_result.content.strip() or "[空消息]"
        lines.append(f"{sender_name}: {content}")
        derived.append(
            DerivedMessage(
                sender_name=sender_name,
                content=content,
                raw_segments_json=node_result.raw_segments_json,
                forward_id=forward_id,
                time_ms=_node_time_ms(node),
            )
        )
        derived.extend(node_result.derived_messages)

    if len(nodes) > FORWARD_MAX_NODES:
        lines.append(f"[合并转发还有 {len(nodes) - FORWARD_MAX_NODES} 条，已省略]")
        status = "partial"
    return "\n".join(lines), derived, status


async def _normalize_plain_segment(segment: dict) -> str:
    segment_type = segment.get("type")
    data = segment.get("data", {})
    if segment_type == "image":
        summary = data.get("summary")
        return f"[图片:{summary}]" if summary else "[图片]"
    if segment_type == "record":
        duration = data.get("duration", 0)
        return f"[语音:{duration}秒]"
    if segment_type == "video":
        duration = data.get("duration", 0)
        return f"[视频:{duration}秒]"

    from utils.message import message_extract

    text, *_ = await message_extract([segment])
    return text


async def _normalize_segments(bot, segments: list[dict], *, depth: int = 0) -> NormalizedMessage:
    text_parts: list[str] = []
    derived_messages: list[DerivedMessage] = []
    status = "complete"

    for segment in segments:
        if segment.get("type") == "forward":
            forward_text, forward_derived, forward_status = await _normalize_forward_segment(bot, segment, depth=depth)
            text_parts.append(forward_text)
            derived_messages.extend(forward_derived)
            if forward_status != "complete":
                status = "partial"
            continue

        plain_text = await _normalize_plain_segment(segment)
        if plain_text:
            text_parts.append(plain_text)

    return NormalizedMessage(
        content="\n".join(part for part in text_parts if part),
        raw_segments_json=segments_to_raw_json(segments),
        derived_messages=derived_messages,
        status=status,
    )


async def normalize_segments(bot, segments: list[dict]) -> NormalizedMessage:
    return await _normalize_segments(bot, segments, depth=0)
