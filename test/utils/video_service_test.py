# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from utils import video_service


def _set_video_config(monkeypatch) -> None:
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_MODEL", "sora-test", raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_MODEL_PROVIDER", "media", raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_SIZE", "1280x720", raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_SECONDS", "8", raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_INTERVAL_SECONDS", 0, raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_TIMEOUT_SECONDS", 30, raising=False)
    monkeypatch.setattr(
        video_service,
        "get_provider_profile",
        lambda name: {
            "type": "openai",
            "base_url": "https://media.example.com/v1",
            "api_key": "sk-video",
        }
        if name == "media"
        else None,
    )


class DummyBinaryResponse:
    def __init__(self, data: bytes):
        self.data = data

    async def read(self):
        return self.data


@pytest.mark.asyncio
async def test_generate_video_creates_polls_and_downloads(monkeypatch):
    calls = {}

    class DummyVideos:
        async def create(self, **kwargs):
            calls["create"] = kwargs
            return SimpleNamespace(id="video_123", status="queued")

        async def retrieve(self, video_id):
            calls["retrieve"] = video_id
            return SimpleNamespace(id=video_id, status="completed")

        async def download_content(self, video_id):
            calls["download"] = video_id
            return DummyBinaryResponse(b"generated-video")

    class DummyClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.videos = DummyVideos()

        async def close(self):
            calls["closed"] = True

    _set_video_config(monkeypatch)
    monkeypatch.setattr(video_service, "AsyncOpenAI", DummyClient)

    result = await video_service.generate_video("a happy horse")

    assert result == video_service.VideoGenerationResult(raw=b"generated-video")
    assert calls["client"] == {"api_key": "sk-video", "base_url": "https://media.example.com/v1"}
    assert calls["create"] == {
        "prompt": "a happy horse",
        "model": "sora-test",
        "size": "1280x720",
        "seconds": "8",
    }
    assert calls["retrieve"] == "video_123"
    assert calls["download"] == "video_123"
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_generate_video_uses_image_reference(monkeypatch):
    calls = {}

    class DummyVideos:
        async def create(self, **kwargs):
            calls["create"] = kwargs
            return SimpleNamespace(id="video_image", status="completed")

        async def download_content(self, _video_id):
            return DummyBinaryResponse(b"image-video")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.videos = DummyVideos()

        async def close(self):
            return None

    _set_video_config(monkeypatch)
    monkeypatch.setattr(video_service, "AsyncOpenAI", DummyClient)

    result = await video_service.generate_video(
        "animate this",
        image=video_service.MediaReference(data=b"image-bytes", mime_type="image/png"),
    )

    assert result == video_service.VideoGenerationResult(raw=b"image-video")
    reference = calls["create"]["input_reference"]
    assert reference == ("reference.png", b"image-bytes", "image/png")


@pytest.mark.asyncio
async def test_generate_video_uses_edit_endpoint_for_video_reference(monkeypatch):
    calls = {}

    class DummyVideos:
        async def edit(self, **kwargs):
            calls["edit"] = kwargs
            return SimpleNamespace(id="video_edit", status="completed")

        async def download_content(self, _video_id):
            return DummyBinaryResponse(b"edited-video")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.videos = DummyVideos()

        async def close(self):
            return None

    _set_video_config(monkeypatch)
    monkeypatch.setattr(video_service, "AsyncOpenAI", DummyClient)

    result = await video_service.generate_video(
        "extend this",
        video=video_service.MediaReference(data=b"video-bytes", mime_type="video/mp4"),
    )

    assert result == video_service.VideoGenerationResult(raw=b"edited-video")
    assert calls["edit"] == {
        "prompt": "extend this",
        "video": ("reference.mp4", b"video-bytes", "video/mp4"),
    }


@pytest.mark.asyncio
async def test_generate_video_returns_none_for_failed_job(monkeypatch):
    class DummyVideos:
        async def create(self, **_kwargs):
            return SimpleNamespace(id="video_failed", status="failed", error="blocked")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.videos = DummyVideos()

        async def close(self):
            return None

    _set_video_config(monkeypatch)
    monkeypatch.setattr(video_service, "AsyncOpenAI", DummyClient)

    assert await video_service.generate_video("a failed horse") is None


@pytest.mark.asyncio
async def test_generate_video_falls_back_to_result_url(monkeypatch):
    class DummyVideos:
        async def create(self, **_kwargs):
            return SimpleNamespace(id="video_url", status="completed", url="https://cdn.example.com/video.mp4")

        async def download_content(self, _video_id):
            raise RuntimeError("content endpoint unavailable")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.videos = DummyVideos()

        async def close(self):
            return None

    class DummyHttpClient:
        async def get(self, url):
            assert url == "https://cdn.example.com/video.mp4"
            raise RuntimeError("cdn unavailable")

    _set_video_config(monkeypatch)
    monkeypatch.setattr(video_service, "AsyncOpenAI", DummyClient)
    monkeypatch.setattr(video_service, "httpx_client", DummyHttpClient())

    assert await video_service.generate_video("a video") == video_service.VideoGenerationResult(
        url="https://cdn.example.com/video.mp4"
    )


@pytest.mark.asyncio
async def test_generate_video_returns_none_when_model_empty(monkeypatch):
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_MODEL", "", raising=False)

    assert await video_service.generate_video("a video") is None
