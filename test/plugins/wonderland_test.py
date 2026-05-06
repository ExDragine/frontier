# ruff: noqa: S101

import importlib
import importlib.util
import sys
import types
from itertools import count
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr


class DummyUniMessage:
    def __init__(self, content=None):
        self.content = content

    def __add__(self, other):
        return type(self)([self.content, other.content])

    @classmethod
    def reply(cls, message_id):
        return cls({"reply": message_id})

    @classmethod
    def text(cls, text):
        return cls(text)

    @classmethod
    def image(cls, raw=None):
        return cls(raw)

    @classmethod
    def video(cls, url=None, raw=None):
        return cls({"video_url": url, "video_raw": raw})

    async def send(self):
        return None


@pytest.fixture
def load_wonderland_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "plugins/wonderland/__init__.py"
    idx_gen = count()

    async def fake_message_extract(_segments):
        return "", [], [], []

    def _load():
        unique_name = f"test_plugins_wonderland_{next(idx_gen)}"
        spec = importlib.util.spec_from_file_location(unique_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载模块: {module_path}")

        module = importlib.util.module_from_spec(spec)
        message_stub = types.ModuleType("utils.message")
        message_stub.message_extract = fake_message_extract

        old_message = sys.modules.get("utils.message")
        utils_pkg = importlib.import_module("utils")
        old_attr = getattr(utils_pkg, "message", None)
        sys.modules["utils.message"] = message_stub
        utils_pkg.message = message_stub
        old_nonebot_require = None
        old_plugin_require = None
        try:
            import nonebot
            import nonebot.plugin.load as plugin_load

            old_nonebot_require = getattr(nonebot, "require", None)
            old_plugin_require = getattr(plugin_load, "require", None)
            plugin_load.require = lambda *_args, **_kwargs: None
            nonebot.require = plugin_load.require
            sys.modules[unique_name] = module
            spec.loader.exec_module(module)
            return module
        finally:
            if old_message is None:
                sys.modules.pop("utils.message", None)
            else:
                sys.modules["utils.message"] = old_message
            if old_attr is None:
                delattr(utils_pkg, "message")
            else:
                utils_pkg.message = old_attr
            if old_nonebot_require is not None and old_plugin_require is not None:
                plugin_load.require = old_plugin_require
                nonebot.require = old_nonebot_require

    return _load


def test_wonderland_keeps_paint_command_for_compatibility(load_wonderland_module):
    wonderland = load_wonderland_module()

    assert hasattr(wonderland, "painter")
    assert hasattr(wonderland, "handle_painter")
    assert wonderland.PAINT_COMMAND_PREFIXES == ("帮我画一张图", "画一张图", "画图", "绘图", "paint")


@pytest.mark.asyncio
async def test_handle_painter_uses_shared_paint_service_with_reply_context(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()
    captured = {}

    async def fake_message_extract(_segments):
        return "[回复消息:900]/画图 改成水彩", [b"current-image"], [], []

    async def fake_build_reply_context(_bot, _event, reply_seq, group_id, _messages_db):
        assert reply_seq == 900
        assert group_id == 123
        return "\n\n[引用消息]\n用户(Alice): [图片]", [b"quoted-image"]

    async def fake_paint(prompt, reference_images):
        captured["prompt"] = prompt
        captured["reference_images"] = reference_images
        return b"painted-image"

    event = SimpleNamespace(
        data=SimpleNamespace(
            segments=[{"type": "reply", "data": {"message_seq": 900}}, {"type": "text", "data": {"text": "/画图 改成水彩"}}],
            group=SimpleNamespace(group_id=123),
            message_seq=456,
        ),
        get_user_id=lambda: "10001",
    )

    monkeypatch.setattr(wonderland, "message_extract", fake_message_extract)
    monkeypatch.setattr(wonderland, "reply_seq_from_segments", lambda _segments: 900, raising=False)
    monkeypatch.setattr(wonderland, "build_reply_context", fake_build_reply_context, raising=False)
    monkeypatch.setattr(wonderland, "get_bot", lambda: SimpleNamespace(), raising=False)
    monkeypatch.setattr(wonderland, "paint", fake_paint)
    monkeypatch.setattr(wonderland, "UniMessage", DummyUniMessage)

    await wonderland.handle_painter(event)

    assert captured["prompt"] == "改成水彩\n\n[引用消息]\n用户(Alice): [图片]"
    assert captured["reference_images"] == [b"quoted-image", b"current-image"]


def test_strip_paint_prompt_handles_prefixed_text_without_whitespace(load_wonderland_module):
    wonderland = load_wonderland_module()

    assert wonderland.strip_paint_prompt("/画图一只猫") == "一只猫"
    assert wonderland.strip_paint_prompt("paint a crystal fox") == "a crystal fox"


def test_strip_video_prompt_handles_prefixed_text(load_wonderland_module):
    wonderland = load_wonderland_module()

    assert wonderland.strip_video_prompt("/video a happy horse") == "a happy horse"
    assert wonderland.strip_video_prompt("视频 一匹马") == "一匹马"


@pytest.mark.asyncio
async def test_handle_video_sends_generated_video(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()
    sent_messages = []

    class CapturingUniMessage(DummyUniMessage):
        async def send(self):
            sent_messages.append(self.content)
            return None

    async def fake_message_extract(_segments):
        return "/video a happy horse", [], [], []

    async def fake_generate_video(prompt):
        assert prompt == "a happy horse"
        return wonderland.VideoGenerationResult(raw=b"generated-video")

    event = SimpleNamespace(
        data=SimpleNamespace(
            segments=[{"type": "text", "data": {"text": "/video a happy horse"}}],
            group=SimpleNamespace(group_id=123),
            message_seq=456,
        ),
        get_user_id=lambda: "10001",
    )

    monkeypatch.setattr(wonderland, "message_extract", fake_message_extract)
    monkeypatch.setattr(wonderland, "generate_video", fake_generate_video)
    monkeypatch.setattr(wonderland, "UniMessage", CapturingUniMessage)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_RATE_LIMIT_MAX_REQUESTS", 1, raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_RATE_LIMIT_WINDOW_SECONDS", 900, raising=False)
    monkeypatch.setattr(wonderland, "video_rate_limiter", wonderland.PaintRateLimiter())

    await wonderland.handle_video(event)

    assert sent_messages == [
        [{"reply": "456"}, "视频生成OK了"],
        {"video_url": None, "video_raw": b"generated-video"},
    ]


@pytest.mark.asyncio
async def test_handle_video_rate_limits_by_user_before_generation(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()
    sent_messages = []

    class CapturingUniMessage(DummyUniMessage):
        async def send(self):
            sent_messages.append(self.content)
            return None

    async def fake_message_extract(_segments):
        return "/video a happy horse", [], [], []

    async def fake_generate_video(_prompt):
        raise AssertionError("generate_video should not be called while rate limited")

    class DenyLimiter:
        def check(self, user_id, *, now, max_requests, window_seconds):
            assert user_id == "10001"
            assert max_requests == 1
            assert window_seconds == 900
            return wonderland.PaintRateLimitResult(False, 120)

    event = SimpleNamespace(
        data=SimpleNamespace(
            segments=[{"type": "text", "data": {"text": "/video a happy horse"}}],
            group=SimpleNamespace(group_id=123),
            message_seq=456,
        ),
        get_user_id=lambda: "10001",
    )

    monkeypatch.setattr(wonderland, "message_extract", fake_message_extract)
    monkeypatch.setattr(wonderland, "generate_video", fake_generate_video)
    monkeypatch.setattr(wonderland, "UniMessage", CapturingUniMessage)
    monkeypatch.setattr(wonderland, "video_rate_limiter", DenyLimiter())
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_RATE_LIMIT_MAX_REQUESTS", 1, raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_RATE_LIMIT_WINDOW_SECONDS", 900, raising=False)

    await wonderland.handle_video(event)

    assert sent_messages == ["视频生成得太快了，120 秒后再试吧"]


def test_generate_video_uses_happyhorse_vertex_gateway(load_wonderland_module, monkeypatch):
    wonderland = load_wonderland_module()
    calls = {}

    class DummyHttpOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyModels:
        def generate_videos(self, **kwargs):
            calls["generate_videos"] = kwargs
            return SimpleNamespace(done=False)

    class DummyOperations:
        def get(self, *, operation):
            calls["operation"] = operation
            video = SimpleNamespace(video_bytes=b"happyhorse-video")
            return SimpleNamespace(
                done=True,
                result=SimpleNamespace(generated_videos=[SimpleNamespace(video=video)]),
            )

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.models = DummyModels()
            self.operations = DummyOperations()
            self.closed = False

        def close(self):
            self.closed = True
            calls["closed"] = True

    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_MODEL", "alibaba/happyhorse-1.0", raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_BASE_URL", "https://zenmux.ai/api/vertex-ai", raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_API_KEY", SecretStr("sk-video"), raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_POLL_INTERVAL_SECONDS", 0, raising=False)
    monkeypatch.setattr(wonderland.EnvConfig, "VIDEO_POLL_TIMEOUT_SECONDS", 30, raising=False)
    monkeypatch.setattr(wonderland, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(wonderland, "genai_types", SimpleNamespace(HttpOptions=DummyHttpOptions))

    result = wonderland._generate_video_sync("a happy horse")

    assert result == wonderland.VideoGenerationResult(raw=b"happyhorse-video")
    assert calls["client"]["api_key"] == "sk-video"
    assert calls["client"]["vertexai"] is True
    assert calls["client"]["http_options"].kwargs == {
        "api_version": "v1",
        "base_url": "https://zenmux.ai/api/vertex-ai",
    }
    assert calls["generate_videos"] == {
        "model": "alibaba/happyhorse-1.0",
        "prompt": "a happy horse",
    }
    assert calls["closed"] is True


def test_video_result_from_generated_video_uses_http_url(load_wonderland_module):
    wonderland = load_wonderland_module()

    result = wonderland._video_result_from_generated_video(
        SimpleNamespace(),
        SimpleNamespace(video=SimpleNamespace(uri="https://example.com/video.mp4")),
    )

    assert result == wonderland.VideoGenerationResult(url="https://example.com/video.mp4")


def test_get_video_operation_supports_older_sdk_method(load_wonderland_module):
    wonderland = load_wonderland_module()
    operation = SimpleNamespace(name="operations/123")
    updated_operation = SimpleNamespace(done=True)

    class DummyOperations:
        def get_videos_operation(self, *, operation):
            assert operation.name == "operations/123"
            return updated_operation

    result = wonderland._get_video_operation(SimpleNamespace(operations=DummyOperations()), operation)

    assert result is updated_operation
