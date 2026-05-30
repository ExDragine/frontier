from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MISSING_GROUP_ID = "缺少群号：请在群聊中使用，或显式传入 group_id。"
MISSING_USER_ID = "缺少用户号：请显式传入 user_id，或在用户上下文中使用。"
SCENES = {"friend", "group", "temp"}


def is_local(source: str, root_dir: str | None = None) -> bool:
    """Check if *source* points to an existing file.

    When *root_dir* is given, *source* is resolved strictly inside that
    directory — path-traversal attempts (``..``, symlinks that escape, etc.)
    are rejected.  Absolute paths without *root_dir* are also rejected for
    safety, since they would otherwise allow unrestricted filesystem access.
    """
    if root_dir:
        root = Path(root_dir).resolve()
        normalized = source.lstrip("/")
        candidate = (root / normalized).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return False
        return candidate.is_file()

    path = Path(source)
    if path.is_absolute():
        return False
    return path.resolve().is_file()


def resolve_local_path(source: str, root_dir: str | None = None) -> Path | None:
    """Resolve *source* to an existing :class:`Path`.

    When *root_dir* is given, *source* MUST stay inside that sandbox —
    otherwise ``None`` is returned.  Absolute paths without *root_dir* are
    rejected for the same reason.
    """
    if root_dir:
        root = Path(root_dir).resolve()
        normalized = source.lstrip("/")
        candidate = (root / normalized).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        if candidate.is_file():
            return candidate
        return None

    path = Path(source)
    if path.is_absolute():
        return None
    resolved = path.resolve()
    if resolved.is_file():
        return resolved
    return None


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"无效的 URL：{url!r}，仅支持 http/https")


def resolve_group_id(group_id: int | str | None = None, config: dict | None = None) -> tuple[int | None, str | None]:
    raw_group_id: int | str | None = group_id
    if raw_group_id is None:
        raw_group_id = ((config or {}).get("configurable") or {}).get("group_id")
    if raw_group_id in (None, ""):
        return None, MISSING_GROUP_ID
    try:
        return int(raw_group_id), None
    except TypeError, ValueError:
        return None, f"群号格式错误：{raw_group_id!r}"


def resolve_user_id(user_id: int | str | None = None, config: dict | None = None) -> tuple[int | None, str | None]:
    raw_user_id: int | str | None = user_id
    if raw_user_id is None:
        raw_user_id = ((config or {}).get("configurable") or {}).get("user_id")
    if raw_user_id in (None, ""):
        return None, MISSING_USER_ID
    try:
        return int(raw_user_id), None
    except TypeError, ValueError:
        return None, f"用户号格式错误：{raw_user_id!r}"


def resolve_peer(
    message_scene: str,
    peer_id: int | str | None = None,
    config: dict | None = None,
) -> tuple[int | None, str | None]:
    if message_scene not in SCENES:
        return None, "message_scene 仅支持 friend、group 或 temp。"
    if peer_id is not None:
        try:
            return int(peer_id), None
        except TypeError, ValueError:
            return None, f"会话 ID 格式错误：{peer_id!r}"
    if message_scene == "group":
        return resolve_group_id(config=config)
    return resolve_user_id(config=config)


def binary_kwargs_from_uri(uri: str | None, root_dir: str | None = None) -> dict[str, str]:
    raw = (uri or "").strip()
    if not raw:
        return {}

    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        validate_url(raw)
        return {"url": raw}
    if parsed.scheme == "file":
        path = parsed.path
        if parsed.netloc and not path:
            path = parsed.netloc
        if not path:
            raise ValueError(f"无效的文件 URI：{uri!r}")
        return {"path": path}
    if parsed.scheme == "base64":
        encoded = raw[len("base64://") :]
        if not encoded:
            raise ValueError(f"无效的文件 URI：{uri!r}")
        return {"base64": encoded}
    if resolved := resolve_local_path(raw, root_dir):
        return {"path": str(resolved)}

    raise ValueError(f"无效的文件 URI：{uri!r}，仅支持 file://、http(s)://、base64:// 或本地文件路径")


def dump_model(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "dict_"):
        return item.dict_()
    if hasattr(item, "model_dump"):
        return item.model_dump(exclude_none=True)
    if hasattr(item, "dict"):
        return item.dict(exclude_none=True)
    if hasattr(item, "__dict__"):
        return {key: value for key, value in vars(item).items() if not key.startswith("_")}
    return {"value": item}


def truncate_text(text: Any, limit: int = 80) -> str:
    value = str(text).replace("\n", " ").strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 1]}..."


def format_key_values(data: Any, fields: list[str] | tuple[str, ...] | None = None) -> str:
    item = dump_model(data)
    ordered_fields = fields or tuple(item)
    return " ".join(f"{field}={truncate_text(item[field])}" for field in ordered_fields if item.get(field) is not None)


def format_records(title: str, records: list[Any], fields: list[str] | tuple[str, ...]) -> str:
    if not records:
        return f"{title}：无"
    lines = [f"{title}（{len(records)} 条）："]
    lines.extend("- " + format_key_values(record, fields) for record in records)
    return "\n".join(lines)


def segments_to_text(segments: list[dict] | None) -> str:
    if not segments:
        return ""
    parts: list[str] = []
    for segment in segments:
        segment_type = segment.get("type", "")
        data = segment.get("data") if isinstance(segment.get("data"), dict) else segment
        if segment_type == "text":
            parts.append(str(data.get("text", "")))
        else:
            parts.append(f"[{segment_type}]")
    return truncate_text("".join(parts), 120)


def format_message(message: Any) -> str:
    data = dump_model(message)
    text = segments_to_text(data.get("segments"))
    parts = [
        f"message_scene={data.get('message_scene', '')}",
        f"peer_id={data.get('peer_id', '')}",
        f"message_seq={data.get('message_seq', '')}",
        f"sender_id={data.get('sender_id', '')}",
        f"time={data.get('time', '')}",
        f"text={text}",
    ]
    return " ".join(parts)


def format_messages(title: str, messages: list[Any], next_message_seq: int | None = None) -> str:
    suffix = f"，next_message_seq={next_message_seq}" if next_message_seq is not None else ""
    if not messages:
        return f"{title}：无{suffix}"
    lines = [f"{title}（{len(messages)} 条{suffix}）："]
    lines.extend("- " + format_message(message) for message in messages)
    return "\n".join(lines)


def format_forwarded_messages(messages: list[Any]) -> str:
    if not messages:
        return "合并转发消息：无"
    lines = [f"合并转发消息（{len(messages)} 条）："]
    for message in messages:
        data = dump_model(message)
        lines.append(
            "- "
            f"message_seq={data.get('message_seq', '')} "
            f"sender_name={data.get('sender_name', '')} "
            f"time={data.get('time', '')} "
            f"text={segments_to_text(data.get('segments'))}"
        )
    return "\n".join(lines)


def format_files_info(group_id: int, info: Any) -> str:
    data = dump_model(info)
    files = data.get("files") or []
    folders = data.get("folders") or []
    lines = [f"群 {group_id} 文件（文件 {len(files)} 个，文件夹 {len(folders)} 个）："]
    for folder in folders:
        lines.append("- folder " + format_key_values(folder, ("folder_id", "folder_name", "file_count")))
    for file in files:
        lines.append(
            "- file "
            + format_key_values(file, ("file_id", "file_name", "file_size", "parent_folder_id", "uploader_id"))
        )
    return "\n".join(lines)
