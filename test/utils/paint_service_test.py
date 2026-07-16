# ruff: noqa: S101

import base64
from types import SimpleNamespace

import pytest

from utils import paint_service


def _set_paint_config(monkeypatch, *, base_url: str = "https://media.example.com/v1") -> None:
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gpt-image-test")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL_PROVIDER", "media")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_SIZE", "1536x1024")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_QUALITY", "high")
    monkeypatch.setattr(
        paint_service,
        "get_provider_profile",
        lambda name: {
            "type": "openai",
            "base_url": base_url,
            "api_key": "sk-media",
        }
        if name == "media"
        else None,
    )


def _tiny_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6f8AAAAASUVORK5CYII="
    )


@pytest.mark.asyncio
async def test_paint_generates_with_openai_images_api(monkeypatch):
    calls = {}

    class DummyImages:
        async def generate(self, **kwargs):
            calls["generate"] = kwargs
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b"generated").decode())])

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = DummyImages()

        async def close(self):
            calls["closed"] = True

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    result = await paint_service.paint("a crystal fox")

    assert result == b"generated"
    assert calls["client"] == {"api_key": "sk-media", "base_url": "https://media.example.com/v1"}
    assert calls["generate"] == {
        "model": "gpt-image-test",
        "prompt": "a crystal fox",
        "size": "1536x1024",
        "quality": "high",
    }
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_paint_edits_multiple_reference_images(monkeypatch):
    calls = {}

    class DummyImages:
        async def edit(self, **kwargs):
            calls["edit"] = kwargs
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b"edited").decode())])

    class DummyClient:
        def __init__(self, **_kwargs):
            self.images = DummyImages()

        async def close(self):
            return None

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    result = await paint_service.paint("turn it into watercolor", [_tiny_png_bytes(), _tiny_png_bytes()])

    assert result == b"edited"
    request = calls["edit"]
    assert request["model"] == "gpt-image-test"
    assert request["prompt"] == "turn it into watercolor"
    assert request["size"] == "1536x1024"
    assert request["quality"] == "high"
    assert len(request["image"]) == 2
    assert request["image"][0][0] == "reference_0.png"
    assert request["image"][0][2] == "image/png"
    assert request["image"][0][1].startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_paint_downloads_url_response(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            return None

        async def aread(self):
            return b"downloaded-image"

    class DummyHttpClient:
        async def get(self, url):
            assert url == "https://cdn.example.com/image.png"
            return DummyResponse()

    class DummyImages:
        async def generate(self, **_kwargs):
            return SimpleNamespace(data=[SimpleNamespace(b64_json=None, url="https://cdn.example.com/image.png")])

    class DummyClient:
        def __init__(self, **_kwargs):
            self.images = DummyImages()

        async def close(self):
            return None

    _set_paint_config(monkeypatch, base_url="")
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)
    monkeypatch.setattr(paint_service, "httpx_client", DummyHttpClient())

    assert await paint_service.paint("a landscape") == b"downloaded-image"


@pytest.mark.asyncio
async def test_paint_returns_none_for_empty_response(monkeypatch):
    class DummyImages:
        async def generate(self, **_kwargs):
            return SimpleNamespace(data=[])

    class DummyClient:
        def __init__(self, **_kwargs):
            self.images = DummyImages()

        async def close(self):
            return None

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    assert await paint_service.paint("a prompt") is None


@pytest.mark.asyncio
async def test_paint_returns_none_on_client_error_and_closes(monkeypatch):
    calls = {}

    class DummyImages:
        async def generate(self, **_kwargs):
            raise RuntimeError("provider failed")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.images = DummyImages()

        async def close(self):
            calls["closed"] = True

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    assert await paint_service.paint("a prompt") is None
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_paint_returns_none_when_model_empty(monkeypatch):
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "")

    assert await paint_service.paint("a crystal fox") is None


def test_paint_rate_limiter_rejects_requests_over_limit():
    limiter = paint_service.PaintRateLimiter()

    first = limiter.check("10001", now=1000.0, max_requests=3, window_seconds=600)
    second = limiter.check("10001", now=1100.0, max_requests=3, window_seconds=600)
    third = limiter.check("10001", now=1200.0, max_requests=3, window_seconds=600)
    fourth = limiter.check("10001", now=1300.0, max_requests=3, window_seconds=600)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is True
    assert fourth.allowed is False
    assert fourth.retry_after_seconds == 300


def test_paint_rate_limiter_allows_after_window_slides():
    limiter = paint_service.PaintRateLimiter()

    limiter.check("10001", now=1000.0, max_requests=3, window_seconds=600)
    limiter.check("10001", now=1100.0, max_requests=3, window_seconds=600)
    limiter.check("10001", now=1200.0, max_requests=3, window_seconds=600)
    result = limiter.check("10001", now=1601.0, max_requests=3, window_seconds=600)

    assert result.allowed is True
    assert result.retry_after_seconds == 0
