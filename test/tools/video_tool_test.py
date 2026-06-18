# ruff: noqa: S101

import base64

import pytest


def _data_url(mime_type: str, raw: bytes) -> str:
    return f"data:{mime_type};base64,{base64.b64encode(raw).decode()}"


@pytest.mark.asyncio
async def test_get_video_uses_shared_video_service(load_tool_module, monkeypatch):
    mod = load_tool_module("video")
    captured = {}

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return mod.VideoGenerationResult(raw=b"generated-video")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_video("a happy horse", state={"user_id": "10001"})

    assert captured == {"prompt": "a happy horse", "image": None, "video": None}
    assert "视频生成OK了" in text
    assert "send_staged_artifact" not in text
    assert "staged_artifact" not in text
    assert artifact.content["raw"] == b"generated-video"


@pytest.mark.asyncio
async def test_get_video_can_return_url_artifact(load_tool_module, monkeypatch):
    mod = load_tool_module("video")

    async def fake_generate_video(_prompt, *, image=None, video=None):
        assert image is None
        assert video is None
        return mod.VideoGenerationResult(url="https://example.com/video.mp4")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_video("a happy horse", state={"user_id": "10001"})

    assert "视频生成OK了" in text
    assert artifact.content["url"] == "https://example.com/video.mp4"


@pytest.mark.asyncio
async def test_get_video_image_input_uses_latest_user_image(load_tool_module, monkeypatch):
    mod = load_tool_module("video")
    captured = {}
    state = {
        "user_id": "10001",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "old"},
                    {"type": "image_url", "image_url": {"url": _data_url("image/png", b"history-image")}},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "make this move"},
                    {"type": "image_url", "image_url": {"url": _data_url("image/jpeg", b"current-image")}},
                ],
            },
        ],
    }

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return mod.VideoGenerationResult(raw=b"generated-video")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_video("make this move", input_type="image", state=state)

    assert captured["prompt"] == "make this move"
    assert captured["image"] == mod.MediaReference(data=b"current-image", mime_type="image/jpeg")
    assert captured["video"] is None
    assert "视频生成OK了" in text
    assert artifact.content["raw"] == b"generated-video"


@pytest.mark.asyncio
async def test_get_video_image_input_prefers_injected_image_inputs(load_tool_module, monkeypatch):
    mod = load_tool_module("video")
    captured = {}
    state = {
        "user_id": "10001",
        "image_inputs": [b"injected-image"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": _data_url("image/png", b"message-image")}},
                ],
            },
        ],
    }

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return mod.VideoGenerationResult(raw=b"generated-video")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    await mod.get_video("make this move", input_type="image", state=state)

    assert captured["image"] == mod.MediaReference(data=b"injected-image", mime_type="image/jpeg")
    assert captured["video"] is None


@pytest.mark.asyncio
async def test_get_video_video_input_uses_latest_user_video(load_tool_module, monkeypatch):
    mod = load_tool_module("video")
    captured = {}
    state = {
        "user_id": "10001",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "extend it"},
                    {"type": "video_url", "video_url": {"url": _data_url("video/mp4", b"current-video")}},
                ],
            },
        ],
    }

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return mod.VideoGenerationResult(raw=b"generated-video")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_video("extend it", input_type="video", state=state)

    assert captured["prompt"] == "extend it"
    assert captured["image"] is None
    assert captured["video"] == mod.MediaReference(data=b"current-video", mime_type="video/mp4")
    assert "视频生成OK了" in text
    assert artifact.content["raw"] == b"generated-video"


@pytest.mark.asyncio
async def test_get_video_video_input_prefers_injected_video_inputs(load_tool_module, monkeypatch):
    mod = load_tool_module("video")
    captured = {}
    state = {
        "user_id": "10001",
        "video_inputs": [b"injected-video"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": _data_url("video/webm", b"message-video")}},
                ],
            },
        ],
    }

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return mod.VideoGenerationResult(raw=b"generated-video")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    await mod.get_video("extend it", input_type="video", state=state)

    assert captured["image"] is None
    assert captured["video"] == mod.MediaReference(data=b"injected-video", mime_type="video/mp4")


@pytest.mark.asyncio
async def test_get_video_image_input_without_image_fails_before_service_call(load_tool_module, monkeypatch):
    mod = load_tool_module("video")

    async def fake_generate_video(_prompt, *, image=None, video=None):
        raise AssertionError("generate_video should not be called without image input")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_video(
        "make this move", input_type="image", state={"user_id": "10001", "messages": []}
    )

    assert "没有可用的图片" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_get_video_video_input_without_video_fails_before_service_call(load_tool_module, monkeypatch):
    mod = load_tool_module("video")

    async def fake_generate_video(_prompt, *, image=None, video=None):
        raise AssertionError("generate_video should not be called without video input")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)

    text, artifact = await mod.get_video("extend it", input_type="video", state={"user_id": "10001", "messages": []})

    assert "没有可用的视频" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_get_video_respects_disabled_module(load_tool_module, monkeypatch):
    mod = load_tool_module("video")

    async def fake_generate_video(_prompt):
        raise AssertionError("generate_video should not be called while disabled")

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", False, raising=False)

    text, artifact = await mod.get_video("a happy horse", state={"user_id": "10001"})

    assert "视频功能没开" in text
    assert artifact is None


@pytest.mark.asyncio
async def test_get_video_rate_limits_by_injected_user_id(load_tool_module, monkeypatch):
    mod = load_tool_module("video")

    async def fake_generate_video(_prompt):
        raise AssertionError("generate_video should not be called while rate limited")

    class DenyLimiter:
        def check(self, user_id, *, now, max_requests, window_seconds):
            assert user_id == "10001"
            assert max_requests == 1
            assert window_seconds == 900
            return mod.PaintRateLimitResult(False, 120)

    monkeypatch.setattr(mod, "generate_video", fake_generate_video)
    monkeypatch.setattr(mod, "video_rate_limiter", DenyLimiter())
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_MODULE_ENABLED", True, raising=False)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_RATE_LIMIT_MAX_REQUESTS", 1, raising=False)
    monkeypatch.setattr(mod.EnvConfig, "VIDEO_RATE_LIMIT_WINDOW_SECONDS", 900, raising=False)

    text, artifact = await mod.get_video("a happy horse", state={"user_id": "10001"})

    assert "视频生成得太快了" in text
    assert "120 秒后再试" in text
    assert artifact is None


def test_get_video_tool_schema_hides_injected_state(load_tool_module):
    mod = load_tool_module("video")
    args = getattr(mod.get_video, "args", {})

    assert "prompt" in args
    assert "input_type" in args
    assert "state" not in args
