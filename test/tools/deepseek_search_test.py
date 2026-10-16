# ruff: noqa: S101, S105, S106

import asyncio
import json
from types import SimpleNamespace

import pytest

from utils import deepseek_web as web
from utils.agent_context import FrontierRuntimeContext


@pytest.fixture(autouse=True)
def active_config(monkeypatch):
    from utils.configs import EnvConfig

    monkeypatch.setattr(web, "EnvConfig", EnvConfig)


@pytest.fixture
def configured(monkeypatch):
    web.EnvConfig.reload({"config_version": 2, "providers": {"deepseek_responses": {"api_key": "sk-search-test"}}})

    async def no_wait(operation):
        pass

    monkeypatch.setattr(web, "_wait_for_slot", no_wait)


def result(index=1, **updates):
    return {
        "title": f"页面 {index}",
        "url": f"https://example.com/{index}",
        "summary": f"摘要 {index}",
        "snippet": "短摘要",
        "content": "",
        "date": None,
        "site_name": "Example",
        "site_icon": "https://example.com/icon.png",
        "rerank_score": 2.4,
        "authority": 3,
        **updates,
    }


class Client:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        value = self.responses.pop(0)
        if isinstance(value, BaseException):
            raise value
        status, data = value
        return SimpleNamespace(status_code=status, json=lambda: data)


def install(monkeypatch, *responses):
    client = Client(*responses)
    monkeypatch.setattr(web, "get_http_client", lambda *args, **kwargs: client)
    return client


@pytest.mark.asyncio
async def test_default_twenty_results_and_model_facing_fields(configured, monkeypatch, load_tool_module):
    client = install(monkeypatch, (200, {"results": [result(i) for i in range(20)]}))
    tool = load_tool_module("deepseek_search")
    data = json.loads(await tool.deepseek_web_search("DeepSeek site:example.com after:2026", ori_question="原问题"))
    assert data["status"] == "ok" and data["count"] == 20
    assert [item["rank"] for item in data["results"]] == list(range(1, 21))
    assert data["results"][0] == {
        "title": "页面 0",
        "url": "https://example.com/0",
        "summary": "摘要 0",
        "date": None,
        "site_name": "Example",
        "rerank_score": 2.4,
        "authority": 3,
        "rank": 1,
    }
    url, request = client.calls[0]
    assert url == "https://api.deepseek.com/v1/tools/search"
    assert request["json"] == {
        "query": "DeepSeek site:example.com after:2026",
        "count": 20,
        "need_content": False,
        "ori_question": "原问题",
    }
    assert request["headers"] == {"Authorization": "Bearer sk-search-test"}
    assert request["follow_redirects"] is False
    assert "sk-search-test" not in str(data)


@pytest.mark.asyncio
async def test_fallback_snippet_oversize_original_question_and_empty_results(configured, monkeypatch):
    client = install(monkeypatch, (200, {"results": [result(summary="")]}), (200, {"results": []}))
    data = await web.search_web("query", ori_question="问" * 129)
    assert "ori_question" not in client.calls[0][1]["json"]
    assert data["results"][0]["summary"] == "短摘要"
    empty = await web.search_web("query")
    assert empty == {"status": "empty", "query": "query", "count": 0, "results": []}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    [
        {"query": " "},
        {"query": "字" * 129},
        {"query": "q", "count": 51},
        {"query": "q", "count": True},
        {"query": "q", "count": 0},
        {"query": "q", "need_content": "false"},
    ],
)
async def test_invalid_search_never_uses_network(configured, monkeypatch, kwargs):
    client = install(monkeypatch)
    assert (await web.search_web(**kwargs))["error"]["code"] == "invalid_request"
    assert not client.calls


@pytest.mark.asyncio
async def test_body_previews_keep_all_results_and_full_files(configured, monkeypatch, tmp_path):
    monkeypatch.setattr(
        web.EnvConfig,
        "SEARCH",
        web.EnvConfig.SEARCH.model_copy(update={"content_preview_chars": 256, "max_content_chars": 256}),
    )
    bodies = ["第一页" * 300, "第二页" * 300, "第三页" * 300]
    install(monkeypatch, (200, {"results": [result(i, content=body) for i, body in enumerate(bodies)]}))
    data = await web.search_web("query", need_content=True, workspace_dir=tmp_path)
    assert data["count"] == 3
    assert sum(len(item["content"]) for item in data["results"]) == 256
    for item, original in zip(data["results"], bodies, strict=True):
        assert item["truncated"] is True
        assert (tmp_path / item["content_path"].lstrip("/")).read_text() == original


@pytest.mark.asyncio
async def test_fetch_uses_trusted_workspace_and_readable_virtual_path(
    configured, monkeypatch, tmp_path, load_tool_module
):
    content = "完整正文\n" * 2000
    client = install(monkeypatch, (200, {"title": "标题", "content": content}))
    tool = load_tool_module("deepseek_search")
    runtime = SimpleNamespace(context=FrontierRuntimeContext("1", 123, None, str(tmp_path / "trusted")))
    data = json.loads(
        await tool.deepseek_web_fetch(
            "https://example.com/article",
            config={"configurable": {"workspace_dir": str(tmp_path / "wrong")}},
            runtime=runtime,
        )
    )
    assert data["status"] == "ok" and data["truncated"] is True
    assert data["url"] == "https://example.com/article" and data["title"] == "标题"
    assert (tmp_path / "trusted" / data["content_path"].lstrip("/")).read_text() == content
    assert not (tmp_path / "wrong").exists()
    assert client.calls[0][0] == "https://api.deepseek.com/v1/tools/fetch"
    assert client.calls[0][1]["json"] == {"url": "https://example.com/article"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://user:password@example.com",
        "https://",
        "https://example.com:bad",
        "https://example.com/\nsecret",
    ],
)
async def test_invalid_fetch_never_uses_network(configured, monkeypatch, tmp_path, url):
    client = install(monkeypatch)
    assert (await web.fetch_web(url, workspace_dir=tmp_path))["error"]["code"] == "invalid_request"
    assert not client.calls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, code, stop",
    [
        (400, "invalid_request", False),
        (401, "authentication", False),
        (402, "insufficient_balance", True),
        (403, "access_denied", False),
        (404, "page_unavailable", False),
        (429, "rate_limited", True),
    ],
)
async def test_non_retryable_errors_are_safe_and_not_empty(configured, monkeypatch, status, code, stop):
    client = install(monkeypatch, (status, {"error": {"message": "secret-key /private/path"}}))
    data = await web.search_web("query")
    assert data["status"] == "error" and data["error"]["code"] == code
    assert data["error"]["stop_search"] is stop and not data["error"]["retryable"]
    assert len(client.calls) == 1 and "secret-key" not in str(data) and "/private" not in str(data)


@pytest.mark.asyncio
async def test_transient_error_retries_once_and_cancellation_propagates(configured, monkeypatch):
    client = install(monkeypatch, (503, {}), (200, {"results": []}))
    assert (await web.search_web("query"))["status"] == "empty"
    assert len(client.calls) == 2
    client = install(monkeypatch, (503, {}), (503, {}))
    assert (await web.search_web("query"))["status"] == "error" and len(client.calls) == 2
    install(monkeypatch, asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        await web.search_web("query")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [{}, {"results": None}, {"results": [result(url="javascript:alert(1)")]}, {"results": [result(rerank_score=99)]}],
)
async def test_malformed_results_are_errors_not_empty(configured, monkeypatch, response):
    install(monkeypatch, (200, response))
    assert (await web.search_web("query"))["error"]["code"] == "invalid_response"


def test_configuration_and_key_selection_do_not_follow_main_model(configured, monkeypatch):
    monkeypatch.setattr(web.EnvConfig, "ADVAN_MODEL", "another-model")
    monkeypatch.setattr(web.EnvConfig, "ADVAN_MODEL_PROVIDER", "google")
    assert web.deepseek_search_available()
    assert web._credentials() == ("https://api.deepseek.com", "sk-search-test")
    monkeypatch.setattr(
        web.EnvConfig,
        "SEARCH",
        web.EnvConfig.SEARCH.model_copy(update={"base_url": "https://proxy.example/deepseek/v1/"}),
    )
    assert web._api_base() == "https://proxy.example/deepseek"
    monkeypatch.setattr(web.EnvConfig, "SEARCH", web.EnvConfig.SEARCH.model_copy(update={"enabled": False}))
    assert not web.deepseek_search_available()


@pytest.mark.asyncio
async def test_storage_failure_is_explicit_and_does_not_claim_full_read(configured, monkeypatch, tmp_path):
    def fail(*args):
        raise OSError("secret/path")

    monkeypatch.setattr(web, "_save_content", fail)
    install(monkeypatch, (200, {"content": "字" * 10000}))
    data = await web.fetch_web("https://example.com", workspace_dir=tmp_path)
    assert data["status"] == "ok" and data["truncated"]
    assert "storage_error" in data and "content_path" not in data and "secret/path" not in str(data)


@pytest.mark.asyncio
async def test_missing_configuration_and_workspace_fail_before_request(monkeypatch):
    client = install(monkeypatch)
    assert not web.deepseek_search_available()
    assert (await web.search_web("query"))["error"]["code"] == "configuration"
    assert (await web.fetch_web("https://example.com"))["error"]["code"] == "workspace_required"
    assert (await web.search_web("query", need_content=True))["error"]["code"] == "workspace_required"
    assert not client.calls


@pytest.mark.asyncio
async def test_search_and_fetch_have_separate_process_shared_rate_gates(monkeypatch):
    clock, sleeps = [0.0], []

    async def sleep(delay):
        sleeps.append(delay)
        clock[0] += delay

    monkeypatch.setattr(web, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(web.asyncio, "sleep", sleep)
    await web._wait_for_slot("search-test")
    await web._wait_for_slot("fetch-test")
    assert not sleeps
    await web._wait_for_slot("search-test")
    await web._wait_for_slot("search-test")
    assert sleeps == [0.25, 0.25]
