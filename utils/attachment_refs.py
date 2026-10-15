"""Stable, download-free descriptions of attachments in original QQ segments."""

import json
from typing import Any


def message_segments(raw: str | None) -> list:
    try:
        value = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    return value if isinstance(value, list) else []


def attachment_refs(segments: list) -> list[dict[str, Any]]:
    """Use original zero-based segment positions, never successful-download order."""
    refs = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or segment.get("type") not in {"image", "file"}:
            continue
        data = segment.get("data") or {}
        if not isinstance(data, dict):
            continue
        ref = {"segment_index": index, "kind": segment["type"]}
        if name := data.get("file_name"):
            ref["file_name"] = str(name)[:200]
        if isinstance(data.get("file_size"), int) and data["file_size"] >= 0:
            ref["file_size"] = data["file_size"]
        refs.append(ref)
    return refs


def format_attachment_refs(segments: list) -> str:
    refs = attachment_refs(segments)
    if not refs:
        return ""
    # Keep identifiers separate from truncated message text and never expose
    # temporary URLs or platform download credentials to the model.
    return " attachments=" + json.dumps(refs, ensure_ascii=False, separators=(",", ":"))


def attachment_metadata(record) -> dict:
    try:
        value = json.loads(record.metadata_json)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def preferred_attachment_records(records: list) -> list:
    """One model-facing record per original segment; retain old rows for TTL cleanup.

    Call only after selecting one message's records. New indexed versions can
    replace expired caches or an unsupported-format legacy image.
    """
    latest = {}
    superseded = set()
    for record in sorted(records, key=lambda item: item.id or 0):
        metadata = attachment_metadata(record)
        if isinstance(index := metadata.get("segment_index"), int):
            key = record.kind, index
            if key in latest:
                superseded.add(latest[key])
            latest[key] = record.id
        if isinstance(old_id := metadata.get("supersedes_attachment_id"), int):
            superseded.add(old_id)
    return [record for record in records if record.id not in superseded]
