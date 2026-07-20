# ruff: noqa: C901

import datetime
import json
import zoneinfo

from nonebot import get_driver, on_command
from nonebot.adapters.milky.event import MessageEvent


# 延迟导入避免循环依赖
def get_task_manager():
    from . import task_manager

    return task_manager


task_cmd = on_command("task", priority=6, block=True, aliases={"任务", "定时任务"})


def _is_superuser(user_id: str) -> bool:
    """检查是否为超级用户"""
    superusers = {str(item) for item in getattr(get_driver().config, "superusers", set())}
    return str(user_id) in superusers


def _strip_task_prefix(text: str) -> str:
    """移除命令前缀"""
    stripped = text.strip()
    for prefix in ("/task", "task", "/任务", "任务", "/定时任务", "定时任务"):
        if stripped.lower().startswith(prefix.lower()):
            return stripped[len(prefix) :].strip()
    return stripped


def _format_time(ts: int | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if not ts:
        return "无"
    return datetime.datetime.fromtimestamp(ts).astimezone(zoneinfo.ZoneInfo("Asia/Shanghai")).strftime(fmt)


async def _can_access_task(job_id: str, user_id: str, is_superuser: bool) -> bool:
    return await get_task_manager().user_can_manage_task(job_id, user_id, is_superuser)


def _target_label(metadata) -> str:
    if not metadata:
        return "系统任务"
    return f"{metadata.target_type}:{metadata.target_id}"


def _help_message() -> str:
    """返回帮助信息"""
    return (
        "定时任务管理命令:\n"
        "/task my [all]                               - 查看我的自动任务\n"
        "/task info <job_id>                          - 查看任务详情\n"
        "/task pause <job_id>                         - 暂停我的自动任务\n"
        "/task resume <job_id>                        - 恢复我的自动任务\n"
        "/task cancel <job_id>                        - 取消我的自动任务\n"
        "/task run <job_id>                           - 立即运行我的自动任务\n"
        "\n管理员命令:\n"
        "/task list [enabled|disabled|all]           - 列出任务\n"
        "/task enable <job_id>                        - 启用任务\n"
        "/task disable <job_id>                       - 禁用任务\n"
        "/task trigger <job_id> cron <时间>           - 修改cron触发器\n"
        "    示例: /task trigger apod_everyday cron 20:00\n"
        "/task trigger <job_id> interval <分钟数>     - 修改interval触发器\n"
        "    示例: /task trigger eq_usgs interval 5\n"
        "/task groups <job_id> set <群号1> [群号2...]  - 设置推送群组\n"
        "/task groups <job_id> add <群号>             - 添加推送群组\n"
        "/task groups <job_id> remove <群号>          - 移除推送群组\n"
        "/task history <job_id> [limit]               - 查看执行历史\n"
        "/task stats <job_id>                         - 查看统计信息"
    )


@task_cmd.handle()
async def handle_task_command(event: MessageEvent):
    """处理任务命令"""
    from nonebot_plugin_alconna import UniMessage

    user_id = event.get_user_id()
    is_superuser = _is_superuser(user_id)

    text = _strip_task_prefix(event.get_plaintext())
    if not text:
        await UniMessage.text(_help_message()).send()
        return

    args = text.split()
    action = args[0].lower()

    # 路由到具体的处理函数
    if action in {"my", "我的"}:
        await handle_task_my(args, user_id)
        return

    if action in {"list", "列表", "ls"}:
        if not is_superuser:
            await UniMessage.text("普通用户请使用 /task my 查看自己的自动任务").send()
            return
        await handle_task_list(args)
        return

    if action in {"info", "详情", "show"}:
        await handle_task_info(args, user_id=user_id, is_superuser=is_superuser)
        return

    if action in {"enable", "启用", "开启"}:
        if not is_superuser:
            await UniMessage.text("普通用户请使用 /task resume <job_id> 恢复自己的自动任务").send()
            return
        await handle_task_enable(args)
        return

    if action in {"disable", "禁用", "关闭"}:
        if not is_superuser:
            await UniMessage.text("普通用户请使用 /task pause <job_id> 暂停自己的自动任务").send()
            return
        await handle_task_disable(args)
        return

    if action in {"pause", "暂停"}:
        await handle_task_pause(args, user_id=user_id, is_superuser=is_superuser)
        return

    if action in {"resume", "恢复"}:
        await handle_task_resume(args, user_id=user_id, is_superuser=is_superuser)
        return

    if action in {"cancel", "取消"}:
        await handle_task_cancel(args, user_id=user_id, is_superuser=is_superuser)
        return

    if action in {"run", "运行", "立即运行"}:
        await handle_task_run(args, user_id=user_id, is_superuser=is_superuser)
        return

    if action in {"trigger", "触发器", "时间"}:
        if not is_superuser:
            await UniMessage.text("此命令仅限管理员使用").send()
            return
        await handle_task_trigger(args)
        return

    if action in {"groups", "群组", "group"}:
        if not is_superuser:
            await UniMessage.text("此命令仅限管理员使用").send()
            return
        await handle_task_groups(args)
        return

    if action in {"history", "历史", "hist"}:
        await handle_task_history(args, user_id=user_id, is_superuser=is_superuser)
        return

    if action in {"stats", "统计", "stat"}:
        await handle_task_stats(args, user_id=user_id, is_superuser=is_superuser)
        return

    await UniMessage.text(_help_message()).send()


async def handle_task_my(args: list[str], user_id: str):
    """处理 /task my 命令"""
    from nonebot_plugin_alconna import UniMessage

    include_archived = len(args) > 1 and args[1].lower() in {"all", "全部", "archived", "归档"}
    tasks = await get_task_manager().list_tasks(owner_user_id=user_id, include_archived=include_archived)
    if not tasks:
        await UniMessage.text("你还没有自动任务").send()
        return

    metadata_map = await get_task_manager().get_task_metadata_map([task.job_id for task in tasks])
    lines = [f"我的自动任务 (共{len(tasks)}个):\n"]
    for task in tasks:
        metadata = metadata_map.get(task.job_id)
        status = "📦" if metadata and metadata.archived else ("✅" if task.enabled else "⏸️")
        next_run = _format_time(task.next_run_time, "%m-%d %H:%M") if task.next_run_time else "无"
        lines.append(f"{status} {task.name} ({task.job_id})")
        lines.append(f"   目标: {_target_label(metadata)}")
        lines.append(f"   下次执行: {next_run}")
        if metadata:
            lines.append(f"   Prompt: {metadata.prompt[:80]}")
        lines.append("")

    await UniMessage.text("\n".join(lines)).send()


async def handle_task_list(args: list[str]):
    """处理 /task list 命令"""
    from nonebot_plugin_alconna import UniMessage

    filter_type = args[1] if len(args) > 1 else "all"
    enabled = None

    if filter_type in {"enabled", "启用"}:
        enabled = True
    elif filter_type in {"disabled", "禁用"}:
        enabled = False

    tasks = await get_task_manager().list_tasks(enabled=enabled, include_archived=True)

    if not tasks:
        await UniMessage.text("没有找到任务").send()
        return

    # 格式化输出
    lines = [f"定时任务列表 (共{len(tasks)}个):\n"]
    metadata_map = await get_task_manager().get_task_metadata_map([task.job_id for task in tasks])
    for task in tasks:
        metadata = metadata_map.get(task.job_id)
        status = "📦" if metadata and metadata.archived else ("✅" if task.enabled else "⏸️")
        trigger_args = json.loads(task.trigger_args)

        # 格式化触发器信息
        if task.trigger_type == "cron":
            if "year" in trigger_args:
                trigger_info = f"cron: {trigger_args.get('year')}-{trigger_args.get('month')}-{trigger_args.get('day')} {trigger_args.get('hour')}:{trigger_args.get('minute')}:{trigger_args.get('second', '00')}"
            else:
                trigger_info = f"cron: {trigger_args.get('hour', '*')}:{trigger_args.get('minute', '0')}"
        elif task.trigger_type == "interval":
            trigger_info = f"interval: 每{trigger_args.get('minutes', 1)}分钟"
        else:
            trigger_info = task.trigger_type

        # 下次执行时间
        if task.next_run_time:
            next_run = _format_time(task.next_run_time, "%m-%d %H:%M")
        else:
            next_run = "无"

        lines.append(f"{status} {task.name} ({task.job_id})")
        lines.append(f"   类型: {'自动任务' if metadata else '系统任务'}")
        lines.append(f"   目标: {_target_label(metadata)}")
        lines.append(f"   触发器: {trigger_info}")
        lines.append(f"   下次执行: {next_run}")
        lines.append(f"   成功/失败: {task.success_runs}/{task.failed_runs}\n")

    await UniMessage.text("\n".join(lines)).send()


async def handle_task_info(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task info 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task info <job_id>").send()
        return

    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限查看任务 {job_id}").send()
        return

    task = await get_task_manager().get_task(job_id)

    if not task:
        await UniMessage.text(f"任务 {job_id} 不存在").send()
        return

    # 获取群组配置
    group_ids = await get_task_manager().get_task_groups(job_id)
    groups_str = ", ".join(map(str, group_ids)) if group_ids else "无"
    metadata = await get_task_manager().get_task_metadata(job_id)

    # 解析触发器
    trigger_args = json.loads(task.trigger_args)
    trigger_str = json.dumps(trigger_args, ensure_ascii=False)

    # 格式化时间
    created_at = _format_time(task.created_at)
    last_run = _format_time(task.last_run_time) if task.last_run_time else "从未执行"
    next_run = _format_time(task.next_run_time)

    # 计算成功率
    success_rate = (task.success_runs / task.total_runs * 100) if task.total_runs > 0 else 0

    info = f"""任务详情:
📋 名称: {task.name}
🆔 ID: {task.job_id}
📝 描述: {task.description or "无"}
⚙️ 处理函数: {task.handler_module}.{task.handler_function}
🧭 类型: {"自动任务" if metadata else "系统任务"}
🎯 目标: {_target_label(metadata)}
👤 创建者: {metadata.owner_user_id if metadata else "系统"}
📦 归档: {"是" if metadata and metadata.archived else "否"}

⏰ 触发器:
  类型: {task.trigger_type}
  参数: {trigger_str}
  容错时间: {task.misfire_grace_time}秒

📊 状态:
  当前状态: {"✅ 启用" if task.enabled else "⏸️ 禁用"}
  创建时间: {created_at}
  上次执行: {last_run}
  下次执行: {next_run}

📈 统计:
  总执行次数: {task.total_runs}
  成功次数: {task.success_runs}
  失败次数: {task.failed_runs}
  成功率: {success_rate:.1f}%

👥 推送群组: {groups_str}
"""
    if metadata:
        info += f"\n🧠 Prompt:\n{metadata.prompt}"

    await UniMessage.text(info).send()


async def handle_task_enable(args: list[str]):
    """处理 /task enable 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task enable <job_id>").send()
        return

    job_id = args[1]
    success = await get_task_manager().enable_task(job_id)

    if success:
        await UniMessage.text(f"任务 {job_id} 已启用").send()
    else:
        await UniMessage.text(f"启用任务 {job_id} 失败，请检查任务是否存在").send()


async def handle_task_disable(args: list[str]):
    """处理 /task disable 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task disable <job_id>").send()
        return

    job_id = args[1]
    success = await get_task_manager().disable_task(job_id)

    if success:
        await UniMessage.text(f"任务 {job_id} 已禁用").send()
    else:
        await UniMessage.text(f"禁用任务 {job_id} 失败，请检查任务是否存在").send()


async def handle_task_pause(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task pause 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task pause <job_id>").send()
        return
    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限暂停任务 {job_id}").send()
        return
    success = await get_task_manager().disable_task(job_id)
    await UniMessage.text(f"任务 {job_id} 已暂停" if success else f"暂停任务 {job_id} 失败").send()


async def handle_task_resume(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task resume 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task resume <job_id>").send()
        return
    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限恢复任务 {job_id}").send()
        return
    success = await get_task_manager().enable_task(job_id)
    await UniMessage.text(f"任务 {job_id} 已恢复" if success else f"恢复任务 {job_id} 失败").send()


async def handle_task_cancel(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task cancel 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task cancel <job_id>").send()
        return
    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限取消任务 {job_id}").send()
        return
    success = await get_task_manager().archive_task(job_id)
    await UniMessage.text(f"任务 {job_id} 已取消" if success else f"取消任务 {job_id} 失败").send()


async def handle_task_run(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task run 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task run <job_id>").send()
        return
    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限运行任务 {job_id}").send()
        return
    success = await get_task_manager().run_task_now(job_id)
    await UniMessage.text(f"任务 {job_id} 已运行" if success else f"运行任务 {job_id} 失败").send()


async def handle_task_trigger(args: list[str]):
    """处理 /task trigger 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 4:
        await UniMessage.text("用法: /task trigger <job_id> <cron|interval> <参数>").send()
        return

    job_id = args[1]
    trigger_type = args[2]

    if trigger_type == "cron":
        # 解析cron表达式: "19:00" -> {"hour": "19", "minute": "0"}
        time_str = args[3]
        if ":" in time_str:
            parts = time_str.split(":")
            trigger_args = {"hour": parts[0], "minute": parts[1] if len(parts) > 1 else "0"}
        else:
            await UniMessage.text("cron时间格式错误，应为 HH:MM，例如: 19:00").send()
            return
    elif trigger_type == "interval":
        try:
            minutes = int(args[3])
            trigger_args = {"minutes": minutes}
        except ValueError:
            await UniMessage.text("interval参数必须是整数（分钟数）").send()
            return
    else:
        await UniMessage.text("触发器类型只能是 cron 或 interval").send()
        return

    success = await get_task_manager().update_task_trigger(job_id, trigger_type, trigger_args)

    if success:
        await UniMessage.text(f"任务 {job_id} 触发器已更新为 {trigger_type}: {trigger_args}").send()
    else:
        await UniMessage.text("更新失败，请检查任务是否存在").send()


async def handle_task_groups(args: list[str]):
    """处理 /task groups 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 3:
        await UniMessage.text("用法: /task groups <job_id> <set|add|remove> <群号...>").send()
        return

    job_id = args[1]
    operation = args[2]

    # 获取当前群组配置
    current_groups = await get_task_manager().get_task_groups(job_id)

    if operation in {"set", "设置"}:
        # 设置群组（覆盖）
        if len(args) < 4:
            await UniMessage.text("用法: /task groups <job_id> set <群号1> [群号2...]").send()
            return

        try:
            new_groups = [int(g) for g in args[3:]]
        except ValueError:
            await UniMessage.text("群号必须是整数").send()
            return

        success = await get_task_manager().update_task_groups(job_id, new_groups)
        if success:
            # 同步到 EnvConfig
            await get_task_manager().initialize()
            await UniMessage.text(f"任务 {job_id} 群组已设置为: {', '.join(map(str, new_groups))}").send()
        else:
            await UniMessage.text("设置失败，请检查任务是否存在").send()

    elif operation in {"add", "添加"}:
        # 添加群组
        if len(args) < 4:
            await UniMessage.text("用法: /task groups <job_id> add <群号>").send()
            return

        try:
            group_to_add = int(args[3])
        except ValueError:
            await UniMessage.text("群号必须是整数").send()
            return

        if group_to_add in current_groups:
            await UniMessage.text(f"群组 {group_to_add} 已存在于任务 {job_id} 中").send()
            return

        new_groups = current_groups + [group_to_add]
        success = await get_task_manager().update_task_groups(job_id, new_groups)
        if success:
            await get_task_manager().initialize()
            await UniMessage.text(f"已添加群组 {group_to_add} 到任务 {job_id}").send()
        else:
            await UniMessage.text("添加失败，请检查任务是否存在").send()

    elif operation in {"remove", "移除", "删除"}:
        # 移除群组
        if len(args) < 4:
            await UniMessage.text("用法: /task groups <job_id> remove <群号>").send()
            return

        try:
            group_to_remove = int(args[3])
        except ValueError:
            await UniMessage.text("群号必须是整数").send()
            return

        if group_to_remove not in current_groups:
            await UniMessage.text(f"群组 {group_to_remove} 不在任务 {job_id} 中").send()
            return

        new_groups = [g for g in current_groups if g != group_to_remove]
        success = await get_task_manager().update_task_groups(job_id, new_groups)
        if success:
            await get_task_manager().initialize()
            await UniMessage.text(f"已从任务 {job_id} 移除群组 {group_to_remove}").send()
        else:
            await UniMessage.text("移除失败，请检查任务是否存在").send()

    else:
        await UniMessage.text("操作必须是 set、add 或 remove").send()


async def handle_task_history(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task history 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task history <job_id> [limit]").send()
        return

    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限查看任务 {job_id} 的历史").send()
        return
    limit = int(args[2]) if len(args) > 2 else 20

    history = await get_task_manager().get_execution_history(job_id=job_id, limit=limit)

    if not history:
        await UniMessage.text(f"任务 {job_id} 没有执行历史").send()
        return

    lines = [f"任务 {job_id} 执行历史 (最近{len(history)}条):\n"]

    for h in history:
        time_str = _format_time(h.execution_time, "%m-%d %H:%M:%S")

        status_icon = {"success": "✅", "failed": "❌", "skipped": "⏭️", "missed": "⏰"}.get(h.status, "❓")

        duration_str = f"{h.duration_ms}ms" if h.duration_ms else "-"

        line = f"{status_icon} {time_str} | {h.status.upper()} | 耗时: {duration_str}"

        if h.error_message:
            line += f"\n   错误: {h.error_message[:100]}"
        if h.output_summary:
            line += f"\n   输出: {h.output_summary[:100]}"

        lines.append(line)

    await UniMessage.text("\n".join(lines)).send()


async def handle_task_stats(args: list[str], user_id: str, is_superuser: bool):
    """处理 /task stats 命令"""
    from nonebot_plugin_alconna import UniMessage

    if len(args) < 2:
        await UniMessage.text("用法: /task stats <job_id>").send()
        return

    job_id = args[1]
    if not await _can_access_task(job_id, user_id, is_superuser):
        await UniMessage.text(f"没有权限查看任务 {job_id} 的统计").send()
        return
    stats = await get_task_manager().get_task_statistics(job_id)

    if not stats:
        await UniMessage.text(f"任务 {job_id} 不存在").send()
        return

    last_run = _format_time(stats["last_run_time"]) if stats.get("last_run_time") else "从未执行"
    next_run = _format_time(stats["next_run_time"])

    stats_text = f"""任务统计: {stats["name"]} ({stats["job_id"]})

📊 执行统计:
  总执行次数: {stats["total_runs"]}
  成功次数: {stats["success_runs"]}
  失败次数: {stats["failed_runs"]}
  成功率: {stats["success_rate"] * 100:.1f}%

⏰ 时间信息:
  上次执行: {last_run}
  下次执行: {next_run}

📝 最近执行记录:
"""

    for h in stats.get("recent_history", [])[:5]:
        exec_time = _format_time(h["execution_time"], "%m-%d %H:%M")
        status_icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(h["status"], "❓")
        duration_str = f"{h['duration_ms']}ms" if h.get("duration_ms") else "-"
        stats_text += f"  {status_icon} {exec_time} | {duration_str}\n"

    await UniMessage.text(stats_text).send()
