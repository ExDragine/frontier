import functools
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlparse

MISSING_GROUP_ID = "缺少群号：请在群聊中使用，或显式传入 group_id。"
MISSING_USER_ID = "缺少用户号：请显式传入 user_id，或在用户上下文中使用。"
SCENES = {"friend", "group", "temp"}


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


def resolve_virtual_path(source: str, virtual_roots: dict[str, str]) -> Path | None:
    """Resolve an agent virtual path against its explicitly mounted roots.

    Routes use the same virtual prefixes as ``CompositeBackend``. The longest
    matching route wins, and reserved mounts cannot fall through to the default
    workspace route.
    """
    raw = source.strip()
    if not raw:
        return None
    virtual_path = raw if raw.startswith("/") else f"/{raw}"

    normalized_routes: list[tuple[str, Path]] = []
    for prefix, root_dir in virtual_roots.items():
        normalized_prefix = f"/{prefix.strip('/')}" if prefix != "/" else "/"
        if normalized_prefix != "/":
            normalized_prefix += "/"
        normalized_routes.append((normalized_prefix, Path(root_dir).resolve()))

    for prefix, root in sorted(normalized_routes, key=lambda item: len(item[0]), reverse=True):
        if prefix == "/":
            if virtual_path.startswith(("/memory/", "/skills/")):
                continue
            relative = virtual_path.lstrip("/")
        elif virtual_path.startswith(prefix):
            relative = virtual_path[len(prefix) :]
        else:
            continue

        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        return candidate if candidate.is_file() else None
    return None


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"无效的 URL：{url!r}，仅支持 http/https")


def configurable(config: dict | None) -> dict:
    """取出 RunnableConfig 中的 ``configurable`` 段。

    缺失或显式为 ``None`` 时返回空字典，调用方可以直接 ``.get(...)``。
    """
    return (config or {}).get("configurable") or {}


def _coerce_id(raw: Any, *, label: str) -> tuple[int | None, str | None]:
    """把 *raw* 归一化为整数 ID。

    失败时返回 ``(None, f"{label}：{raw!r}")``；错误文案由 :func:`resolve_group_id`
    等直接透出，因此各调用点的文案完全一致。
    """
    try:
        return int(raw), None
    except TypeError, ValueError:
        return None, f"{label}：{raw!r}"


def resolve_group_id(group_id: int | str | None = None, config: dict | None = None) -> tuple[int | None, str | None]:
    raw_group_id: int | str | None = group_id
    if raw_group_id is None:
        raw_group_id = configurable(config).get("group_id")
    if raw_group_id in (None, ""):
        return None, MISSING_GROUP_ID
    return _coerce_id(raw_group_id, label="群号格式错误")


def resolve_user_id(user_id: int | str | None = None, config: dict | None = None) -> tuple[int | None, str | None]:
    raw_user_id: int | str | None = user_id
    if raw_user_id is None:
        raw_user_id = configurable(config).get("user_id")
    if raw_user_id in (None, ""):
        return None, MISSING_USER_ID
    return _coerce_id(raw_user_id, label="用户号格式错误")


def resolve_peer(
    message_scene: str,
    peer_id: int | str | None = None,
    config: dict | None = None,
) -> tuple[int | None, str | None]:
    if message_scene not in SCENES:
        return None, "message_scene 仅支持 friend、group 或 temp。"
    if peer_id is not None:
        return _coerce_id(peer_id, label="会话 ID 格式错误")
    if message_scene == "group":
        return resolve_group_id(config=config)
    return resolve_user_id(config=config)


class ToolInputError(Exception):
    """工具入参或权限校验失败；文案可直接作为工具返回值给模型。"""


def require_group_id(group_id: int | str | None = None, config: dict | None = None) -> int:
    """解析群号，失败时抛出 :class:`ToolInputError`。

    :func:`resolve_group_id` 在所有失败路径上都会给出 ``error``，因此原先
    ``if error or resolved_group_id is None`` 的兜底文案不可达，这里只判 ``error``。
    """
    resolved_group_id, error = resolve_group_id(group_id, config)
    if error:
        raise ToolInputError(error)
    return cast("int", resolved_group_id)


def require_user_id(user_id: int | str | None = None, config: dict | None = None) -> int:
    """解析用户号，失败时抛出 :class:`ToolInputError`。"""
    resolved_user_id, error = resolve_user_id(user_id, config)
    if error:
        raise ToolInputError(error)
    return cast("int", resolved_user_id)


def require_peer(message_scene: str, peer_id: int | str | None = None, config: dict | None = None) -> int:
    """解析会话 ID，失败时抛出 :class:`ToolInputError`。"""
    resolved_peer_id, error = resolve_peer(message_scene, peer_id, config)
    if error:
        raise ToolInputError(error)
    return cast("int", resolved_peer_id)


def input_error_text(func):
    """把 :class:`ToolInputError` 变成工具的错误文案返回值。

    与各工具原先 ``resolved, error = resolve_*(...); if error: return error``
    的返回值逐字一致；content 与 content_and_artifact 工具原先都直接返回该字符串。
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ToolInputError as exc:
            return str(exc)

    return wrapper


def binary_kwargs_from_uri(uri: str | None, root_dir: str | None = None) -> dict[str, str]:  # noqa: C901
    raw = (uri or "").strip()
    if not raw:
        return {}

    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        validate_url(raw)
        return {"url": raw}
    if parsed.scheme == "file":
        path = unquote(parsed.path)
        if parsed.netloc and not path:
            path = unquote(parsed.netloc)
        if not path:
            raise ValueError(f"无效的文件 URI：{uri!r}")
        if root_dir is None:
            return {"path": path}
        root = Path(root_dir).resolve()
        candidate = (root / path.lstrip("/")).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            raise ValueError(f"无效的文件 URI：{uri!r}，文件路径不在允许的工作区内") from None
        return {"path": str(candidate)}
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
        segment_data = segment.get("data")
        data = segment_data if isinstance(segment_data, dict) else segment
        if segment_type == "text":
            parts.append(str(data.get("text", "")))
        elif segment_type == "markdown":
            parts.append(str(data.get("content", "")))
        else:
            parts.append(f"[不支持的消息段:{segment_type or 'unknown'}]")
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
    lines.extend(
        "- folder " + format_key_values(folder, ("folder_id", "folder_name", "file_count"))
        for folder in folders
    )
    lines.extend(
        (
            "- file "
            + format_key_values(
                file_info,
                ("file_id", "file_name", "file_size", "parent_folder_id", "uploader_id"),
            )
        )
        for file_info in files
    )
    return "\n".join(lines)
