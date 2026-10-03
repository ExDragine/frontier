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
    await repository.stage_deliveries("r", ["1"])
    await repository.mark_delivery("r", "1", "failed", error="x")
    assert (await repository.deliveries("r"))[0]["state"] == "failed"
    assert await repository.retry_failed("r", ["1"]) == ["1"]
    assert (await repository.deliveries("r"))[0]["state"] == "pending"


@pytest.mark.asyncio
async def test_only_failed_delivery_is_requeued(tmp_path):
    repository = NewsRepository(tmp_path / "news.db")
    await repository.initialize()
    now = time.time()
    await seed_report(repository, now)
    await repository.stage_deliveries("r", ["1", "2"])
    await repository.mark_delivery("r", "1", "sent")
    assert await repository.retry_failed("r", ["1", "2", "3"]) == []
    rows = {row["target"]: row["state"] for row in await repository.deliveries("r")}
    assert rows == {"1": "sent", "2": "pending"}
