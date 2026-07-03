# ruff: noqa: S101

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from utils import paint_service


def _tiny_png_bytes() -> bytes:
    """最小有效 PNG 图片（1x1 像素）。"""
    import base64

    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6f8AAAAASUVORK5CYII="
    )


def _gemini_image_response(raw: bytes, mime_type: str = "image/png"):
    """构建一个 Gemini generate_content 响应，包含一张图片。"""
    inline_data = SimpleNamespace(data=raw, mime_type=mime_type)
    part = SimpleNamespace(inline_data=inline_data, text=None)
    content = SimpleNamespace(parts=[part])
    candidate = SimpleNamespace(content=content, finish_reason=None)
    return SimpleNamespace(candidates=[candidate])


# ── Gemini 图片生成测试 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paint_gemini_text_to_image(monkeypatch):
    """纯文本 → 图片生成：不传参考图片时只传 prompt 字符串。"""
    calls = {}

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            calls["generate_content"] = kwargs
            return _gemini_image_response(b"gemini-generated-image")

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.aio = DummyAio()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://generativelanguage.googleapis.com")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint-key"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    result = await paint_service.paint("a crystal fox")

    assert result == b"gemini-generated-image"
    assert calls["client"]["api_key"] == "sk-paint-key"
    assert calls["generate_content"]["model"] == "gemini-2.5-flash-image"
    # 没有参考图片时，contents 应该是纯字符串
    assert calls["generate_content"]["contents"] == "a crystal fox"
    # 验证 config
    config = calls["generate_content"]["config"]
    assert "TEXT" in config.kwargs["response_modalities"]
    assert "IMAGE" in config.kwargs["response_modalities"]


@pytest.mark.asyncio
async def test_paint_gemini_image_edit(monkeypatch):
    """图片编辑：传参考图片时 contents 包含图片 Parts 和文本 Part。"""
    calls = {}

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            calls["generate_content"] = kwargs
            return _gemini_image_response(b"gemini-edited-image")

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.aio = DummyAio()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://generativelanguage.googleapis.com")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint-key"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    result = await paint_service.paint("turn it into watercolor", [_tiny_png_bytes()])

    assert result == b"gemini-edited-image"
    contents = calls["generate_content"]["contents"]
    assert len(contents) == 2
    # 第一个 part 是参考图片
    assert contents[0].mime_type == "image/png"
    # 第二个 part 是文本提示词
    assert contents[1].text == "turn it into watercolor"


@pytest.mark.asyncio
async def test_paint_gemini_aspect_ratio_config(monkeypatch):
    """自定义宽高比应反映在 ImageConfig 中。"""
    calls = {}

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            calls["generate_content"] = kwargs
            return _gemini_image_response(b"wide-image")

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.aio = DummyAio()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://generativelanguage.googleapis.com")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint-key"))
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_ASPECT_RATIO", "16:9")
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    await paint_service.paint("a wide landscape")

    config = calls["generate_content"]["config"]
    assert config.kwargs["image_config"].kwargs["aspect_ratio"] == "16:9"


@pytest.mark.asyncio
async def test_paint_gemini_api_key_falls_back_to_google_key(monkeypatch):
    """PAINT_API_KEY 为空时回退到 GOOGLE_API_KEY。"""
    calls = {}

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            calls["generate_content"] = kwargs
            return _gemini_image_response(b"gemini-with-google-key")

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.aio = DummyAio()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr(""))
    monkeypatch.setattr(paint_service.EnvConfig, "GOOGLE_API_KEY", SecretStr("sk-google-key"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    result = await paint_service.paint("a landscape")

    assert result == b"gemini-with-google-key"
    assert calls["client"]["api_key"] == "sk-google-key"


# ── 安全过滤与错误处理测试 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_paint_gemini_safety_filter(monkeypatch):
    """安全过滤时返回 None。"""

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            finish_reason = SimpleNamespace(name="SAFETY")
            candidate = SimpleNamespace(content=None, finish_reason=finish_reason)
            return SimpleNamespace(candidates=[candidate])

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "https://generativelanguage.googleapis.com")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-key"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=lambda **kw: SimpleNamespace(aio=DummyAio())))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    result = await paint_service.paint("something inappropriate")

    assert result is None


@pytest.mark.asyncio
async def test_paint_gemini_no_candidates(monkeypatch):
    """空 candidates 时返回 None。"""

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            return SimpleNamespace(candidates=[])

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-key"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=lambda **kw: SimpleNamespace(aio=DummyAio())))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    result = await paint_service.paint("a prompt")

    assert result is None


@pytest.mark.asyncio
async def test_paint_gemini_client_error(monkeypatch):
    """ClientError 时捕获并返回 None。"""
    from google.genai.errors import ClientError

    class DummyAioModels:
        async def generate_content(self, **kwargs):
            raise ClientError(500, {"error": "test"})

    class DummyAio:
        def __init__(self):
            self.models = DummyAioModels()

    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "gemini-2.5-flash-image")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_BASE_URL", "")
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_API_KEY", SecretStr("sk-key"))
    monkeypatch.setattr(paint_service, "genai", SimpleNamespace(Client=lambda **kw: SimpleNamespace(aio=DummyAio())))
    monkeypatch.setattr(
        paint_service,
        "genai_types",
        SimpleNamespace(
            GenerateContentConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            ImageConfig=lambda **kw: SimpleNamespace(kwargs=kw),
            Part=SimpleNamespace(
                from_bytes=lambda data, mime_type: SimpleNamespace(data=data, mime_type=mime_type),
                from_text=lambda text: SimpleNamespace(text=text),
            ),
            HttpOptions=lambda **kw: SimpleNamespace(kwargs=kw),
        ),
    )

    result = await paint_service.paint("a prompt")

    assert result is None


# ── 空绘画模型配置测试 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paint_returns_none_when_paint_model_empty_without_fallback(monkeypatch):
    """PAINT_MODEL 为空时直接失败，不再使用备用绘画服务。"""
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "")

    result = await paint_service.paint("a crystal fox")

    assert result is None


@pytest.mark.asyncio
async def test_paint_with_reference_images_returns_none_when_model_empty(monkeypatch):
    """PAINT_MODEL 为空且有参考图片时也直接失败。"""
    monkeypatch.setattr(paint_service.EnvConfig, "PAINT_MODEL", "")

    result = await paint_service.paint("turn it into watercolor", [_tiny_png_bytes()])

    assert result is None


# ── 限流器测试（保持不变）──────────────────────────────────────────


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
