import datetime
import zoneinfo
from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from nonebot import logger

from utils.agents import assistant_agent
from utils.configs import EnvConfig
from utils.database import MessageDatabase

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


@tool(response_format="content")
async def summarize_messages(
    start_date: str,
    end_date: str,
    user_id: Annotated[str, InjectedState("user_id")],
    group_id: Annotated[int | None, InjectedState("group_id")] = None,
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
