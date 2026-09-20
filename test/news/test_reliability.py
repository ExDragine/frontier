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


def service(repo, *, drafts, verification=None, attempts=3):
    sources = SimpleNamespace(collect=AsyncMock(return_value=[article(str(i)) for i in range(2)]))
    editor = SimpleNamespace(
        edit=AsyncMock(side_effect=drafts),
        verify=AsyncMock(side_effect=verification or (lambda draft, _articles: draft)),
    )
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
async def test_rejected_draft_cleared_even_when_budget_exhausted(repo, edition):
    svc = service(repo, drafts=[payload(1), payload(1)], attempts=2)
    with pytest.raises(InsufficientEvidence):
        await svc.generate_report(edition)
    assert svc.editor.edit.await_count == 2
    assert (await repo.get(edition.report_id))["payload"] is None
    svc.editor.edit.side_effect = [payload(2)]
    assert (await svc.generate_report(edition))["status"] == "ready"
    assert svc.sources.collect.await_count == 1


@pytest.mark.asyncio
async def test_verification_network_failure_preserves_draft(repo, edition):
    svc = service(repo, drafts=[payload(2)], verification=[ConnectionError(), payload(2)])
    with pytest.raises(ConnectionError):
        await svc.generate_report(edition)
    assert (await repo.get(edition.report_id))["payload"] is not None
    assert (await svc.generate_report(edition))["status"] == "ready"
    assert svc.editor.edit.await_count == 1


@pytest.mark.asyncio
async def test_checkpoint_preserves_long_generation_lease(repo, edition):
    token = await repo.claim(edition, ttl=930)
    before = await repo.get(edition.report_id)
    await repo.checkpoint(edition.report_id, token, "edit")
    assert (await repo.get(edition.report_id))["lease_until"] == before["lease_until"]


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

    send = AsyncMock(return_value=SimpleNamespace(message_id="123"))
    message = SimpleNamespace(send=send)
    monkeypatch.setattr(delivery, "UniMessage", SimpleNamespace(text=lambda _: message))
    return send


def report():
    return {"id": "r", "scheduled_at": time.time(), "payload": payload().model_dump()}


@pytest.mark.asyncio
async def test_send_confirmation_failure_cannot_resend(repo, sender, monkeypatch):
    from plugins.news.delivery import deliver

    original = repo.finish_delivery

    async def fail_confirmation(*args, **kwargs):
        if args[3] == "sent":
            raise OSError("database unavailable")
        return await original(*args, **kwargs)

    monkeypatch.setattr(repo, "finish_delivery", fail_confirmation)
    cfg = NewsConfig()
    assert await deliver(repo, report(), [1], cfg) == [1]
    assert (await repo.deliveries("r"))[0]["state"] == "sending"
    assert await repo.retry_failed("r", ["1"], time.time() + 60) == []
    await repo._run(lambda db: db.execute("UPDATE news_deliveries SET lease_until=0"))
    assert await deliver(repo, report(), [1], cfg) == []
    assert (await repo.deliveries("r"))[0]["state"] == "unknown"
    assert sender.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["absent", "sent", "unknown", "failed"])
async def test_retry_only_existing_failed_target(repo, sender, state):
    from plugins.news.delivery import deliver

    if state != "absent":
        await repo.stage_deliveries("r", ["1"], time.time() + 60)
        token = await repo.claim_delivery("r", "1")
        await repo.finish_delivery("r", "1", token, state)
    targets = await repo.retry_failed("r", ["1"], time.time() + 60)
    sent = await deliver(repo, report(), targets, NewsConfig(), stage=False)
    assert sent == ([1] if state == "failed" else [])
    assert sender.await_count == (1 if state == "failed" else 0)
    if state == "absent":
        assert await repo.deliveries("r") == []


@pytest.mark.asyncio
@pytest.mark.parametrize("exception", [TimeoutError, asyncio.CancelledError])
async def test_ambiguous_send_never_becomes_retryable(repo, sender, exception):
    from plugins.news.delivery import deliver

    sender.side_effect = exception
    if exception is asyncio.CancelledError:
        with pytest.raises(asyncio.CancelledError):
            await deliver(repo, report(), [1], NewsConfig())
    else:
        assert await deliver(repo, report(), [1], NewsConfig()) == []
    assert (await repo.deliveries("r"))[0]["state"] in {"unknown", "sending"}
    assert await repo.retry_failed("r", ["1"], time.time() + 60) == []


@pytest.mark.asyncio
async def test_retention_protects_active_generation_and_delivery(repo, edition):
    cutoff = time.time() - 40 * 86400
    token = await repo.claim(edition)
    await repo._run(lambda db: db.execute("UPDATE news_reports SET updated_at=?", (cutoff,)))
    assert await repo.prune(30) == 0  # Active generation.
    await repo.fail(edition.report_id, token, "failed")
    await repo.stage_deliveries(edition.report_id, ["1"], time.time() + 60)
    await repo.claim_delivery(edition.report_id, "1")
    await repo._run(lambda db: db.execute("UPDATE news_reports SET updated_at=?", (cutoff,)))
    await repo._run(lambda db: db.execute("UPDATE news_deliveries SET updated_at=?", (cutoff,)))
    assert await repo.prune(30) == 0  # Active delivery.
    await repo._run(lambda db: db.execute("UPDATE news_deliveries SET lease_until=0"))
    assert await repo.prune(30) == 1
    assert await repo.get(edition.report_id) is None
    assert await repo.deliveries(edition.report_id) == []


def test_rendering_uses_archived_edition_time():
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
    svc.sources.errors = ["exa:missing_key"]
    with pytest.raises(InsufficientEvidence, match=r"eligible=0/2.*undated=8.*exa:missing_key"):
        await svc.generate_report(edition)
    svc.editor.edit.assert_not_awaited()
    assert (await repo.get(edition.report_id))["status"] == "failed"
