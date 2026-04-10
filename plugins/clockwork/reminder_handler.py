"""定时提醒处理函数"""

import json

from nonebot import logger
from nonebot_plugin_alconna import At, Target, Text, UniMessage


async def fire_reminder(job_id: str = "", **kwargs) -> None:
    """触发提醒：读取 payload、发送消息、自清理。"""
    from plugins.clockwork import task_manager

    task = await task_manager.get_task(job_id)
    if not task or not task.description:
        logger.warning(f"提醒任务 {job_id} 不存在或缺少 payload，跳过")
        return

    try:
        payload: dict = json.loads(task.description)
    except json.JSONDecodeError:
        logger.error(f"提醒任务 {job_id} 的 description 不是合法 JSON")
        await task_manager.delete_task(job_id)
        return

    text: str = payload.get("text", "")
    user_id: str = str(payload.get("user_id", ""))
    group_id: int | None = payload.get("group_id")
    private: bool = payload.get("private", False)

    message = UniMessage([Text(f"⏰ 提醒：{text}")])

    if private or not group_id:
        target = Target.user(user_id)
    else:
        message = UniMessage([At("user", user_id), Text(f" ⏰ 提醒：{text}")])
        target = Target.group(str(group_id))

    try:
        await message.send(target=target)
        logger.info(f"提醒 {job_id} 已发送 → {'私聊' if private or not group_id else f'群 {group_id}'}")
    except Exception as e:
        logger.error(f"提醒 {job_id} 发送失败: {e}")
    finally:
        await task_manager.delete_task(job_id)
