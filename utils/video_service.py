import asyncio
import base64
import binascii
import inspect
from dataclasses import dataclass

from nonebot import logger
from openai import AsyncOpenAI

from utils.configs import EnvConfig, get_provider_profile
from utils.http_client import get_http_client

httpx_client = get_http_client("video_service")


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


def _file_tuple(reference: MediaReference, *, stem: str) -> tuple[str, bytes, str]:
    extension = {
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "video/webm": "webm",
        "video/x-msvideo": "avi",
    }.get(reference.mime_type, "mp4" if reference.mime_type.startswith("video/") else "jpg")
    return f"{stem}.{extension}", reference.data, reference.mime_type


def _build_openai_client() -> AsyncOpenAI:
    profile = get_provider_profile(EnvConfig.VIDEO_MODEL_PROVIDER)
    if str(profile.get("type", "")).strip().lower() != "openai":
        raise ValueError("video_model_provider 必须引用 type = 'openai' 的 provider")
    kwargs = {"api_key": str(profile.get("api_key", ""))}
    if base_url := str(profile.get("base_url", "")).strip():
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def _video_create_options() -> dict[str, str]:
    options: dict[str, str] = {"model": EnvConfig.VIDEO_MODEL}
    if size := str(EnvConfig.VIDEO_SIZE).strip():
        options["size"] = size
    if seconds := str(EnvConfig.VIDEO_SECONDS).strip():
        options["seconds"] = seconds
    return options


async def _create_video_job(
    client: AsyncOpenAI,
    prompt: str,
    *,
    image: MediaReference | bytes | None,
    video: MediaReference | bytes | None,
):
    video_ref = _coerce_media_reference(
        video,
        default_mime_type=_guess_video_mime_type(video) if isinstance(video, bytes) else "video/mp4",
    )
    if video_ref is not None:
        return await client.videos.edit(prompt=prompt, video=_file_tuple(video_ref, stem="reference"))

    image_ref = _coerce_media_reference(
        image,
        default_mime_type=_guess_image_mime_type(image) if isinstance(image, bytes) else "image/jpeg",
    )
    options = _video_create_options()
    if image_ref is not None:
        options["input_reference"] = _file_tuple(image_ref, stem="reference")
    return await client.videos.create(prompt=prompt, **options)


async def _poll_video_job(client: AsyncOpenAI, job):
    timeout_seconds = EnvConfig.VIDEO_POLL_TIMEOUT_SECONDS
    deadline = None if timeout_seconds <= 0 else asyncio.get_running_loop().time() + timeout_seconds

    while getattr(job, "status", None) in {"queued", "in_progress"}:
        if deadline is not None and asyncio.get_running_loop().time() >= deadline:
            logger.warning(f"OpenAI 视频生成超时: timeout={timeout_seconds}s")
            return None
        await asyncio.sleep(max(0, EnvConfig.VIDEO_POLL_INTERVAL_SECONDS))
        job = await client.videos.retrieve(job.id)

    if getattr(job, "status", None) != "completed":
        error = getattr(job, "error", None) or getattr(job, "last_error", None)
        logger.warning(f"OpenAI 视频生成失败: status={getattr(job, 'status', None)}, error={error}")
        return None
    return job


async def _binary_response_bytes(response) -> bytes | None:
    if isinstance(response, bytes):
        return response
    if isinstance(response, bytearray):
        return bytes(response)

    read = getattr(response, "read", None)
    if callable(read):
        content = read()
        if inspect.isawaitable(content):
            content = await content
        if isinstance(content, bytes):
            return content

    content = getattr(response, "content", None)
    if isinstance(content, bytes):
        return content
    return None


async def _video_result(client: AsyncOpenAI, job) -> VideoGenerationResult | None:
    try:
        response = await client.videos.download_content(job.id)
        if raw := await _binary_response_bytes(response):
            return VideoGenerationResult(raw=raw)
    except Exception as exc:
        logger.warning(f"下载 OpenAI 视频内容失败: {exc}")

    if encoded := getattr(job, "b64_json", None):
        try:
            return VideoGenerationResult(raw=base64.b64decode(encoded, validate=True))
        except (binascii.Error, ValueError):
            logger.warning("OpenAI 视频 API 返回了无效的 base64 内容")

    for field in ("url", "download_url"):
        url = getattr(job, field, None)
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            try:
                response = await httpx_client.get(url)
                response.raise_for_status()
                return VideoGenerationResult(raw=await response.aread())
            except Exception as exc:
                logger.warning(f"下载 OpenAI 视频 URL 失败: {exc}")
                return VideoGenerationResult(url=url)

    logger.warning("OpenAI 视频 API 响应缺少可发送的视频内容")
    return None


async def generate_video(
    prompt: str,
    *,
    image: MediaReference | bytes | None = None,
    video: MediaReference | bytes | None = None,
) -> VideoGenerationResult | None:
    if not EnvConfig.VIDEO_MODEL:
        logger.warning("VIDEO_MODEL 未配置，视频请求失败")
        return None

    logger.info(f"🎬 调用 OpenAI 视频 API, model={EnvConfig.VIDEO_MODEL}, prompt_length={len(prompt)}")
    client: AsyncOpenAI | None = None
    try:
        client = _build_openai_client()
        job = await _create_video_job(client, prompt, image=image, video=video)
        if completed := await _poll_video_job(client, job):
            return await _video_result(client, completed)
        return None
    except Exception as exc:
        logger.exception(f"💥 调用 OpenAI 视频 API 失败: {exc}")
        return None
    finally:
        if client is not None:
            await client.close()
