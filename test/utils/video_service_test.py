# ruff: noqa: S101

from types import SimpleNamespace

from pydantic import SecretStr

from utils import video_service


class DummyHttpOptions:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyImage:
    def __init__(self, *, image_bytes, mime_type):
        self.image_bytes = image_bytes
        self.mime_type = mime_type


class DummyVideo:
    def __init__(self, *, video_bytes, mime_type):
        self.video_bytes = video_bytes
        self.mime_type = mime_type


class DummyGenerateVideosSource:
    def __init__(self, *, prompt=None, image=None, video=None):
        self.prompt = prompt
        self.image = image
        self.video = video


def _dummy_genai_types():
    return SimpleNamespace(
        HttpOptions=DummyHttpOptions,
        Image=DummyImage,
        Video=DummyVideo,
        GenerateVideosSource=DummyGenerateVideosSource,
    )


def test_generate_video_uses_happyhorse_vertex_gateway(monkeypatch):
    calls = {}

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

    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_MODEL", "alibaba/happyhorse-1.0", raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_BASE_URL", "https://zenmux.ai/api/vertex-ai", raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_API_KEY", SecretStr("sk-video"), raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_INTERVAL_SECONDS", 0, raising=False)
    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_TIMEOUT_SECONDS", 30, raising=False)
    monkeypatch.setattr(video_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(video_service, "genai_types", _dummy_genai_types())

    result = video_service._generate_video_sync("a happy horse")

    assert result == video_service.VideoGenerationResult(raw=b"happyhorse-video")
    assert calls["client"]["api_key"] == "sk-video"
    assert calls["client"]["vertexai"] is True
    assert calls["client"]["http_options"].kwargs == {
        "api_version": "v1",
        "base_url": "https://zenmux.ai/api/vertex-ai",
    }
    assert calls["generate_videos"]["model"] == "alibaba/happyhorse-1.0"
    source = calls["generate_videos"]["source"]
    assert source.prompt == "a happy horse"
    assert source.image is None
    assert source.video is None
    assert calls["closed"] is True


def test_generate_video_uses_image_source(monkeypatch):
    calls = {}

    class DummyModels:
        def generate_videos(self, **kwargs):
            calls["generate_videos"] = kwargs
            video = SimpleNamespace(video_bytes=b"image-video")
            return SimpleNamespace(
                done=True,
                result=SimpleNamespace(generated_videos=[SimpleNamespace(video=video)]),
            )

    class DummyClient:
        def __init__(self, **_kwargs):
            self.models = DummyModels()

        def close(self):
            return None

    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_TIMEOUT_SECONDS", 30, raising=False)
    monkeypatch.setattr(video_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(video_service, "genai_types", _dummy_genai_types())

    result = video_service._generate_video_sync(
        "animate this",
        image=video_service.MediaReference(data=b"image-bytes", mime_type="image/png"),
    )

    assert result == video_service.VideoGenerationResult(raw=b"image-video")
    source = calls["generate_videos"]["source"]
    assert source.prompt == "animate this"
    assert source.image.image_bytes == b"image-bytes"
    assert source.image.mime_type == "image/png"
    assert source.video is None


def test_generate_video_uses_video_source(monkeypatch):
    calls = {}

    class DummyModels:
        def generate_videos(self, **kwargs):
            calls["generate_videos"] = kwargs
            video = SimpleNamespace(video_bytes=b"extended-video")
            return SimpleNamespace(
                done=True,
                result=SimpleNamespace(generated_videos=[SimpleNamespace(video=video)]),
            )

    class DummyClient:
        def __init__(self, **_kwargs):
            self.models = DummyModels()

        def close(self):
            return None

    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_TIMEOUT_SECONDS", 30, raising=False)
    monkeypatch.setattr(video_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(video_service, "genai_types", _dummy_genai_types())

    result = video_service._generate_video_sync(
        "extend this",
        video=video_service.MediaReference(data=b"video-bytes", mime_type="video/mp4"),
    )

    assert result == video_service.VideoGenerationResult(raw=b"extended-video")
    source = calls["generate_videos"]["source"]
    assert source.prompt == "extend this"
    assert source.image is None
    assert source.video.video_bytes == b"video-bytes"
    assert source.video.mime_type == "video/mp4"


def test_video_result_from_generated_video_uses_http_url():
    result = video_service._video_result_from_generated_video(
        SimpleNamespace(),
        SimpleNamespace(video=SimpleNamespace(uri="https://example.com/video.mp4")),
    )

    assert result == video_service.VideoGenerationResult(url="https://example.com/video.mp4")


def test_get_video_operation_supports_older_sdk_method():
    operation = SimpleNamespace(name="operations/123")
    updated_operation = SimpleNamespace(done=True)

    class DummyOperations:
        def get_videos_operation(self, *, operation):
            assert operation.name == "operations/123"
            return updated_operation

    result = video_service._get_video_operation(SimpleNamespace(operations=DummyOperations()), operation)

    assert result is updated_operation


def test_generate_video_returns_none_on_failed_operation(monkeypatch):
    class DummyModels:
        def generate_videos(self, **_kwargs):
            return SimpleNamespace(done=True, error="blocked")

    class DummyClient:
        def __init__(self, **_kwargs):
            self.models = DummyModels()

        def close(self):
            return None

    monkeypatch.setattr(video_service.EnvConfig, "VIDEO_POLL_TIMEOUT_SECONDS", 30, raising=False)
    monkeypatch.setattr(video_service, "genai", SimpleNamespace(Client=DummyClient))
    monkeypatch.setattr(video_service, "genai_types", _dummy_genai_types())

    result = video_service._generate_video_sync("a failed horse")

    assert result is None
