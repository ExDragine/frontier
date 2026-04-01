"""创建定时提醒工具"""

import json
import time
import datetime
import zoneinfo
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

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
    config: RunnableConfig | None = None,
) -> str:
    """创建定时提醒。到达指定时间后自动发送提醒消息给用户。

    Args:
        reminder_text: 提醒内容，例如"开会"、"取快递"、"吃药"
        remind_time: 提醒时间，北京时间(UTC+8)，格式 "YYYY-MM-DD HH:MM:SS"，例如 "2026-04-02 15:00:00"
        private: 是否通过私聊发送。True=私聊，False=在原群聊@用户（默认）
    """
    from plugins.clockwork import task_manager

    configurable = (config or {}).get("configurable", {})
    user_id: str = str(configurable.get("user_id", ""))
    group_id: int | None = configurable.get("group_id")

    dt = _parse_time(remind_time)
    if dt is None:
        return "时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式（北京时间）"

    now = datetime.datetime.now(tz=_SHANGHAI)
    if dt <= now:
        return f"提醒时间必须是将来的时间。当前北京时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    job_id = f"reminder_{user_id}_{int(time.time() * 1000)}"
    payload = {
        "text": reminder_text,
        "user_id": user_id,
        "group_id": group_id,
        "private": private,
    }

    await task_manager.register_task(
        job_id=job_id,
        name=f"提醒: {reminder_text[:20]}",
        handler_module="plugins.clockwork.reminder_handler",
        handler_function="fire_reminder",
        trigger_type="date",
        trigger_args={"run_date": dt.isoformat()},
        group_ids=[group_id] if group_id else [],
        description=json.dumps(payload, ensure_ascii=False),
        enabled=True,
        misfire_grace_time=300,
    )

    return f"已设置提醒：将在 {dt.strftime('%Y年%m月%d日 %H:%M')} 提醒你「{reminder_text}」"
