"""Bounded news inputs, immutable edition identity, and evidence contracts."""

import datetime as dt
import hashlib
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        raise ValueError("news timestamps must include a timezone")
    return value.astimezone(dt.UTC)


def canonical_url(value: str) -> str:
    if any(ord(char) < 32 for char in value) or len(value) > 2048:
        raise ValueError("invalid article URL")
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"https", "http"} or not host or parsed.username or parsed.password:
        raise ValueError("article URL must be a public HTTP(S) URL")
    if host == "localhost" or host.endswith((".local", ".internal")):
        raise ValueError("private article URL")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("private article URL")
    # Preserve meaningful query parameters: dropping every query can merge different articles.
    query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}]
    port = parsed.port  # Validate malformed ports too.
    authority = f"[{host}]" if ":" in host else host
    if port is not None and port != (443 if parsed.scheme == "https" else 80):
        authority += f":{port}"
    return urlunsplit((parsed.scheme, authority, parsed.path or "/", urlencode(sorted(query)), ""))


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


@dataclass(frozen=True)
class Edition:
    board: str
    scheduled_at: dt.datetime
    window_hours: int = 24
    namespace: str = "published"

    def __post_init__(self):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", self.board):
            raise ValueError("invalid board")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", self.namespace):
            raise ValueError("invalid namespace")
        if not 1 <= self.window_hours <= 72:
            raise ValueError("invalid news window")
        object.__setattr__(self, "scheduled_at", utc(self.scheduled_at))

    @property
    def report_id(self) -> str:
        value = f"{self.namespace}:{self.board}:{self.scheduled_at.isoformat()}"
        return hashlib.sha256(value.encode()).hexdigest()[:32]

    @property
    def start(self) -> dt.datetime:
        return self.scheduled_at - dt.timedelta(hours=self.window_hours)


class Article(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    article_id: str
    url: str
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=40, max_length=6000)
    source: str
    provider: str
    published_at: dt.datetime | None = None
    fetched_at: dt.datetime
    fingerprint: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        return canonical_url(value)

    @field_validator("published_at", "fetched_at")
    @classmethod
    def validate_time(cls, value):
        return utc(value) if value is not None else None


class Support(BaseModel):
    model_config = ConfigDict(extra="forbid")
    article_id: str = Field(min_length=1, max_length=64)
    quote: str = Field(min_length=15, max_length=700, description="Verbatim passage from the supplied evidence text")


class Story(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=12)
    summary: str = Field(min_length=1, max_length=160)
    impact: str = Field(default="", max_length=80)
    evidence: list[Support] = Field(min_length=1, max_length=4)


class NewsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_stories: list[Story] = Field(max_length=6)
    worth_reading: list[Story] = Field(max_length=12)

    @model_validator(mode="after")
    def nonempty(self):
        if not self.top_stories and not self.worth_reading:
            raise ValueError("empty news payload")
        return self

    @property
    def stories(self) -> list[Story]:
        return self.top_stories + self.worth_reading


class Verification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    supported_indices: list[int] = Field(max_length=18)


def validate_evidence(payload: NewsPayload, articles: list[Article]) -> NewsPayload:
    """Check references and exact quotes; this is NOT a proof of factual truth."""
    known = {item.article_id: item for item in articles}
    used: set[str] = set()
    titles: set[str] = set()
    for story in payload.stories:
        title = compact(story.title).casefold()
        if title in titles:
            raise ValueError("duplicate story title")
        titles.add(title)
        ids = {support.article_id for support in story.evidence}
        if used & ids:
            raise ValueError("the same article cannot fill multiple news slots")
        used.update(ids)
        for support in story.evidence:
            article = known.get(support.article_id)
            if article is None or compact(support.quote) not in compact(article.text):
                raise ValueError("missing or fabricated evidence quote")
    return payload


def eligible(articles: list[Article], edition: Edition, seen: set[str] | None = None) -> list[Article]:
    fingerprints = set(seen or ())
    urls: set[str] = set()
    result = []
    for article in articles:
        # fetched_at is never substituted for an unknown publication timestamp.
        if article.published_at is None or not edition.start <= article.published_at <= edition.scheduled_at:
            continue
        if article.fingerprint in fingerprints or article.url in urls:
            continue
        fingerprints.add(article.fingerprint)
        urls.add(article.url)
        result.append(article)
    return result
