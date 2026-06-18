"""创建定时提醒工具"""

import datetime
import zoneinfo

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from tools.scheduled_task import create_scheduled_task_record

_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")
_TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")


def _parse_time(raw: str) -> datetime.datetime | None:
    for fmt in _TIME_FORMATS:
        try:
            return datetime.datetime.strptime(raw, fmt).replace(tzinfo=_SHANGHAI)
        except ValueError:
            continue
    return None


@tool(response_format="content")
async def create_reminder(
    reminder_text: str,
    remind_time: str,
    private: bool = False,
    config: RunnableConfig = None,
) -> str:
    """创建定时提醒。到达指定时间后自动发送提醒消息给用户。

    Args:
        reminder_text: 提醒内容，例如"开会"、"取快递"、"吃药"
        remind_time: 提醒时间，北京时间(UTC+8)，格式 "YYYY-MM-DD HH:MM:SS"，例如 "2026-04-02 15:00:00"
        private: 是否通过私聊发送。True=私聊，False=在原群聊@用户（默认）
    """
    configurable = (config or {}).get("configurable", {})
    group_id: int | None = configurable.get("group_id")

    dt = _parse_time(remind_time)
    if dt is None:
        return "时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式（北京时间）"

    now = datetime.datetime.now(tz=_SHANGHAI)
    if dt <= now:
        return f"提醒时间必须是将来的时间。当前北京时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    target_type = "user" if private or not group_id else "group"
    target_id = configurable.get("user_id") if target_type == "user" else group_id
    prompt = f"在指定时间提醒用户：{reminder_text}。请生成一条简短提醒消息。"
    result = await create_scheduled_task_record(
        name=f"提醒: {reminder_text[:20]}",
        prompt=prompt,
        trigger_type="date",
        trigger_args={"run_date": dt.isoformat()},
        target_type=target_type,
        target_id=target_id,
        config=config,
        created_from="reminder_tool",
        validate_target=False,
    )

    if not result.startswith("已创建自动任务"):
        return result
    return f"已设置提醒：将在 {dt.strftime('%Y年%m月%d日 %H:%M')} 提醒你「{reminder_text}」"
