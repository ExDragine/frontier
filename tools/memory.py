import datetime
import zoneinfo

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from nonebot import logger

from utils.configs import EnvConfig
from utils.database import Message, MessageDatabase

_LARGE_MSG_THRESHOLD = 50
_MSG_LIMIT = 500
_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")

_SUMMARIZE_PROMPT = """你是一个聊天记录分析助手。请对以下聊天记录进行总结和分析。

要求:
1. 提取主要讨论话题，按话题分类整理
2. 总结每个话题的核心观点和结论
3. 标注重要的信息、决定或待办事项（如有）
4. 保持客观中立，不添加个人评价
5. 使用简洁的中文输出
6. 如果聊天内容涉及多个不相关话题，分别总结

输出格式:
## 话题概览
（列出主要话题）

## 详细总结
（按话题逐一总结）

## 重要信息
（关键决定、待办事项等，如无则省略此节）
"""

message_db = MessageDatabase()


def _parse_datetime_to_ms(date_str: str, end_of_day: bool = False) -> int:
    """将日期字符串解析为 Unix 毫秒时间戳（Asia/Shanghai 时区）。

    Args:
        date_str: 日期字符串，支持 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM" 格式
        end_of_day: 若为 True 且输入仅包含日期，则视为当天 23:59:59
    """
    date_str = date_str.strip()
    has_time = False
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            has_time = fmt == "%Y-%m-%d %H:%M"
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"无法解析日期「{date_str}」，请使用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM 格式")

    if end_of_day and not has_time:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)

    dt = dt.replace(tzinfo=_SHANGHAI)
    return int(dt.timestamp() * 1000)


def _build_statistics(messages: list, capped: bool) -> str:
    """生成消息统计摘要。"""
    total = len(messages)
    participants: dict[int, str] = {}
    for msg in messages:
        if msg.role == "user":
            participants[msg.user_id] = msg.user_name or str(msg.user_id)

    start_ts = datetime.datetime.fromtimestamp(messages[0].time / 1000, tz=_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S")
    end_ts = datetime.datetime.fromtimestamp(messages[-1].time / 1000, tz=_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S")

    duration_sec = (messages[-1].time - messages[0].time) / 1000
    if duration_sec < 3600:
        duration_str = f"{duration_sec / 60:.0f} 分钟"
    elif duration_sec < 86400:
        duration_str = f"{duration_sec / 3600:.1f} 小时"
    else:
        duration_str = f"{duration_sec / 86400:.1f} 天"

    names = "、".join(participants.values()) if participants else "无"
    lines = [
        "📊 **消息统计**",
        f"- 时间范围：{start_ts} ~ {end_ts}（跨度 {duration_str}）",
        f"- 消息总数：{total} 条",
        f"- 参与用户（{len(participants)} 人）：{names}",
    ]
    if capped:
        lines.append(f"- ⚠️ 该时间段消息较多，仅展示最早的 {_MSG_LIMIT} 条")
    return "\n".join(lines)


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _truncate_content(content: str, limit: int = 240) -> str:
    content = " ".join(content.split())
    if len(content) <= limit:
        return content
    return f"{content[: limit - 1]}…"


def _format_search_results(messages: list[Message]) -> str:
    lines = [f"找到 {len(messages)} 条聊天记录（按时间倒序）："]
    for msg in messages:
        ts = datetime.datetime.fromtimestamp(msg.time / 1000, tz=_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S")
        scope = f"群{msg.group_id}" if msg.group_id is not None else "私聊"
        msg_id = msg.msg_id if msg.msg_id is not None else "无"
        name = msg.user_name or ("助手" if msg.role == "assistant" else str(msg.user_id))
        role_label = "助手" if msg.role == "assistant" else "用户"
        lines.append(
            f"- [{ts}] {scope} msg_id={msg_id} user_id={msg.user_id} {role_label}({name}): "
            f"{_truncate_content(msg.content)}"
        )
    return "\n".join(lines)


@tool(response_format="content")
async def summarize_messages(
    start_date: str,
    end_date: str,
    config: RunnableConfig,
    target_user_id: int | None = None,
) -> str:
    """
    检索并总结指定时间段内的聊天记录。
    在群聊中总结本群消息，在私聊中总结与该用户的私聊消息。
    可选指定 target_user_id 来仅分析群内某位用户的发言。
    Args:
        start_date (str): 起始日期，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM"
        end_date (str): 结束日期，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM"（仅日期时视为当天结束）
        target_user_id (int): 可选，群聊中筛选特定用户ID的发言
    Returns:
        str: 消息统计信息与内容摘要
    """
    cfg = config.get("configurable", {})
    user_id: str = cfg.get("user_id", "")
    group_id: int | None = cfg.get("group_id")
    try:
        start_ms = _parse_datetime_to_ms(start_date, end_of_day=False)
        end_ms = _parse_datetime_to_ms(end_date, end_of_day=True)
    except ValueError as e:
        return f"日期格式错误：{e}"

    if end_ms <= start_ms:
        return "结束时间不能早于或等于开始时间。"

    query_user_id = int(user_id) if group_id is None else target_user_id
    query_group_id = group_id

    try:
        messages = await message_db.select_by_time_range(
            start_time=start_ms,
            end_time=end_ms,
            group_id=query_group_id,
            user_id=query_user_id,
            limit=_MSG_LIMIT,
        )
    except Exception as e:
        logger.error(f"消息查询失败: {e}")
        return "消息查询失败，请稍后重试。"

    if not messages:
        return "在指定时间段内未找到聊天记录。"

    capped = len(messages) == _MSG_LIMIT
    stats = _build_statistics(messages, capped)
    formatted = MessageDatabase.format_for_llm(messages)

    if len(messages) <= _LARGE_MSG_THRESHOLD:
        return f"{stats}\n\n---\n\n{formatted}"

    try:
        from utils.agents import assistant_agent  # 延迟导入避免循环依赖

        summary = await assistant_agent(
            system_prompt=_SUMMARIZE_PROMPT,
            user_prompt=formatted,
            use_model=EnvConfig.BASIC_MODEL,
        )
        return f"{stats}\n\n---\n\n{summary}"
    except Exception as e:
        logger.error(f"消息总结生成失败: {e}")
        truncated = MessageDatabase.format_for_llm(messages[:_LARGE_MSG_THRESHOLD])
        return f"{stats}\n\n---\n\n（自动总结失败，以下为前 {_LARGE_MSG_THRESHOLD} 条原始记录）\n\n{truncated}"


@tool(response_format="content")
async def search_messages(  # noqa: C901
    config: RunnableConfig,
    query: str | None = None,
    search_mode: str = "keyword",
    target_user_id: int | None = None,
    target_user_name: str | None = None,
    message_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
) -> str:
    """
    按内容关键词、用户名称、用户ID、消息ID或时间范围搜索历史聊天记录。
    在群聊中只搜索本群消息，在私聊中只搜索与当前用户的私聊消息。
    Args:
        query (str): 可选，消息内容关键词，支持部分匹配
        search_mode (str): 搜索模式，默认 keyword
        target_user_id (int): 可选，群聊中筛选特定用户ID
        target_user_name (str): 可选，按用户显示名称部分匹配
        message_id (int): 可选，按平台消息ID精确搜索
        start_date (str): 可选，起始日期，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM"
        end_date (str): 可选，结束日期，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM"
        limit (int): 返回数量上限，默认 50，最大 100
    Returns:
        str: 匹配的聊天记录列表
    """
    content_query = _clean_optional_text(query)
    if search_mode != "keyword":
        return "当前仅支持 keyword 搜索模式。"
    user_name_query = _clean_optional_text(target_user_name)
    start_ms: int | None = None
    end_ms: int | None = None

    try:
        if start_date:
            start_ms = _parse_datetime_to_ms(start_date, end_of_day=False)
        if end_date:
            end_ms = _parse_datetime_to_ms(end_date, end_of_day=True)
    except ValueError as e:
        return f"日期格式错误：{e}"

    if start_ms is not None and end_ms is not None and end_ms <= start_ms:
        return "结束时间不能早于或等于开始时间。"

    if not any([content_query, target_user_id is not None, user_name_query, message_id is not None, start_ms, end_ms]):
        return "请至少提供内容关键词、用户名称、用户ID、消息ID或时间范围中的一个搜索条件。"

    cfg = config.get("configurable", {})
    raw_user_id = cfg.get("user_id")
    raw_group_id = cfg.get("group_id")
    try:
        current_user_id = int(raw_user_id) if raw_user_id not in (None, "") else None
        group_id = int(raw_group_id) if raw_group_id is not None else None
    except (TypeError, ValueError):
        return "用户上下文错误，无法搜索聊天记录。"

    if group_id is None and current_user_id is None:
        return "缺少当前用户上下文，无法搜索私聊记录。"

    query_limit = max(1, min(limit, 100))

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
            limit=query_limit,

        )
    except Exception as e:
        logger.error(f"消息搜索失败: {e}")
        return "消息搜索失败，请稍后重试。"

    if not messages:
        return "未找到匹配的聊天记录。"

    return _format_search_results(messages)
