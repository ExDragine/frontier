# ruff: noqa: S101

import base64
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from utils import paint_service


def _image_response(raw: bytes):
    return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(raw).decode("utf-8"))])


def _tiny_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6f8AAAAASUVORK5CYII="
    )


@pytest.mark.asyncio
async def test_paint_uses_images_generate_without_reference_images(monkeypatch):
    calls = {}

    class DummyImages:
        async def generate(self, **kwargs):
            calls["generate"] = kwargs
            return _image_response(b"generated-image")

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = DummyImages()

    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_BASE_URL", "https://global.example.com/v1")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://paint.example.com/v1")
    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_API_KEY", SecretStr("sk-global"))
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint"))
    monkeypatch.setattr(paint_service, "AsyncClient", DummyClient)

    result = await paint_service.paint("a crystal fox")

    assert result == b"generated-image"
    assert calls["client"]["base_url"] == "https://paint.example.com/v1"
    assert calls["client"]["api_key"] == "sk-paint"
    assert calls["generate"]["model"] == paint_service.EnvConfig.PAINT_MODEL
    assert calls["generate"]["prompt"] == "a crystal fox"
    assert calls["generate"]["response_format"] == "b64_json"


@pytest.mark.asyncio
async def test_paint_passes_empty_paint_base_url_to_openai_client(monkeypatch):
    calls = {}

    class DummyImages:
        async def generate(self, **kwargs):
            calls["generate"] = kwargs
            return _image_response(b"generated-image")

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = DummyImages()

    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_BASE_URL", "https://global.example.com/v1")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "")
    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_API_KEY", SecretStr("sk-global"))
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint"))
    monkeypatch.setattr(paint_service, "AsyncClient", DummyClient)

    result = await paint_service.paint("a blank endpoint fox")

    assert result == b"generated-image"
    assert calls["client"]["api_key"] == "sk-paint"
    assert calls["client"]["base_url"] == ""


@pytest.mark.asyncio
async def test_paint_uses_google_genai_for_vertex_style_gateway(monkeypatch):
    calls = {}

    class DummyHttpOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyAioModels:
        async def generate_images(self, **kwargs):
            calls["generate_images"] = kwargs
            image = SimpleNamespace(image_bytes=b"vertex-generated-image", mime_type="image/png")
            return SimpleNamespace(generated_images=[SimpleNamespace(image=image)])

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.aio = SimpleNamespace(models=DummyAioModels())

    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://zenmux.ai/api/vertex-ai")
    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_API_KEY", SecretStr("sk-global"))
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(paint_service, "genai_types", SimpleNamespace(HttpOptions=DummyHttpOptions))

    result = await paint_service.paint("a relay cat")

    assert result == b"vertex-generated-image"
    assert calls["client"]["api_key"] == "sk-paint"
    assert calls["client"]["vertexai"] is True
    assert calls["client"]["http_options"].kwargs == {
        "api_version": "v1",
        "base_url": "https://zenmux.ai/api/vertex-ai",
    }
    assert calls["generate_images"] == {
        "model": paint_service.EnvConfig.PAINT_MODEL,
        "prompt": "a relay cat",
    }


@pytest.mark.asyncio
async def test_paint_edits_images_with_google_genai_for_vertex_style_gateway(monkeypatch):
    calls = {}

    class DummyHttpOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyImage:
        def __init__(self, *, image_bytes, mime_type):
            self.image_bytes = image_bytes
            self.mime_type = mime_type

    class DummyRawReferenceImage:
        def __init__(self, *, reference_id, reference_image):
            self.reference_id = reference_id
            self.reference_image = reference_image

    class DummyAioModels:
        async def edit_image(self, **kwargs):
            calls["edit_image"] = kwargs
            image = SimpleNamespace(image_bytes=b"vertex-edited-image", mime_type="image/png")
            return SimpleNamespace(generated_images=[SimpleNamespace(image=image)])

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.aio = SimpleNamespace(models=DummyAioModels())

    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://zenmux.ai/api/vertex-ai")
    monkeypatch.setattr(paint_service.EnvConfig, "OPENAI_API_KEY", SecretStr("sk-global"))
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            HttpOptions=DummyHttpOptions,
            Image=DummyImage,
            RawReferenceImage=DummyRawReferenceImage,
        ),
    )

    result = await paint_service.paint("add a robot", [_tiny_png_bytes()])

    assert result == b"vertex-edited-image"
    assert calls["client"]["api_key"] == "sk-paint"
    assert calls["client"]["vertexai"] is True
    assert calls["client"]["http_options"].kwargs["base_url"] == "https://zenmux.ai/api/vertex-ai"
    assert calls["edit_image"]["model"] == paint_service.EnvConfig.PAINT_MODEL
    assert calls["edit_image"]["prompt"] == "add a robot"
    assert len(calls["edit_image"]["reference_images"]) == 1
    reference = calls["edit_image"]["reference_images"][0]
    assert reference.reference_id == 1
    assert reference.reference_image.mime_type == "image/png"
    assert reference.reference_image.image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.asyncio
async def test_paint_uses_images_edit_with_reference_images(monkeypatch):
    calls = {}

    class DummyImages:
        async def edit(self, **kwargs):
            calls["edit"] = kwargs
            return _image_response(b"edited-image")

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.images = DummyImages()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://paint.example.com/v1")
    monkeypatch.setattr(paint_service, "AsyncClient", DummyClient)

    result = await paint_service.paint("turn it into watercolor", [_tiny_png_bytes()])

    assert result == b"edited-image"
    assert calls["edit"]["model"] == paint_service.EnvConfig.PAINT_MODEL
    assert calls["edit"]["prompt"] == "turn it into watercolor"
    assert calls["edit"]["response_format"] == "b64_json"
    assert len(calls["edit"]["image"]) == 1
    filename, content, content_type = calls["edit"]["image"][0]
    assert filename == "reference-1.png"
    assert isinstance(content, bytes)
    assert content.startswith(b"\x89PNG\r\n\x1a\n")
    assert content_type == "image/png"


@pytest.mark.asyncio
async def test_paint_returns_none_when_images_api_fails(monkeypatch):
    class DummyImages:
        async def generate(self, **_kwargs):
            raise RuntimeError("boom")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.images = DummyImages()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://paint.example.com/v1")
    monkeypatch.setattr(paint_service, "AsyncClient", DummyClient)

    result = await paint_service.paint("a crystal fox")

    assert result is None


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
