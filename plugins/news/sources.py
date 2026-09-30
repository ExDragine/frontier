"""Direct search-provider collection with bounded fallback."""

import asyncio
import datetime as dt
import hashlib
import json
import os
import re
from collections import Counter
from email.utils import parsedate_to_datetime
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
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    return parsed.astimezone(dt.UTC) if parsed.tzinfo else None


def _mcp_value(value):
    """Unwrap the common LangChain/FastMCP tool result containers."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        artifact = value.get("artifact")
        if artifact is not None:
            return _mcp_value(artifact)
        structured = value.get("structured_content")
        if structured is not None:
            return _mcp_value(structured)
        return {key: _mcp_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mcp_value(item) for item in value]
    artifact = getattr(value, "artifact", None)
    if artifact is not None:
        return _mcp_value(artifact)
    content = getattr(value, "content", None)
    if content is not None:
        return _mcp_value(content)
    if hasattr(value, "model_dump"):
        return _mcp_value(value.model_dump())
    return str(value)


def _mcp_text_items(value):
    pattern = re.compile(
        r"(?ms)(?:^|\n)(?:#+\s*)?\[([^\]]+)\]\((https?://[^)]+)\)(.*?)(?=\n(?:#+\s*)?\[|\Z)"
    )
    linked = pattern.findall(value)
    if linked:
        return [
            {"title": title, "url": url, "text": body, "raw": body}
            for title, url, body in linked
        ]

    # Some MCP adapters flatten Exa's result blocks into labelled text rather
    # than preserving structured content. Keep the URL and the following
    # metadata/body together so publication dates remain recoverable.
    labelled = re.compile(
        r"(?ms)(?:^|\n)(?:Title:\s*)?(.+?)\n(?:URL|Link):\s*(https?://\S+)(.*?)(?=\n(?:Title:|URL:|Link:)|\Z)"
    )
    return [
        {"title": title.strip(), "url": url.rstrip("),."), "text": body, "raw": body}
        for title, url, body in labelled.findall(value)
    ]


def _mcp_result_items(value):  # noqa: C901
    """Extract article-like result dictionaries from an MCP response."""
    value = _mcp_value(value)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError):
            decoded = None
        if decoded is not None:
            return _mcp_result_items(decoded)
        # Exa's MCP server may return markdown when structured content is not
        # exposed by the adapter. Keep each linked result as an evidence item.
        return _mcp_text_items(value)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_mcp_result_items(item))
        return items
    if not isinstance(value, dict):
        return []
    for key in ("results", "items", "data", "articles"):
        nested = value.get(key)
        if isinstance(nested, (list, dict, str)):
            items = _mcp_result_items(nested)
            if items:
                return items
    if value.get("type") == "text" and isinstance(value.get("text"), str):
        return _mcp_result_items(value["text"])
    if value.get("url") or value.get("link"):
        return [value]
    return []


def _mcp_tool_arguments(tool, query, edition, source_results):
    """Build arguments compatible with both Exa MCP schema spellings."""
    fields = getattr(getattr(tool, "args_schema", None), "model_fields", {})
    names = set(fields) if fields else {"query"}
    args = {"query": query}

    def add(value, *candidates):
        for name in candidates:
            if name in names:
                args[name] = value
                return

    add(source_results, "numResults", "num_results", "max_results")
    add("auto", "type")
    add("news", "category", "topic")
    add(edition.start.isoformat(), "startPublishedDate", "start_published_date", "start_date")
    add(edition.scheduled_at.isoformat(), "endPublishedDate", "end_published_date", "end_date")
    add({"text": True}, "contents")
    return args


def _mcp_articles(value, *, provider="exa"):
    """Convert MCP search results to the bounded Article evidence contract."""
    output = []
    now = dt.datetime.now(dt.UTC)
    for item in _mcp_result_items(value):
        try:
            url = canonical_url(str(item.get("url") or item.get("link") or ""))
            title = compact(str(item.get("title") or item.get("name") or ""))[:300]
            highlights = item.get("highlights")
            if isinstance(highlights, list):
                highlights = " ".join(str(part) for part in highlights)
            text = compact(
                str(
                    item.get("text")
                    or item.get("content")
                    or item.get("raw_content")
                    or item.get("snippet")
                    or highlights
                    or item.get("raw")
                    or ""
                )
            )[:6000]
            if len(title) < 1 or len(text) < 40:
                continue
            fingerprint = hashlib.sha256((title + "\n" + text).encode()).hexdigest()
            published = publication_time(
                item.get("publishedDate")
                or item.get("published_date")
                or item.get("published_at")
                or item.get("published")
                or item.get("date")
            )
            if published is None:
                # Text-only MCP adapters can still expose the publication date
                # in a labelled block. Never substitute fetched_at for it.
                dates = re.findall(
                    r"\b20\d{2}-\d{2}-\d{2}(?:[T ][0-9:.+\-Z]+)?\b"
                    r"|\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+\d{1,2}\s+"
                    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}[^\n]*",
                    text,
                    flags=re.IGNORECASE,
                )
                for date_value in dates:
                    published = publication_time(date_value.strip())
                    if published is not None:
                        break
            output.append(
                Article(
                    article_id=hashlib.sha256((url + fingerprint).encode()).hexdigest()[:32],
                    url=url,
                    title=title,
                    text=text,
                    source=urlsplit(url).hostname or provider,
                    provider=provider,
                    published_at=published,
                    fetched_at=now,
                    fingerprint=fingerprint,
                )
            )
        except (TypeError, ValueError):
            continue
    return output


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
        if not isinstance(results, list):
            raise SourceError("invalid_results")
        output = []
        now = dt.datetime.now(dt.UTC)
        for item in results[: self.cfg.source_results]:
            if not isinstance(item, dict):
                continue
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


class ExaMcpSource:
    """Use the configured public Exa MCP endpoint when no REST key is set."""

    name = "exa"

    def __init__(self, cfg):
        self.cfg = cfg
        self._tool = None

    async def _get_tool(self):
        if self._tool is not None:
            return self._tool
        try:
            from tools.mcp_client import mcp_get_tools_async

            tools = await mcp_get_tools_async()
        except Exception as exc:
            raise SourceError("mcp_unavailable", retryable=True) from exc
        self._tool = next(
            (
                tool
                for tool in tools
                if getattr(tool, "name", "") == "web_search_advanced_exa"
            ),
            None,
        ) or next(
            (tool for tool in tools if getattr(tool, "name", "") == "web_search_exa"),
            None,
        )
        if self._tool is None:
            raise SourceError("mcp_tool_missing")
        return self._tool

    async def search(self, query, edition):
        tool = await self._get_tool()
        args = _mcp_tool_arguments(tool, query, edition, self.cfg.source_results)
        try:
            async with asyncio.timeout(self.cfg.source_timeout):
                result = await tool.ainvoke(args)
        except SourceError:
            raise
        except Exception as exc:
            raise SourceError(f"mcp_{type(exc).__name__}", retryable=True) from exc
        return _mcp_articles(result)


class SourcePool:
    def __init__(self, sources, cfg):
        self.sources = sources
        self.cfg = cfg
        self.errors = []
        self.stats = Counter()

    async def collect(self, edition, seen):
        self.errors = []
        self.stats = Counter()

        async def collect_query(source, query):
            for attempt in range(2):
                try:
                    articles = await source.search(query, edition)
                    self.stats["received"] += len(articles)
                    self.stats["undated"] += sum(item.published_at is None for item in articles)
                    self.stats["outside_window"] += sum(
                        item.published_at is not None
                        and not edition.start <= item.published_at <= edition.scheduled_at
                        for item in articles
                    )
                    return eligible(articles, edition, seen)
                except SourceError as exc:
                    self.errors.append(f"{source.name}:{exc}")
                    if not exc.retryable:
                        break
                except Exception as exc:
                    self.errors.append(f"{source.name}:{type(exc).__name__}")
                if attempt == 0:
                    await asyncio.sleep(1)
            return []

        collected = []
        for source in self.sources:
            batches = await asyncio.gather(
                *(collect_query(source, query) for query in self.cfg.queries)
            )
            collected = eligible(collected + [item for batch in batches for item in batch], edition, seen)
            if len(collected) >= self.cfg.target_stories:
                break
        self.stats["eligible"] = len(collected)
        return collected[:40]


def configured_sources(client, cfg):
    sources = []
    for name in cfg.sources:
        key = os.getenv(f"{name.upper()}_API_KEY", "")
        if name == "exa" and not key:
            sources.append(ExaMcpSource(cfg))
        else:
            sources.append(SearchSource(name, key, client, cfg))
    return SourcePool(sources, cfg)
