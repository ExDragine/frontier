import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from nonebot import logger

STAGED_ARTIFACTS_DIR = Path("cache") / "staged_artifacts"

_ARTIFACT_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _root_dir() -> Path:
    return Path(STAGED_ARTIFACTS_DIR)


def _validate_artifact_id(artifact_id: str) -> str:
    normalized = str(artifact_id).strip().lower()
    if not _ARTIFACT_ID_RE.fullmatch(normalized):
        raise ValueError(f"无效的暂存内容 ID: {artifact_id!r}")
    return normalized


def _write_bytes(value: bytes, artifact_dir: Path, blob_counter: list[int]) -> dict[str, str]:
    blob_counter[0] += 1
    filename = f"blob-{blob_counter[0]}.bin"
    (artifact_dir / filename).write_bytes(value)
    return {"__bytes_file__": filename}


def _serialize_value(value: Any, artifact_dir: Path, blob_counter: list[int]) -> Any:
    if isinstance(value, bytes):
        return _write_bytes(value, artifact_dir, blob_counter)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _serialize_value(item, artifact_dir, blob_counter) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item, artifact_dir, blob_counter) for item in value]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if _looks_like_segment(value):
        return _serialize_segment(value, artifact_dir, blob_counter)
    return str(value)


def _looks_like_segment(value: Any) -> bool:
    if isinstance(value, dict):
        return "type" in value
    return any(hasattr(value, attr) for attr in ("type", "data", "url", "raw", "text"))


def _segment_type(segment: Any) -> str | None:
    if isinstance(segment, dict):
        segment_type = segment.get("type")
        return str(segment_type) if segment_type is not None else None
    segment_type = getattr(segment, "type", None)
    if segment_type is not None:
        return str(segment_type)
    name = segment.__class__.__name__.lower()
    if name in {"image", "text"}:
        return name
    return None


def _segment_data(segment: Any) -> dict[str, Any]:
    if isinstance(segment, dict):
        return dict(segment)
    data = getattr(segment, "data", None)
    if isinstance(data, dict):
        return dict(data)

    result: dict[str, Any] = {}
    for attr in ("url", "path", "raw", "name", "id", "user_id", "text", "online"):
        if hasattr(segment, attr):
            result[attr] = getattr(segment, attr)
    return result


def _serialize_segment(segment: Any, artifact_dir: Path, blob_counter: list[int]) -> dict[str, Any]:
    segment_type = _segment_type(segment)
    data = _segment_data(segment)
    if segment_type is not None:
        data.setdefault("type", segment_type)
    if "type" not in data:
        data = {"type": "text", "text": str(segment)}
    return {str(key): _serialize_value(value, artifact_dir, blob_counter) for key, value in data.items()}


def _artifact_segments(artifact: Any) -> list[Any]:
    content = getattr(artifact, "content", artifact)
    if isinstance(content, (list, tuple)):
        return list(content)
    return [content]


def stage_artifact(artifact: Any) -> str:
    artifact_id = str(uuid.uuid4())
    artifact_dir = _root_dir() / artifact_id
    artifact_dir.mkdir(parents=True, exist_ok=False)
    try:
        blob_counter = [0]
        manifest = {
            "version": 1,
            "segments": [
                _serialize_segment(segment, artifact_dir, blob_counter) for segment in _artifact_segments(artifact)
            ],
        }
        manifest_path = artifact_dir / "manifest.json"
        tmp_path = artifact_dir / "manifest.json.tmp"
        tmp_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, manifest_path)
    except Exception:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise
    return artifact_id


def stage_artifact_response(text: str, artifact: Any | None) -> tuple[str, Any | None]:
    if artifact is None:
        return text, artifact
    try:
        artifact_id = stage_artifact(artifact)
    except Exception as exc:
        logger.warning(f"暂存工具 artifact 失败，继续返回原始 artifact: {type(exc).__name__}: {exc}")
        return text, artifact
    staged_notice = (
        f'<staged_artifact artifact_id="{artifact_id}" send_tool="send_staged_artifact" />\n'
        f'主 Agent：请调用 send_staged_artifact(artifact_id="{artifact_id}") 发送这份内容，'
        "不要把 staged_artifact 标签原样发给用户。"
    )
    return f"{text}\n\n{staged_notice}", artifact


def _read_bytes(payload: dict[str, str], artifact_dir: Path) -> bytes:
    filename = payload["__bytes_file__"]
    if "/" in filename or "\\" in filename:
        raise ValueError(f"无效的暂存二进制文件名: {filename!r}")
    return (artifact_dir / filename).read_bytes()


def _deserialize_value(value: Any, artifact_dir: Path) -> Any:
    if isinstance(value, dict) and "__bytes_file__" in value:
        return _read_bytes(value, artifact_dir)
    if isinstance(value, dict):
        return {key: _deserialize_value(item, artifact_dir) for key, item in value.items()}
    if isinstance(value, list):
        return [_deserialize_value(item, artifact_dir) for item in value]
    return value


def _path_or_none(path: str | None) -> Path | None:
    return Path(path) if path else None


def _build_message_segment(segment: dict[str, Any], uni_message_cls):
    segment_type = segment.get("type")
    match segment_type:
        case "image":
            return uni_message_cls.image(
                url=segment.get("url"),
                path=_path_or_none(segment.get("path")),
                raw=segment.get("raw"),
            )
        case "audio":
            return uni_message_cls.audio(
                url=segment.get("url"),
                path=_path_or_none(segment.get("path")),
                raw=segment.get("raw"),
            )
        case "voice":
            return uni_message_cls.voice(
                url=segment.get("url"),
                path=_path_or_none(segment.get("path")),
                raw=segment.get("raw"),
            )
        case "video":
            return uni_message_cls.video(
                url=segment.get("url"),
                path=_path_or_none(segment.get("path")),
                raw=segment.get("raw"),
            )
        case "file":
            return uni_message_cls.file(
                url=segment.get("url"),
                path=_path_or_none(segment.get("path")),
                name=segment.get("name") or "file.bin",
            )
        case "emoji":
            return uni_message_cls.emoji(id=segment.get("id"))
        case "at":
            return uni_message_cls.at(str(segment.get("user_id") or ""))
        case "at_all":
            return uni_message_cls.at_all(online=bool(segment.get("online", False)))
        case "text":
            return uni_message_cls.text(str(segment.get("text") or ""))
        case _:
            return uni_message_cls(segment)


def _combine_segments(messages: list[Any], uni_message_cls):
    if not messages:
        return uni_message_cls()
    combined = messages[0]
    for message in messages[1:]:
        if hasattr(combined, "extend"):
            result = combined.extend(message)
            if result is not None:
                combined = result
        else:
            combined = combined + message
    return combined


def load_staged_artifact(artifact_id: str, *, uni_message_cls):
    artifact_id = _validate_artifact_id(artifact_id)
    artifact_dir = _root_dir() / artifact_id
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"暂存内容不存在: {artifact_id}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    segments = manifest.get("segments")
    if manifest.get("version") != 1 or not isinstance(segments, list):
        raise ValueError(f"暂存内容格式无效: {artifact_id}")

    messages = [
        _build_message_segment(_deserialize_value(segment, artifact_dir), uni_message_cls)
        for segment in segments
        if isinstance(segment, dict)
    ]
    return _combine_segments(messages, uni_message_cls)
