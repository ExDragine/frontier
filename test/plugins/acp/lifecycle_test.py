# ruff: noqa: S101

import pytest

from plugins.acp import lifecycle
from utils.timeutil import SHANGHAI


@pytest.mark.asyncio
async def test_acp_owns_cache_schedule_and_shutdown(monkeypatch):
    calls = []

    class Service:
        async def cleanup_cache(self):
            calls.append("cleanup")
            return 1

        async def close(self):
            calls.append("close")

    class Scheduler:
        def add_job(self, func, trigger, **kwargs):
            calls.append((func, trigger, kwargs))

    monkeypatch.setattr(lifecycle, "acp_service", Service())
    monkeypatch.setattr(lifecycle, "scheduler", Scheduler())
    await lifecycle.startup_acp()
    func, trigger, options = calls.pop()
    assert func is lifecycle.run_daily_cache_cleanup
    assert trigger == "cron"
    assert options["id"] == lifecycle.CACHE_CLEANUP_JOB_ID
    assert (options["hour"], options["minute"]) == (4, 0)
    assert options["timezone"] is SHANGHAI
    assert options["replace_existing"] is True
    assert options["coalesce"] is True
    assert options["max_instances"] == 1
    assert options["misfire_grace_time"] == 3600
    await func()
    await lifecycle.shutdown_acp()
    assert calls == ["cleanup", "close"]
