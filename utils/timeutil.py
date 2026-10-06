"""Shared timezone constant and APScheduler helpers."""

from collections.abc import Callable
from typing import Any
from zoneinfo import ZoneInfo

__all__ = ["SHANGHAI", "add_daily_job"]

#: The single process-wide reference timezone for user-facing schedules and formatting.
SHANGHAI = ZoneInfo("Asia/Shanghai")


def add_daily_job(
    scheduler: Any,
    job_id: str,
    func: Callable[[], Any],
    *,
    hour: int = 4,
    minute: int = 0,
) -> Any:
    """Register one daily cron job in ``Asia/Shanghai`` and return the created job.

    ``replace_existing``, ``coalesce``, a single instance and a one-hour misfire
    grace window are fixed so every maintenance job behaves identically.
    """
    return scheduler.add_job(
        func,
        "cron",
        id=job_id,
        hour=hour,
        minute=minute,
        timezone=SHANGHAI,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
