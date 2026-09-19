# ruff: noqa: S101

import datetime as dt

import pytest

from plugins.news.config import NewsConfig
from plugins.news.schemas import (
    Article,
    Edition,
    NewsPayload,
    Story,
    Support,
    canonical_url,
    eligible,
    validate_evidence,
)


def article(identifier="a", hours=1):
    now = dt.datetime(2026, 9, 19, 1, tzinfo=dt.UTC)
    return Article(
        article_id=identifier,
        url=f"https://example.com/{identifier}?utm_source=x",
        title=f"title {identifier}",
        text="x" * 50 + f" exact supported passage {identifier}",
        source="example.com",
        provider="test",
        published_at=now - dt.timedelta(hours=hours),
        fetched_at=now,
        fingerprint=identifier,
    )


def test_url_drops_tracking_and_rejects_private():
    assert canonical_url("https://example.com/a?utm_source=x&id=1") == "https://example.com/a?id=1"
    with pytest.raises(ValueError):
        canonical_url("http://127.0.0.1/a")


def test_unknown_publication_is_not_eligible():
    edition = Edition("general", dt.datetime(2026, 9, 19, 1, tzinfo=dt.UTC))
    item = article().model_copy(update={"published_at": None})
    assert eligible([item], edition) == []


def test_evidence_quote_must_exist():
    item = article()
    payload = NewsPayload(
        top_stories=[
            Story(
                title="t",
                category="国际",
                summary="s",
                evidence=[
                    Support(
                        article_id="a",
                        quote="fabricated evidence passage",
                    )
                ],
            )
        ],
        worth_reading=[],
    )
    with pytest.raises(ValueError):
        validate_evidence(payload, [item])


def test_config_defaults_are_coherent():
    assert NewsConfig().min_stories <= NewsConfig().target_stories
