from nonebot import get_driver, logger, require

from utils.database import get_engine

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .task_manager import TaskExecutor, TaskManager  # noqa: E402
from .task_models import ScheduledTaskMetadata, TaskConfig, TaskExecutionHistory, TaskGroupMapping  # noqa: E402

# 初始化任务管理系统
engine = get_engine()
task_manager = TaskManager(scheduler, engine)
task_executor = TaskExecutor(task_manager)
task_manager.set_job_func(task_executor.execute)

driver = get_driver()

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

    # 5. 注册主动智能引擎（每 10 分钟评估一次）
    from .proactive_engine import ProactiveEngine

    proactive = ProactiveEngine()
    scheduler.add_job(
        func=proactive.evaluate_all_groups,
        trigger="interval",
        id="proactive_engine",
        minutes=10,
        misfire_grace_time=120,
        replace_existing=True,
    )
    logger.info("主动智能引擎已注册（每 10 分钟评估一次）")

    logger.info("定时任务管理系统初始化完成！")


@driver.on_shutdown
async def shutdown_task_system():
    from utils.http_client import aclose_all

    await aclose_all()
