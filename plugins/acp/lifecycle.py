"""NoneBot lifecycle hooks for ACP processes and workspace maintenance."""

from nonebot import get_driver, logger
from nonebot_plugin_apscheduler import scheduler

from utils.timeutil import add_daily_job

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
    add_daily_job(scheduler, CACHE_CLEANUP_JOB_ID, run_daily_cache_cleanup)


@driver.on_shutdown
async def shutdown_acp() -> None:
    await acp_service.close()
