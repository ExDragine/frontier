# ruff: noqa: S101

import time

import pytest

from plugins.news.repository import NewsRepository


async def seed_report(repository, now):
    await repository._run(
        lambda database: database.execute(
            "INSERT INTO news_reports"
            "(id,board,namespace,scheduled_at,status,stage,evidence,updated_at) "
            "VALUES('r','g','published',?,'ready','complete','[]',?)",
            (now, now),
        )
    )


@pytest.mark.asyncio
async def test_failed_delivery_can_be_explicitly_requeued(tmp_path):
    repository = NewsRepository(tmp_path / "news.db")
    await repository.initialize()
    now = time.time()
    await seed_report(repository, now)
    await repository.stage_deliveries("r", ["1"], now + 60)
    token = await repository.claim_delivery("r", "1")
    assert token
    await repository.finish_delivery("r", "1", token, "failed", error="x")
    await repository.retry_failed("r", ["1"], now + 60)
    assert (await repository.deliveries("r"))[0]["state"] == "pending"


@pytest.mark.asyncio
async def test_expired_inflight_is_unknown_not_retried(tmp_path):
    repository = NewsRepository(tmp_path / "news.db")
    await repository.initialize()
    now = time.time()
    await seed_report(repository, now)
    await repository.stage_deliveries("r", ["1"], now + 60)
    token = await repository.claim_delivery("r", "1", ttl=1)
    assert token
    await repository._run(
        lambda database: database.execute(
            "UPDATE news_deliveries SET lease_until=0 WHERE report_id='r'"
        )
    )
    assert await repository.claim_delivery("r", "1") is None
    assert (await repository.deliveries("r"))[0]["state"] == "unknown"
