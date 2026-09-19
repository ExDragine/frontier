# ruff: noqa: S101
import datetime as dt
import pytest
from plugins.news.config import NewsConfig
from plugins.news.schemas import Article,Edition,NewsPayload,Story,Support,canonical_url,eligible,validate_evidence

def article(i="a",hours=1):
 e=dt.datetime(2026,9,19,1,tzinfo=dt.UTC)
 return Article(article_id=i,url=f"https://example.com/{i}?utm_source=x",title="title "+i,text="x"*50+" exact supported passage "+i,source="example.com",provider="test",published_at=e-dt.timedelta(hours=hours),fetched_at=e,fingerprint=i)

def test_url_drops_tracking_and_rejects_private():
 assert canonical_url("https://example.com/a?utm_source=x&id=1")=="https://example.com/a?id=1"
 with pytest.raises(ValueError):canonical_url("http://127.0.0.1/a")

def test_unknown_publication_is_not_eligible():
 e=Edition("general",dt.datetime(2026,9,19,1,tzinfo=dt.UTC))
 a=article();a=a.model_copy(update={"published_at":None})
 assert eligible([a],e)==[]

def test_evidence_quote_must_exist():
 a=article(); p=NewsPayload(top_stories=[Story(title="t",category="国际",summary="s",evidence=[Support(article_id="a",quote="fabricated evidence passage")])],worth_reading=[])
 with pytest.raises(ValueError):validate_evidence(p,[a])

def test_config_defaults_are_coherent():
 assert NewsConfig().min_stories<=NewsConfig().target_stories
