"""创建和管理统一自动任务工具。"""

import json
import time
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import get_bot


def _configurable(config: RunnableConfig | None) -> dict:
    return (config or {}).get("configurable", {})


def _owner_user_id(config: RunnableConfig | None) -> str:
    return str(_configurable(config).get("user_id") or "")


def _default_target(config: RunnableConfig | None) -> tuple[str, str] | tuple[None, None]:
    cfg = _configurable(config)
    group_id = cfg.get("group_id")
    if group_id is not None:
        return "group", str(group_id)
    user_id = cfg.get("user_id")
    if user_id:
        return "user", str(user_id)
    return None, None


async def _validate_target(target_type: str, target_id: str) -> str | None:
    bot = get_bot()
    if target_type == "group":
        groups = await bot.get_group_list()
        if any(str(getattr(group, "group_id", "")) == str(target_id) for group in groups):
            return None
        return f"Bot 当前不可达群 {target_id}"
    if target_type == "user":
        try:
            await bot.get_friend_info(user_id=int(target_id))
        except Exception:
            return f"Bot 当前不可达用户 {target_id}"
        return None
    return "target_type 只能是 group 或 user"


def _trigger_label(trigger_type: str, trigger_args: dict[str, Any]) -> str:
    if trigger_type == "date":
        return str(trigger_args.get("run_date", "指定时间"))
    if trigger_type == "cron":
        return f"cron {json.dumps(trigger_args, ensure_ascii=False)}"
    if trigger_type == "interval":
        return f"interval {json.dumps(trigger_args, ensure_ascii=False)}"
    return f"{trigger_type} {json.dumps(trigger_args, ensure_ascii=False)}"


async def create_scheduled_task_record(
    *,
    name: str,
    prompt: str,
    trigger_type: str,
    trigger_args: dict[str, Any],
    target_type: str | None,
    target_id: str | int | None,
    config: RunnableConfig | None,
    created_from: str,
    validate_target: bool = True,
) -> str:
    from plugins.clockwork import task_manager

    owner_user_id = _owner_user_id(config)
    if not owner_user_id:
        return "缺少用户上下文，无法创建自动任务"

    if (target_type is None) != (target_id is None):
        return "target_type 和 target_id 必须同时传入，或都不传以使用当前会话"

    if target_type is None and target_id is None:
        default_target_type, default_target_id = _default_target(config)
        if default_target_type is None or default_target_id is None:
            return "缺少投递目标：请在群聊/私聊中使用，或显式传入 target_type 和 target_id"
        target_type = default_target_type
        target_id = default_target_id

    target_type = str(target_type)
    target_id = str(target_id)
    if validate_target:
        error = await _validate_target(target_type, target_id)
        if error:
            return error

    job_id = f"scheduled_{owner_user_id}_{int(time.time() * 1000)}"
    await task_manager.register_scheduled_task(
        job_id=job_id,
        name=name[:80] or "自动任务",
        prompt=prompt,
        trigger_type=trigger_type,
        trigger_args=trigger_args,
        owner_user_id=owner_user_id,
        target_type=target_type,
        target_id=target_id,
        description=prompt[:120],
        created_from=created_from,
    )
    return f"已创建自动任务 {job_id}，触发时间：{_trigger_label(trigger_type, trigger_args)}，目标：{target_type}:{target_id}"


@tool(response_format="content")
async def create_scheduled_task(
    name: str,
    prompt: str,
    trigger_type: str,
    trigger_args: dict,
    target_type: str | None = None,
    target_id: str | int | None = None,
    config: RunnableConfig = None,
) -> str:
    """创建统一自动任务，到点后由 Agent 执行 prompt 并投递最终回复。

    Args:
        name: 任务名称
        prompt: 到点后交给 Agent 执行的任务说明
        trigger_type: APScheduler 触发器类型，支持 date、cron、interval
        trigger_args: APScheduler 触发器参数，例如 {"run_date": "2026-05-16T12:00:00+08:00"}
        target_type: 可选投递目标类型，group 或 user；未传时使用当前会话
        target_id: 可选投递目标 ID；未传时使用当前会话
    """
    return await create_scheduled_task_record(
        name=name,
        prompt=prompt,
        trigger_type=trigger_type,
        trigger_args=trigger_args,
        target_type=target_type,
        target_id=target_id,
        config=config,
        created_from="tool",
        validate_target=True,
    )


@tool(response_format="content")
async def list_my_scheduled_tasks(include_archived: bool = False, config: RunnableConfig = None) -> str:
    """列出当前用户创建的自动任务。"""
    from plugins.clockwork import task_manager

    owner_user_id = _owner_user_id(config)
    if not owner_user_id:
        return "缺少用户上下文，无法查询自动任务"
    tasks = await task_manager.list_tasks(owner_user_id=owner_user_id, include_archived=include_archived)
    if not tasks:
        return "你还没有自动任务。"
    metadata_map = await task_manager.get_task_metadata_map([task.job_id for task in tasks])
    lines = [f"你的自动任务（{len(tasks)} 个）："]
    for task in tasks:
        metadata = metadata_map.get(task.job_id)
        archived = "已归档" if metadata and metadata.archived else ("启用" if task.enabled else "暂停")
        target = f"{metadata.target_type}:{metadata.target_id}" if metadata else "未知目标"
        lines.append(f"- {task.job_id} [{archived}] {task.name} -> {target}")
    return "\n".join(lines)


async def _manage_my_task(job_id: str, config: RunnableConfig | None, operation: str) -> str:
    from plugins.clockwork import task_manager

    owner_user_id = _owner_user_id(config)
    if not owner_user_id:
        return "缺少用户上下文，无法管理自动任务"
    if not await task_manager.user_can_manage_task(job_id, owner_user_id):
        return f"没有权限管理任务 {job_id}"
    if operation == "cancel":
        success = await task_manager.archive_task(job_id)
        action = "取消"
    elif operation == "pause":
        success = await task_manager.disable_task(job_id)
        action = "暂停"
    elif operation == "resume":
        success = await task_manager.enable_task(job_id)
        action = "恢复"
    else:
        return f"未知操作：{operation}"
    return f"任务 {job_id} 已{action}" if success else f"任务 {job_id} {action}失败"


@tool(response_format="content")
async def cancel_my_scheduled_task(job_id: str, config: RunnableConfig = None) -> str:
    """取消当前用户自己的自动任务。"""
    return await _manage_my_task(job_id, config, "cancel")


@tool(response_format="content")
async def pause_my_scheduled_task(job_id: str, config: RunnableConfig = None) -> str:
    """暂停当前用户自己的自动任务。"""
    return await _manage_my_task(job_id, config, "pause")


@tool(response_format="content")
async def resume_my_scheduled_task(job_id: str, config: RunnableConfig = None) -> str:
    """恢复当前用户自己的自动任务。"""
    return await _manage_my_task(job_id, config, "resume")
