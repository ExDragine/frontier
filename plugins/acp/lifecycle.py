"""NoneBot lifecycle hooks for ACP processes and workspace maintenance."""

from nonebot import get_driver, logger
from nonebot_plugin_apscheduler import scheduler

from .service import acp_service

driver = get_driver()
CACHE_CLEANUP_JOB_ID = "frontier_acp_daily_cache_cleanup"


async def run_daily_cache_cleanup() -> None:
    try:
        cleaned_scopes = await acp_service.cleanup_cache()
        if cleaned_scopes:
            logger.info("每日清理 ACP 缓存 scope: {}", cleaned_scopes)
    except Exception as exc:
        logger.warning("每日 ACP 缓存清理失败: {}: {}", type(exc).__name__, exc)


@driver.on_startup
async def startup_acp() -> None:
    scheduler.add_job(
        run_daily_cache_cleanup,
        "cron",
        id=CACHE_CLEANUP_JOB_ID,
        hour=4,
        minute=0,
        timezone="Asia/Shanghai",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )


@driver.on_shutdown
async def shutdown_acp() -> None:
    await acp_service.close()
