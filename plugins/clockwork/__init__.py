from nonebot import get_driver, logger, require

from utils.configs import EnvConfig
from utils.database import get_engine

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .task_manager import TaskExecutor, TaskManager  # noqa: E402
from .task_models import ScheduledTaskMetadata, TaskConfig, TaskExecutionHistory, TaskGroupMapping  # noqa: E402

# 初始化任务管理系统
engine = get_engine()
task_manager = TaskManager(scheduler, engine)
task_executor = TaskExecutor(task_manager)
task_manager.set_job_func(task_executor.execute)

driver = get_driver()
_REMOVED_TASKS = {
    "dreaming_daily_v3": "旧版结构化记忆后台整理任务",
    "eq_cenc": "旧版 CENC 定时轮询任务",
}

# 导入命令和处理器（必须在 task_manager 创建之后）
from . import agent_task_handler, task_commands, task_handlers  # noqa: E402, F401, I001


# ==================== 任务管理系统初始化 ====================


@driver.on_startup
async def init_task_system():
    """启动时初始化任务系统"""
    logger.info("正在初始化定时任务管理系统...")

    # 1. 创建数据库表
    TaskConfig.metadata.create_all(engine)
    TaskGroupMapping.metadata.create_all(engine)
    TaskExecutionHistory.metadata.create_all(engine)
    ScheduledTaskMetadata.metadata.create_all(engine)
    task_manager.ensure_schema()
    logger.info("数据库表创建完成")

    # 移除已下线任务，避免历史数据库配置在启动时重新注册。
    for job_id, description in _REMOVED_TASKS.items():
        if not await task_manager.get_task(job_id):
            continue
        try:
            await task_manager.delete_task(job_id)
            logger.info(f"已删除{description}")
        except Exception as exc:
            logger.warning(f"删除{description}失败: {exc}")

    # 2. 迁移旧提醒并读取所有任务配置
    await task_manager.migrate_legacy_reminders()
    tasks = await task_manager.list_tasks()
    logger.info(f"发现 {len(tasks)} 个已存在的任务配置")

    # 3. 注册所有任务到 APScheduler（每次启动都执行）
    for task in tasks:
        try:
            task_manager.add_job_to_scheduler(task)
            status = "已暂停" if not task.enabled else "已启用"
            logger.info(f"任务 {task.job_id} ({task.name}) 已注册到调度器（{status}）")
        except Exception as e:
            logger.error(f"注册任务 {task.job_id} 到调度器失败: {e}")

    # 4. 同步群组配置到 EnvConfig
    await task_manager.initialize()

    # 5. 注册 NRC 远行商人商品提醒推送（每天 8:10、12:10、16:10、20:10）
    try:
        await task_manager.register_task(
            job_id="nrc_merchant_alert",
            name="远行商人商品提醒推送",
            handler_module="plugins.clockwork.task_handlers",
            handler_function="nrc_merchant_alert",
            trigger_type="cron",
            trigger_args={"hour": "8,12,16,20", "minute": "10"},
            group_ids=EnvConfig.NRC_MERCHANT_GROUP_ID,
            description="每天定时检测远行商人是否上架目标商品（国王球、棱镜球、炫彩精灵蛋、祝福项坠、首领血脉秘药），有则推送提醒",
            metadata=ScheduledTaskMetadata(
                job_id="nrc_merchant_alert",
                owner_user_id="system",
                target_type="group",
                target_id=",".join(str(g) for g in EnvConfig.NRC_MERCHANT_GROUP_ID)
                if EnvConfig.NRC_MERCHANT_GROUP_ID
                else "0",
                prompt="",
                created_from="system",
            ),
        )
        logger.info("NRC 远行商人商品提醒推送已注册（cron: 8,12,16,20:10 Asia/Shanghai）")
    except Exception as exc:
        logger.warning(f"注册 NRC 远行商人任务失败（可能已存在）: {exc}")

    logger.info("定时任务管理系统初始化完成！")


@driver.on_shutdown
async def shutdown_task_system():
    from utils.http_client import aclose_all

    await aclose_all()
