from nonebot import logger

from utils.configs import EnvConfig

from .task_manager import TaskManager


async def migrate_existing_tasks(task_manager: TaskManager):
    """迁移现有任务到数据库"""

    TASKS_TO_MIGRATE = [
        {
            "job_id": "apod_everyday",
            "name": "NASA每日一图",
            "description": "每天19:00推送NASA天文图片并翻译",
            "handler_module": "plugins.clockwork.task_handlers",
            "handler_function": "apod_everyday",
            "trigger_type": "cron",
            "trigger_args": {"hour": "19", "minute": "0"},
            "group_ids": EnvConfig.APOD_GROUP_ID,
            "misfire_grace_time": 60,
        },
        {
            "job_id": "earth_now",
            "name": "实时地球图",
            "description": "每天8:30、12:30、18:30推送地球卫星图",
            "handler_module": "plugins.clockwork.task_handlers",
            "handler_function": "earth_now",
            "trigger_type": "cron",
            "trigger_args": {"hour": "8,12,18", "minute": "30"},
            "group_ids": EnvConfig.EARTH_NOW_GROUP_ID,
            "misfire_grace_time": 180,
        },
        {
            "job_id": "eq_cenc",
            "name": "中国地震速报",
            "description": "每分钟检测中国地震台网速报",
            "handler_module": "plugins.clockwork.task_handlers",
            "handler_function": "eq_cenc",
            "trigger_type": "interval",
            "trigger_args": {"minutes": 1},
            "group_ids": EnvConfig.EARTHQUAKE_GROUP_ID,
            "misfire_grace_time": 30,
        },
        {
            "job_id": "eq_usgs",
            "name": "美国地震速报",
            "description": "每5分钟检测USGS地震速报",
            "handler_module": "plugins.clockwork.task_handlers",
            "handler_function": "eq_usgs",
            "trigger_type": "interval",
            "trigger_args": {"minutes": 5},
            "group_ids": EnvConfig.EARTHQUAKE_GROUP_ID,
            "misfire_grace_time": 60,
        },
        {
            "job_id": "daily_news",
            "name": "每日新闻摘要",
            "description": "每天8:30、14:30、20:30推送AI生成的新闻摘要",
            "handler_module": "plugins.clockwork.task_handlers",
            "handler_function": "daily_news",
            "trigger_type": "cron",
            "trigger_args": {"hour": "8,14,20", "minute": "30"},
            "group_ids": EnvConfig.NEWS_SUMMARY_GROUP_ID,
            "misfire_grace_time": 300,
        },
        {
            "job_id": "happy_new_year",
            "name": "新年贺词",
            "description": "2026年2月16日23:59:59发送新年祝福",
            "handler_module": "plugins.clockwork.task_handlers",
            "handler_function": "happy_new_year",
            "trigger_type": "cron",
            "trigger_args": {"year": "2026", "month": "2", "day": "16", "hour": "23", "minute": "59", "second": "59"},
            "group_ids": [],  # 空列表表示发送给所有群
            "misfire_grace_time": 5,
        },
    ]

    logger.info("开始迁移现有任务到数据库...")

    for task_config in TASKS_TO_MIGRATE:
        try:
            await task_manager.register_task(**task_config)
            logger.info(f"✓ 任务 {task_config['job_id']} 迁移成功")
        except Exception as e:
            logger.error(f"✗ 任务 {task_config['job_id']} 迁移失败: {e}")

    logger.info("任务迁移完成！")
