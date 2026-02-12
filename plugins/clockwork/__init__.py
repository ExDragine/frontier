from nonebot import get_driver, logger, require
from sqlmodel import create_engine

from utils.database import DATABASE_FILE

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .task_manager import TaskExecutor, TaskManager  # noqa: E402
from .task_migration import migrate_existing_tasks  # noqa: E402
from .task_models import TaskConfig, TaskExecutionHistory, TaskGroupMapping  # noqa: E402

# 初始化任务管理系统
engine = create_engine(DATABASE_FILE)
task_manager = TaskManager(scheduler, engine)
task_executor = TaskExecutor(task_manager)
task_manager.set_job_func(task_executor.execute)

driver = get_driver()

# 导入命令和处理器（必须在 task_manager 创建之后）
from . import task_commands, task_handlers  # noqa: E402, F401


# ==================== 任务管理系统初始化 ====================


@driver.on_startup
async def init_task_system():
    """启动时初始化任务系统"""
    logger.info("正在初始化定时任务管理系统...")

    # 1. 创建数据库表
    TaskConfig.metadata.create_all(engine)
    TaskGroupMapping.metadata.create_all(engine)
    TaskExecutionHistory.metadata.create_all(engine)
    logger.info("数据库表创建完成")

    # 2. 检查是否需要迁移
    tasks = await task_manager.list_tasks()

    if len(tasks) == 0:
        logger.info("检测到首次启动，开始迁移现有任务...")
        await migrate_existing_tasks(task_manager)
        tasks = await task_manager.list_tasks()
    else:
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

    logger.info("定时任务管理系统初始化完成！")
