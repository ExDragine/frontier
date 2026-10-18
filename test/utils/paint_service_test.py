# ruff: noqa: S101

import asyncio
import base64
import io
from types import SimpleNamespace

import pytest
from PIL import Image

from utils import paint_service


def _set_paint_config(monkeypatch, *, base_url: str = "https://media.example.com/v1", api_mode: str = "responses") -> None:
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gpt-image-test")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL_PROVIDER", "media")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_SIZE", "1536x1024")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_QUALITY", "high")
    monkeypatch.setattr(
        paint_service,
        "get_provider_profile",
        lambda name: {
            "type": "openai",
            "api_mode": api_mode,
            "base_url": base_url,
            "api_key": "sk-media",
        }
        if name == "media"
        else None,
    )


def _tiny_png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (4, 4), "blue").save(output, format="PNG")
    return output.getvalue()


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
                "size": "auto",
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
            "size": "auto",
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


def _install_images_client(monkeypatch, *, result=None, error=None):
    calls = {}

    async def invoke(operation, **kwargs):
        calls[operation] = kwargs
        if error is not None:
            raise error
        return result

    class Client:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = SimpleNamespace(generate=self.generate, edit=self.edit)

        async def generate(self, **kwargs):
            return await invoke("generate", **kwargs)

        async def edit(self, **kwargs):
            return await invoke("edit", **kwargs)

        async def close(self):
            calls["closed"] = True

    _set_paint_config(monkeypatch, api_mode="chat_completions")
    monkeypatch.setattr(paint_service, "AsyncOpenAI", Client)
    return calls


@pytest.mark.asyncio
@pytest.mark.parametrize("as_dict", [False, True])
async def test_images_api_generates_without_responses_or_legacy_fields(monkeypatch, as_dict):
    item = {"b64_json": base64.b64encode(_tiny_png_bytes()).decode()}
    result = {"data": [item]} if as_dict else SimpleNamespace(data=[SimpleNamespace(**item)])
    calls = _install_images_client(monkeypatch, result=result)

    assert await paint_service.paint("a fox") == _tiny_png_bytes()
    assert calls["generate"] == {
        "model": "gpt-image-test", "prompt": "a fox", "n": 1, "output_format": "png",
        "stream": False, "size": "auto", "quality": "high",
    }
    assert "edit" not in calls
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_images_api_edits_all_references_as_png_files(monkeypatch):
    calls = _install_images_client(monkeypatch, result={"data": [{
        "b64_json": "data:image/png;base64," + base64.b64encode(_tiny_png_bytes()).decode(),
    }]})

    assert await paint_service.paint("watercolor", [_tiny_png_bytes(), _tiny_png_bytes()]) == _tiny_png_bytes()
    params = calls["edit"]
    assert params["prompt"] == "watercolor" and params["model"] == "gpt-image-test"
    assert params["size"] == "auto" and params["quality"] == "high"
    assert "response_format" not in params and "input" not in params
    assert len(params["image"]) == 2
    for index, (name, raw, mime) in enumerate(params["image"], start=1):
        assert name == f"reference-{index}.png" and mime == "image/png"
        assert raw.startswith(b"\x89PNG")
    assert "generate" not in calls
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_images_api_keeps_auto_size_with_blank_legacy_size_and_quality(monkeypatch):
    calls = _install_images_client(monkeypatch, result={"data": []})
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_SIZE", " ")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_QUALITY", "")

    assert await paint_service.paint("a fox") is None
    assert calls["generate"]["size"] == "auto"
    assert "quality" not in calls["generate"]


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [None, {}, {"data": []}, {"data": [{}]}, {"data": [{"b64_json": "invalid!"}]}])
async def test_images_api_rejects_unusable_responses(monkeypatch, result):
    calls = _install_images_client(monkeypatch, result=result)

    assert await paint_service.paint("a fox") is None
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_images_api_downloads_provider_url_with_public_fetcher(monkeypatch):
    calls = _install_images_client(monkeypatch, result={"data": [{"url": "https://cdn.example/image.png?sig=private"}]})

    class Fetcher:
        def __init__(self, client, cache_dir, *, fake_ip_fallback):
            assert client is sentinel
            assert fake_ip_fallback is True

        async def get(self, url, *, limit):
            calls["download"] = (url, limit)
            return _tiny_png_bytes(), "image/png"

    sentinel = object()
    monkeypatch.setattr(paint_service, "PublicFetcher", Fetcher)
    monkeypatch.setattr(paint_service, "get_http_client", lambda name: sentinel if name == "paint_service" else None)
    monkeypatch.setattr(paint_service.EnvConfig, "MESSAGE_MEDIA_FAKE_IP_FALLBACK", True)

    assert await paint_service.paint("a fox") == _tiny_png_bytes()
    assert calls["download"] == ("https://cdn.example/image.png?sig=private", 20_000_000)
    assert calls["closed"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["http://127.0.0.1/image", "file:///etc/passwd", "https://user:password@example.com/x"])
async def test_images_api_rejects_nonpublic_output_urls(monkeypatch, url):
    calls = _install_images_client(monkeypatch, result={"data": [{"url": url}]})

    assert await paint_service.paint("a fox") is None
    assert calls["closed"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [RuntimeError("provider failed"), asyncio.CancelledError()])
async def test_images_api_always_closes_client(monkeypatch, error):
    calls = _install_images_client(monkeypatch, error=error)

    if isinstance(error, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await paint_service.paint("a fox")
    else:
        assert await paint_service.paint("a fox") is None
    assert calls["closed"] is True
