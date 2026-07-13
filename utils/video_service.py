import asyncio
import base64
import inspect
import os
import time
from dataclasses import dataclass

from google import genai
from google.genai import types as genai_types
from nonebot import logger

from utils.configs import EnvConfig


@dataclass(frozen=True)
class VideoGenerationResult:
    raw: bytes | None = None
    url: str | None = None


@dataclass(frozen=True)
class MediaReference:
    data: bytes
    mime_type: str


def _guess_image_mime_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _guess_video_mime_type(data: bytes) -> str:
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "video/mp4"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return "video/webm"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return "video/x-msvideo"
    return "video/mp4"


def _coerce_media_reference(value: MediaReference | bytes | None, *, default_mime_type: str) -> MediaReference | None:
    if value is None:
        return None
    if isinstance(value, MediaReference):
        return value
    return MediaReference(data=value, mime_type=default_mime_type)


def _generate_video_source(
    prompt: str,
    *,
    image: MediaReference | bytes | None,
    video: MediaReference | bytes | None,
):
    video_ref = _coerce_media_reference(
        video,
        default_mime_type=_guess_video_mime_type(video) if isinstance(video, bytes) else "video/mp4",
    )
    image_ref = (
        None
        if video_ref
        else _coerce_media_reference(
            image,
            default_mime_type=_guess_image_mime_type(image) if isinstance(image, bytes) else "image/jpeg",
        )
    )
    return genai_types.GenerateVideosSource(
        prompt=prompt,
        image=genai_types.Image(image_bytes=image_ref.data, mime_type=image_ref.mime_type) if image_ref else None,
        video=genai_types.Video(video_bytes=video_ref.data, mime_type=video_ref.mime_type) if video_ref else None,
    )


def _coerce_video_bytes(value) -> bytes | None:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str) and not _is_http_url(value):
        try:
            return base64.b64decode(value, validate=True)
        except Exception:
            return None
    return None


def _extract_video_bytes(*objects) -> bytes | None:
    for obj in objects:
        if obj is None:
            continue
        if raw := _coerce_video_bytes(obj):
            return raw
        for field in ("video_bytes", "bytes", "data", "content", "b64_json", "base64"):
            if raw := _coerce_video_bytes(getattr(obj, field, None)):
                return raw
    return None


def _is_http_url(value: str | None) -> bool:
    return bool(value and value.startswith(("http://", "https://")))


def _extract_video_url(*objects) -> str | None:
    for obj in objects:
        if isinstance(obj, str) and _is_http_url(obj):
            return obj
        if obj is None:
            continue
        for field in ("url", "uri", "download_url", "download_uri"):
            value = getattr(obj, field, None)
            if isinstance(value, str) and _is_http_url(value):
                return value
    return None


def _download_video_bytes(client, *objects) -> bytes | None:
    files = getattr(client, "files", None)
    download = getattr(files, "download", None)
    if not callable(download):
        return None

    for obj in objects:
        if obj is None:
            continue
        try:
            downloaded = download(file=obj)
        except TypeError:
            downloaded = download(obj)
        except Exception as e:
            logger.warning(f"下载视频结果失败: {e}")
            continue
        if raw := _extract_video_bytes(downloaded):
            return raw
    return None


def _video_result_from_generated_video(client, generated_video) -> VideoGenerationResult | None:
    video = getattr(generated_video, "video", None)
    if raw := _extract_video_bytes(generated_video, video):
        return VideoGenerationResult(raw=raw)
    if raw := _download_video_bytes(client, video, generated_video):
        return VideoGenerationResult(raw=raw)
    if url := _extract_video_url(generated_video, video):
        return VideoGenerationResult(url=url)
    logger.warning("HappyHorse 视频API响应缺少可发送的视频内容")
    return None


def _get_video_operation(client, operation):
    operations = getattr(client, "operations", None)
    if operations is None:
        raise AttributeError("google genai client has no operations API")

    get_videos_operation = getattr(operations, "get_videos_operation", None)
    if callable(get_videos_operation):
        try:
            return get_videos_operation(operation=operation)
        except TypeError:
            return get_videos_operation(operation)

    get_operation = getattr(operations, "get", None)
    if callable(get_operation):
        try:
            return get_operation(operation=operation)
        except TypeError:
            return get_operation(operation)

    raise AttributeError("google genai operations API has no supported polling method")


def _close_genai_client(client) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        maybe_awaitable = close()
        if inspect.isawaitable(maybe_awaitable):
            logger.debug("google genai sync client close returned awaitable; ignored in worker thread")


def _generate_video_sync(
    prompt: str,
    *,
    image: MediaReference | bytes | None = None,
    video: MediaReference | bytes | None = None,
) -> VideoGenerationResult | None:
    configured_key = EnvConfig.VIDEO_API_KEY.get_secret_value()
    client = genai.Client(
        api_key=configured_key or os.getenv("ZENMUX_API_KEY", ""),
        vertexai=True,
        http_options=genai_types.HttpOptions(api_version="v1", base_url=EnvConfig.VIDEO_BASE_URL),
    )
    try:
        operation = client.models.generate_videos(
            model=EnvConfig.VIDEO_MODEL,
            source=_generate_video_source(prompt, image=image, video=video),
        )
        timeout_seconds = EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS
        deadline = None if timeout_seconds <= 0 else time.monotonic() + timeout_seconds

        while not operation.done:
            if deadline is not None and time.monotonic() >= deadline:
                logger.warning(f"HappyHorse 视频生成超时: timeout={timeout_seconds}s")
                return None
            time.sleep(max(0, EnvConfig.VIDEO_POLL_INTERVAL_SECONDS))
            operation = _get_video_operation(client, operation)

        if error := getattr(operation, "error", None):
            logger.warning(f"HappyHorse 视频生成失败: {error}")
            return None

        response = getattr(operation, "response", None) or getattr(operation, "result", None)
        generated_videos = getattr(response, "generated_videos", None) or []
        if not generated_videos:
            logger.warning("HappyHorse 视频API返回空 generated_videos")
            return None

        return _video_result_from_generated_video(client, generated_videos[0])
    finally:
        _close_genai_client(client)


async def generate_video(
    prompt: str,
    *,
    image: MediaReference | bytes | None = None,
    video: MediaReference | bytes | None = None,
) -> VideoGenerationResult | None:
    logger.info(f"🎬 调用 HappyHorse 视频API, model={EnvConfig.VIDEO_MODEL}, prompt_length={len(prompt)}")

    try:
        return await asyncio.to_thread(_generate_video_sync, prompt, image=image, video=video)
    except Exception as e:
        logger.exception(f"💥 调用 HappyHorse 视频API失败: {e}")
        return None
