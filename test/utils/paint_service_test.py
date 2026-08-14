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
async def test_paint_generates_with_responses_image_tool(monkeypatch):
    calls = {}

    class DummyResponses:
        async def create(self, **kwargs):
            calls["create"] = kwargs
            return SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="image_generation_call",
                        result=base64.b64encode(b"generated").decode(),
                    )
                ]
            )

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.responses = DummyResponses()

        async def close(self):
            calls["closed"] = True

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    result = await paint_service.paint("a crystal fox")

    assert result == b"generated"
    assert calls["client"] == {"api_key": "sk-media", "base_url": "https://media.example.com/v1"}
    assert calls["create"] == {
        "model": "gpt-image-test",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "a crystal fox"}],
            }
        ],
        "tools": [
            {
                "type": "image_generation",
                "action": "generate",
                "model": "gpt-image-test",
                "output_format": "png",
                "size": "1536x1024",
                "quality": "high",
            }
        ],
        "tool_choice": {"type": "image_generation"},
        "store": False,
        "stream": False,
    }
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_paint_edits_multiple_reference_images(monkeypatch):
    calls = {}

    class DummyResponses:
        async def create(self, **kwargs):
            calls["create"] = kwargs
            return {
                "output": [
                    {
                        "type": "image_generation_call",
                        "result": f"data:image/png;base64,{base64.b64encode(b'edited').decode()}",
                    }
                ]
            }

    class DummyClient:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

        async def close(self):
            return None

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    result = await paint_service.paint("turn it into watercolor", [_tiny_png_bytes(), _tiny_png_bytes()])

    assert result == b"edited"
    request = calls["create"]
    assert request["model"] == "gpt-image-test"
    assert request["tools"] == [
        {
            "type": "image_generation",
            "action": "edit",
            "model": "gpt-image-test",
            "output_format": "png",
            "size": "1536x1024",
            "quality": "high",
        }
    ]
    content = request["input"][0]["content"]
    assert content[0] == {"type": "input_text", "text": "turn it into watercolor"}
    assert len(content) == 3
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert base64.b64decode(content[1]["image_url"].partition(",")[2]).startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_paint_rejects_invalid_responses_base64(monkeypatch):
    class DummyResponses:
        async def create(self, **_kwargs):
            return {"output": [{"type": "image_generation_call", "result": "not base64!"}]}

    class DummyClient:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

        async def close(self):
            return None

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    assert await paint_service.paint("a landscape") is None


@pytest.mark.asyncio
async def test_paint_returns_none_for_empty_response(monkeypatch):
    class DummyResponses:
        async def create(self, **_kwargs):
            return SimpleNamespace(output=[])

    class DummyClient:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

        async def close(self):
            return None

    _set_paint_config(monkeypatch)
    monkeypatch.setattr(paint_service, "AsyncOpenAI", DummyClient)

    assert await paint_service.paint("a prompt") is None


@pytest.mark.asyncio
async def test_paint_returns_none_on_client_error_and_closes(monkeypatch):
    calls = {}

    class DummyResponses:
        async def create(self, **_kwargs):
            raise RuntimeError("provider failed")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.responses = DummyResponses()

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
