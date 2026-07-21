import datetime
import zoneinfo
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot, logger

from utils.database import Message, MessageDatabase
from utils.milky_tools import format_messages

_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")
# 以约 200K tokens 的有效上下文预算规划：典型 QQ 短消息最多读取 1,000 条，
# 每页 200 条；超长消息仍由 content_max_chars 单独截断。
_MAX_PAGE_SIZE = 200
_MAX_OFFSET = 5000
_MAX_MEMORY_MESSAGES = 1000
_MIN_CONTENT_CHARS = 100
_MAX_CONTENT_CHARS = 4000

message_db = MessageDatabase()


def _parse_datetime_to_ms(value: str, *, end_of_day: bool = False) -> int:
    """Parse a local date/time or ISO 8601 timestamp into Unix milliseconds."""
    raw = value.strip()
    if not raw:
        raise ValueError("时间不能为空")

    date_only = False
    try:
        parsed_date = datetime.date.fromisoformat(raw)
        date_only = parsed_date.isoformat() == raw
    except ValueError:
        pass

    try:
        parsed = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"无法解析时间「{raw}」，请使用 YYYY-MM-DD、YYYY-MM-DD HH:MM 或 ISO 8601 格式"
        ) from exc

    if date_only and end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999000)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_SHANGHAI)
    else:
        parsed = parsed.astimezone(_SHANGHAI)
    return int(parsed.timestamp() * 1000)


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _current_scope(config: RunnableConfig | None) -> tuple[int | None, int | None, str | None]:
    cfg = (config or {}).get("configurable", {})
    raw_user_id = cfg.get("user_id")
    raw_group_id = cfg.get("group_id")
    try:
        user_id = int(raw_user_id) if raw_user_id not in (None, "") else None
        group_id = int(raw_group_id) if raw_group_id not in (None, "") else None
    except TypeError, ValueError:
        return None, None, "用户上下文错误，无法读取聊天记忆。"
    if group_id is None and user_id is None:
        return None, None, "缺少当前会话上下文，无法读取聊天记忆。"
    return user_id, group_id, None


def _truncate_content(content: str, limit: int) -> str:
    cleaned = " ".join(content.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1]}…"


def _format_search_results(
    messages: list[Message],
    *,
    sort: str,
    offset: int,
    limit: int,
    content_max_chars: int,
) -> str:
    sort_label = "相关度" if sort == "relevance" else "时间倒序"
    lines = [f"找到 {len(messages)} 条聊天记录（{sort_label}，offset={offset}）："]
    for msg in messages:
        timestamp = datetime.datetime.fromtimestamp(msg.time / 1000, tz=_SHANGHAI).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        scope = f"群{msg.group_id}" if msg.group_id is not None else "私聊"
        message_id = msg.msg_id if msg.msg_id is not None else "无"
        name = msg.user_name or ("助手" if msg.role == "assistant" else str(msg.user_id))
        role_label = "助手" if msg.role == "assistant" else "用户"
        lines.append(
            f"- [{timestamp}] {scope} msg_id={message_id} user_id={msg.user_id} "
            f"{role_label}({name}): {_truncate_content(msg.content, content_max_chars)}"
        )
    if len(messages) == limit and offset + len(messages) < _MAX_MEMORY_MESSAGES:
        lines.append(f"可能还有更多记录；下一页使用 offset={offset + len(messages)}。")
    if offset + len(messages) >= _MAX_MEMORY_MESSAGES:
        lines.append(f"⚠️ 已达到单次记忆任务最多 {_MAX_MEMORY_MESSAGES} 条记录的读取上限。")
    return "\n".join(lines)


@tool(response_format="content")
async def search_messages(  # noqa: C901
    config: RunnableConfig,
    query: str | None = None,
    target_user_id: int | None = None,
    target_user_name: str | None = None,
    message_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    role: Literal["user", "assistant"] | None = None,
    sort: Literal["auto", "time", "relevance"] = "auto",
    limit: int = 50,
    offset: int = 0,
    content_max_chars: int = 800,
) -> str:
    """搜索当前群聊或私聊的本地聊天记忆。

    所有筛选条件都可选；不传条件时返回当前会话最近的消息。关键词查询默认按
    FTS5 相关度排序，其他查询默认按时间倒序。可通过 offset 分页，但单个记忆
    任务最多读取 1000 条记录。

    Args:
        query: 可选消息关键词，支持部分匹配。
        target_user_id: 可选群成员 QQ 号；私聊中只能是当前用户。
        target_user_name: 可选用户显示名称片段。
        message_id: 可选平台消息 ID。
        start_date: 可选起始时间，支持本地日期时间或 ISO 8601。
        end_date: 可选结束时间；仅日期时包含当天结束。
        role: 可选消息角色 user 或 assistant。
        sort: auto、time 或 relevance；relevance 必须提供 query。
        limit: 本页数量，范围 1–200。
        offset: 分页偏移，范围 0–5000；同一任务不要读取超过 1000 条。
        content_max_chars: 每条消息最多返回字符数，范围 100–4000。
    """
    content_query = _clean_optional_text(query)
    user_name_query = _clean_optional_text(target_user_name)
    if sort not in {"auto", "time", "relevance"}:
        return "排序方式错误：仅支持 auto、time 或 relevance。"
    if role not in {None, "user", "assistant"}:
        return "消息角色错误：仅支持 user 或 assistant。"
    if sort == "relevance" and not content_query:
        return "relevance 排序需要提供 query。"

    start_ms: int | None = None
    end_ms: int | None = None
    try:
        if start_date:
            start_ms = _parse_datetime_to_ms(start_date)
        if end_date:
            end_ms = _parse_datetime_to_ms(end_date, end_of_day=True)
    except ValueError as exc:
        return f"日期格式错误：{exc}"
    if start_ms is not None and end_ms is not None and end_ms <= start_ms:
        return "结束时间不能早于或等于开始时间。"

    current_user_id, group_id, context_error = _current_scope(config)
    if context_error:
        return context_error

    query_limit = max(1, min(limit, _MAX_PAGE_SIZE))
    query_offset = max(0, min(offset, _MAX_OFFSET))
    if query_offset >= _MAX_MEMORY_MESSAGES:
        return f"单次记忆任务最多读取 {_MAX_MEMORY_MESSAGES} 条记录，请缩小查询范围。"
    query_limit = min(query_limit, _MAX_MEMORY_MESSAGES - query_offset)
    max_chars = max(_MIN_CONTENT_CHARS, min(content_max_chars, _MAX_CONTENT_CHARS))
    resolved_sort = "relevance" if sort == "auto" and content_query else "time"

    try:
        messages = await message_db.search_messages(
            group_id=group_id,
            user_id=current_user_id,
            content_query=content_query,
            target_user_id=target_user_id,
            target_user_name=user_name_query,
            msg_id=message_id,
            start_time=start_ms,
            end_time=end_ms,
            role=role,
            limit=query_limit,
            offset=query_offset,
            sort=resolved_sort,
        )
    except Exception as exc:
        logger.error(f"消息搜索失败: {type(exc).__name__}: {exc}")
        return "消息搜索失败，请稍后重试。"
    if not messages:
        return "未找到匹配的聊天记录。"
    return _format_search_results(
        messages,
        sort=resolved_sort,
        offset=query_offset,
        limit=query_limit,
        content_max_chars=max_chars,
    )


@tool(response_format="content")
async def get_history_messages(
    config: RunnableConfig,
    start_message_seq: int | None = None,
    limit: int = 20,
) -> str:
    """从 QQ 平台读取当前群聊或私聊的最近消息，不能指定其他会话。

    Args:
        start_message_seq: 可选起始消息序列号，用于继续向前分页。
        limit: 获取数量，范围 1–30。
    """
    user_id, group_id, context_error = _current_scope(config)
    if context_error:
        return context_error
    message_scene = "group" if group_id is not None else "friend"
    peer_id = group_id if group_id is not None else user_id
    try:
        messages, next_message_seq = await get_bot().get_history_messages(
            message_scene=message_scene,
            peer_id=peer_id,
            start_message_seq=start_message_seq,
            limit=max(1, min(limit, 30)),
        )
    except Exception as exc:
        logger.error(f"平台历史消息获取失败: {type(exc).__name__}: {exc}")
        return "平台历史消息获取失败，请稍后重试。"
    return format_messages("当前会话历史消息", messages, next_message_seq)
