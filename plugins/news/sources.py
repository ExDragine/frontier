"""Direct search-provider collection with bounded fallback."""

import asyncio
import datetime as dt
import hashlib
import os
from urllib.parse import urlsplit

from .schemas import Article, canonical_url, compact, eligible


class SourceError(RuntimeError):
    def __init__(self, code, retryable=False):
        super().__init__(code)
        self.retryable = retryable


def publication_time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(dt.UTC) if parsed.tzinfo else None


class SearchSource:
    endpoints = {
        "exa": "https://api.exa.ai/search",
        "tavily": "https://api.tavily.com/search",
    }

    def __init__(self, name, key, client, cfg):
        self.name = name
        self.key = key
        self.client = client
        self.cfg = cfg

    async def search(self, query, edition):
        if not self.key:
            raise SourceError("missing_key")
        if self.name == "exa":
            headers = {"x-api-key": self.key}
            body = {
                "query": query,
                "type": "auto",
                "numResults": self.cfg.source_results,
                "startPublishedDate": edition.start.isoformat(),
                "endPublishedDate": edition.scheduled_at.isoformat(),
                "contents": {"text": True},
            }
        else:
            headers = {"Authorization": f"Bearer {self.key}"}
            body = {
                "query": query,
                "topic": "news",
                "max_results": self.cfg.source_results,
                "include_raw_content": True,
                "start_date": edition.start.date().isoformat(),
                "end_date": edition.scheduled_at.date().isoformat(),
            }
        async with asyncio.timeout(self.cfg.source_timeout):
            response = await self.client.post(
                self.endpoints[self.name],
                headers=headers,
                json=body,
                timeout=self.cfg.source_timeout,
            )
        if response.status_code >= 400:
            retryable = response.status_code == 429 or response.status_code >= 500
            raise SourceError(f"http_{response.status_code}", retryable)
        data = response.json()
        results = data.get("results", []) if isinstance(data, dict) else []
        output = []
        now = dt.datetime.now(dt.UTC)
        for item in results[: self.cfg.source_results]:
            try:
                url = canonical_url(str(item.get("url", "")))
                title = compact(str(item.get("title", "")))[:300]
                text = compact(
                    str(
                        item.get("text")
                        or item.get("raw_content")
                        or item.get("content")
                        or ""
                    )
                )[:6000]
                fingerprint = hashlib.sha256(
                    (title + "\n" + text).encode()
                ).hexdigest()
                article_id = hashlib.sha256(
                    (url + fingerprint).encode()
                ).hexdigest()[:32]
                output.append(
                    Article(
                        article_id=article_id,
                        url=url,
                        title=title,
                        text=text,
                        source=urlsplit(url).hostname or self.name,
                        provider=self.name,
                        published_at=publication_time(
                            item.get("publishedDate") or item.get("published_date")
                        ),
                        fetched_at=now,
                        fingerprint=fingerprint,
                    )
                )
            except (TypeError, ValueError):
                continue
        return output


class SourcePool:
    def __init__(self, sources, cfg):
        self.sources = sources
        self.cfg = cfg
        self.errors = []

    async def collect(self, edition, seen):
        async def collect_query(query):
            for source in self.sources:
                for attempt in range(2):
                    try:
                        items = eligible(
                            await source.search(query, edition),
                            edition,
                            seen,
                        )
                        if items:
                            return items
                    except SourceError as exc:
                        self.errors.append(f"{source.name}:{exc}")
                        if not exc.retryable:
                            break
                    except Exception as exc:
                        self.errors.append(f"{source.name}:{type(exc).__name__}")
                    if attempt == 0:
                        await asyncio.sleep(1)
            return []

        batches = await asyncio.gather(
            *(collect_query(query) for query in self.cfg.queries)
        )
        flattened = [item for batch in batches for item in batch]
        return eligible(flattened, edition, seen)[:40]


def configured_sources(client, cfg):
    sources = [
        SearchSource(
            name,
            os.getenv(f"{name.upper()}_API_KEY", ""),
            client,
            cfg,
        )
        for name in cfg.sources
    ]
    return SourcePool(sources, cfg)
