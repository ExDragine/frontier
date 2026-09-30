# ruff: noqa: S101

import asyncio
import datetime as dt
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from plugins.news.config import NewsConfig
from plugins.news.repository import NewsRepository
from plugins.news.schemas import Edition, NewsPayload, Story, Support
from plugins.news.service import InsufficientEvidence, NewsService
from plugins.news.sources import SourcePool
from test.news.test_core import article


@pytest_asyncio.fixture
async def repo(tmp_path):
    repository = NewsRepository(tmp_path / "news.db")
    await repository.initialize()
    return repository


@pytest.fixture
def edition():
    return Edition("general", dt.datetime(2026, 9, 19, 1, tzinfo=dt.UTC))


def payload(count=2):
    return NewsPayload(top_stories=[
        Story(title=f"story {i}", category="国际", summary="summary", evidence=[
            Support(article_id=str(i), quote=f"exact supported passage {i}"),
        ]) for i in range(count)
    ], worth_reading=[])


def service(repo, *, drafts, attempts=3):
    sources = SimpleNamespace(collect=AsyncMock(return_value=[article(str(i)) for i in range(2)]))
    editor = SimpleNamespace(edit=AsyncMock(side_effect=drafts))
    return NewsService(repo, sources, editor, NewsConfig(
        min_stories=2, target_stories=2, max_generation_attempts=attempts,
    ))


@pytest.mark.asyncio
async def test_rejected_draft_is_reedited_and_ready_report_reused(repo, edition):
    svc = service(repo, drafts=[payload(1), payload(2)])
    report = await svc.generate_report(edition)
    assert report["status"] == "ready"
    assert svc.editor.edit.await_count == 2
    assert (await svc.generate_report(edition))["payload"] == report["payload"]
    assert svc.editor.edit.await_count == 2


@pytest.mark.asyncio
async def test_exhausted_attempts_fail_and_next_run_recollects(repo, edition):
    svc = service(repo, drafts=[payload(1), payload(1)], attempts=2)
    with pytest.raises(InsufficientEvidence):
        await svc.generate_report(edition)
    assert svc.editor.edit.await_count == 2
    assert (await repo.get(edition.report_id))["status"] == "failed"
    svc.editor.edit.side_effect = [payload(2)]
    assert (await svc.generate_report(edition))["status"] == "ready"
    assert svc.sources.collect.await_count == 2


@pytest.mark.asyncio
async def test_edit_timeout_fails_and_next_run_recollects(repo, edition):
    svc = service(repo, drafts=[TimeoutError(), payload(2)])
    with pytest.raises(TimeoutError):
        await svc.generate_report(edition)
    row = await repo.get(edition.report_id)
    assert row["status"] == "failed"
    assert row["payload"] is None
    assert (await svc.generate_report(edition))["status"] == "ready"
    assert svc.sources.collect.await_count == 2


@pytest.mark.asyncio
async def test_complete_requires_live_generation_lease(repo, edition):
    token = await repo.claim(edition)
    await repo._run(lambda db: db.execute("UPDATE news_reports SET lease_until=0"))
    with pytest.raises(RuntimeError, match="lease"):
        await repo.complete(edition.report_id, token, "ready", [], payload(2))


@pytest.mark.asyncio
async def test_retention_protects_active_generation_and_pending_delivery(repo, edition):
    cutoff = time.time() - 40 * 86400
    token = await repo.claim(edition)
    await repo._run(lambda db: db.execute("UPDATE news_reports SET updated_at=?", (cutoff,)))
    assert await repo.prune(30) == 0  # Active generation lease.
    await repo.fail(edition.report_id, token, "failed")
    await repo.stage_deliveries(edition.report_id, ["1"])
    await repo._run(lambda db: db.execute("UPDATE news_reports SET updated_at=?", (cutoff,)))
    assert await repo.prune(30) == 0  # Pending delivery.
    await repo.mark_delivery(edition.report_id, "1", "sent")
    await repo._run(lambda db: db.execute("UPDATE news_reports SET updated_at=?", (cutoff,)))
    await repo._run(lambda db: db.execute("UPDATE news_deliveries SET updated_at=?", (cutoff,)))
    assert await repo.prune(30) == 1
    assert await repo.get(edition.report_id) is None
    assert await repo.deliveries(edition.report_id) == []


@pytest.mark.asyncio
async def test_insufficient_unique_evidence_uses_fallback(edition):
    first = SimpleNamespace(name="first", search=AsyncMock(return_value=[article("0")]))
    second = SimpleNamespace(name="second", search=AsyncMock(return_value=[article("1")]))
    cfg = NewsConfig(min_stories=2, target_stories=2, queries=("a", "b"))
    pool = SourcePool([first, second], cfg)
    assert len(await pool.collect(edition, set())) == 2
    assert second.search.await_count == 2
    first.search.return_value = [article("0"), article("1")]
    second.search.reset_mock()
    assert len(await pool.collect(edition, set())) == 2
    second.search.assert_not_awaited()


@pytest.fixture
def sender(monkeypatch):
    from plugins.news import delivery

    send = AsyncMock()
    message = SimpleNamespace(send=send)
    monkeypatch.setattr(delivery, "UniMessage", SimpleNamespace(text=lambda _: message))
    return send


def report():
    return {"id": "r", "scheduled_at": time.time(), "payload": payload().model_dump()}


@pytest.mark.asyncio
async def test_deliver_marks_sent_and_never_resends(repo, sender):
    from plugins.news.delivery import deliver

    assert await deliver(repo, report(), [1, 2], NewsConfig()) == [1, 2]
    rows = {row["target"]: (row["state"], row["attempts"]) for row in await repo.deliveries("r")}
    assert rows == {"1": ("sent", 1), "2": ("sent", 1)}
    assert await deliver(repo, report(), [1, 2], NewsConfig()) == []
    assert sender.await_count == 2


@pytest.mark.asyncio
async def test_deliver_timeout_is_failed_and_retryable(repo, sender):
    from plugins.news.delivery import deliver

    sender.side_effect = TimeoutError()
    assert await deliver(repo, report(), [1], NewsConfig()) == []
    row = (await repo.deliveries("r"))[0]
    assert row["state"] == "failed" and row["error"] == "TimeoutError"
    sender.side_effect = None
    assert await repo.retry_failed("r", ["1"]) == ["1"]
    assert await deliver(repo, report(), ["1"], NewsConfig(), stage=False) == [1]
    assert (await repo.deliveries("r"))[0]["state"] == "sent"


@pytest.mark.asyncio
async def test_cancelled_send_stays_pending(repo, sender):
    from plugins.news.delivery import deliver

    sender.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await deliver(repo, report(), [1], NewsConfig())
    assert (await repo.deliveries("r"))[0]["state"] == "pending"


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["absent", "sent", "pending", "failed"])
async def test_retry_only_existing_failed_target(repo, sender, state):
    from plugins.news.delivery import deliver

    if state != "absent":
        await repo.stage_deliveries("r", ["1"])
        if state != "pending":
            await repo.mark_delivery("r", "1", state)
    targets = await repo.retry_failed("r", ["1"])
    sent = await deliver(repo, report(), targets, NewsConfig(), stage=False)
    assert sent == ([1] if state == "failed" else [])
    assert sender.await_count == (1 if state == "failed" else 0)
    if state == "absent":
        assert await repo.deliveries("r") == []


@pytest.mark.asyncio
async def test_rendering_uses_archived_edition_time():
    from plugins.news.rendering import render_html, render_text

    data = report() | {
        "scheduled_at": dt.datetime(2026, 9, 19, 1, tzinfo=dt.UTC).timestamp(),
        "evidence": [article(str(i)).model_dump() for i in range(2)],
    }
    for rendered in (render_html(data), render_text(data)):
        assert "2026-09-19" in rendered
        assert "09:00" in rendered


@pytest.mark.asyncio
async def test_insufficient_collection_reports_safe_diagnostics_without_editing(repo, edition):
    svc = service(repo, drafts=[payload(2)])
    svc.sources.collect.return_value = []
    svc.sources.stats = {"received": 8, "undated": 8, "outside_window": 0}
    svc.sources.errors = ["exa:mcp_tool_missing"]
    with pytest.raises(InsufficientEvidence, match=r"eligible=0/2.*undated=8.*exa:mcp_tool_missing"):
        await svc.generate_report(edition)
    svc.editor.edit.assert_not_awaited()
    assert (await repo.get(edition.report_id))["status"] == "failed"


@pytest.mark.asyncio
async def test_editor_receives_configured_story_target(monkeypatch, edition):
    import json

    from plugins.news.editor import NewsEditor

    editor = NewsEditor(NewsConfig(target_stories=14))
    call = AsyncMock(return_value=payload(2))
    monkeypatch.setattr(editor, "call", call)
    await editor.edit(edition, [article(str(i)) for i in range(2)])
    data = json.loads(call.call_args.args[2])
    assert data["target_stories"] == 14
    assert len(data["articles"]) == 2
