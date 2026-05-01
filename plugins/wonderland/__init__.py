import asyncio
import base64
import inspect
import io
import math
import os
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError
from nonebot import get_bot, logger, on_command, require
from nonebot.adapters.milky.event import MessageEvent
from openai import AsyncClient
from PIL import Image

from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.message import message_extract
from utils.reply_context import build_reply_context, reply_seq_from_segments, strip_reply_marker

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})
videographer = on_command("video", priority=3, block=True, aliases={"视频"})
PAINT_COMMAND_PREFIXES = ("帮我画一张图", "画一张图", "画图", "绘图", "paint")
VIDEO_COMMAND_PREFIXES = ("video", "视频")
messages_db = MessageDatabase()


@dataclass(frozen=True)
class PaintRateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0


@dataclass(frozen=True)
class VideoGenerationResult:
    raw: bytes | None = None
    url: str | None = None


class PaintRateLimiter:
    def __init__(self):
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(
        self,
        user_id: str,
        *,
        now: float,
        max_requests: int,
        window_seconds: int,
    ) -> PaintRateLimitResult:
        if max_requests <= 0 or window_seconds <= 0:
            return PaintRateLimitResult(True, 0)

        requests = self._requests[user_id]
        cutoff = now - window_seconds
        while requests and requests[0] <= cutoff:
            requests.popleft()

        if len(requests) >= max_requests:
            retry_after = max(1, math.ceil(window_seconds - (now - requests[0])))
            return PaintRateLimitResult(False, retry_after)

        requests.append(now)
        return PaintRateLimitResult(True, 0)


paint_rate_limiter = PaintRateLimiter()
video_rate_limiter = PaintRateLimiter()


@painter.handle()
async def handle_painter(event: MessageEvent):
    if EnvConfig.PAINT_MODULE_ENABLED is False:
        await painter.finish("么得画了，等升级哇!")
    text, images, *_ = await message_extract(event.data.segments)
    quoted_images: list[bytes] = []
    if reply_seq := reply_seq_from_segments(event.data.segments):
        group_id = event.data.group.group_id if event.data.group else None
        quote_text, quoted_images = await build_reply_context(get_bot(), event, reply_seq, group_id, messages_db)
        text = strip_reply_marker(text, reply_seq)
        if quote_text:
            text += quote_text
    prompt = strip_paint_prompt(text)
    reference_images = quoted_images + images
    if not prompt:
        tip = "你想怎么修改这张图？" if reference_images else "你想画点什么？"
        await UniMessage.text(tip).send()
        return
    rate_limit = paint_rate_limiter.check(
        event.get_user_id(),
        now=time.time(),
        max_requests=EnvConfig.PAINT_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.PAINT_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        await UniMessage.text(f"画得太快了，{rate_limit.retry_after_seconds} 秒后再试吧").send()
        return
    image = await paint(prompt, reference_images)
    if image:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.image(raw=image)).send()
    else:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.text("图被肥猫吃了，画不了嘞")).send()


@videographer.handle()
async def handle_video(event: MessageEvent):
    if EnvConfig.VIDEO_MODULE_ENABLED is False:
        await videographer.finish("视频功能没开")

    text, *_ = await message_extract(event.data.segments)
    prompt = strip_video_prompt(text)
    if not prompt:
        await UniMessage.text("你想生成什么视频？").send()
        return

    rate_limit = video_rate_limiter.check(
        event.get_user_id(),
        now=time.time(),
        max_requests=EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        await UniMessage.text(f"视频生成得太快了，{rate_limit.retry_after_seconds} 秒后再试吧").send()
        return

    video = await generate_video(prompt)
    video_message = _video_result_message(video)
    if video_message:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.text("视频生成OK了")).send()
        await video_message.send()
    else:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.text("视频生成失败了")).send()


def strip_paint_prompt(text: str) -> str:
    stripped = text.strip()
    for prefix in PAINT_COMMAND_PREFIXES:
        boundary = r"(?:\b|\s+|$)" if prefix.isascii() else ""
        pattern = rf"^/?{re.escape(prefix)}{boundary}"
        if re.match(pattern, stripped, flags=re.IGNORECASE):
            return re.sub(pattern, "", stripped, count=1, flags=re.IGNORECASE).strip()
    return stripped


def strip_video_prompt(text: str) -> str:
    stripped = text.strip()
    for prefix in VIDEO_COMMAND_PREFIXES:
        boundary = r"(?:\b|\s+|$)" if prefix.isascii() else ""
        pattern = rf"^/?{re.escape(prefix)}{boundary}"
        if re.match(pattern, stripped, flags=re.IGNORECASE):
            return re.sub(pattern, "", stripped, count=1, flags=re.IGNORECASE).strip()
    return stripped


def _prepare_reference_image(image: bytes, index: int) -> tuple[str, bytes, str]:
    png_bytes = _normalize_reference_image(image)
    return (f"reference-{index}.png", png_bytes, "image/png")


def _normalize_reference_image(image: bytes) -> bytes:
    with Image.open(io.BytesIO(image)) as raw_image:
        mode = "RGBA" if "A" in raw_image.getbands() else "RGB"
        normalized = raw_image.convert(mode)
        with io.BytesIO() as png_bytes:
            normalized.save(png_bytes, format="PNG")
            return png_bytes.getvalue()


def _paint_base_url() -> str:
    return EnvConfig.PAINT_BASE_URL


def _paint_api_key() -> str:
    return EnvConfig.PAINT_API_KEY.get_secret_value()


def _video_base_url() -> str:
    return EnvConfig.VIDEO_BASE_URL


def _video_api_key() -> str:
    configured_key = EnvConfig.VIDEO_API_KEY.get_secret_value()
    return configured_key or os.getenv("ZENMUX_API_KEY", "")


def _use_vertex_image_gateway() -> bool:
    return "vertex-ai" in _paint_base_url().lower()


def _openai_client_kwargs() -> dict[str, str]:
    return {
        "api_key": _paint_api_key(),
        "base_url": _paint_base_url(),
    }


async def _paint_with_openai_images(prompt: str, reference_images: list[bytes]) -> bytes | None:
    client = AsyncClient(**_openai_client_kwargs())
    request = {
        "model": EnvConfig.PAINT_MODEL,
        "prompt": prompt,
        "response_format": "b64_json",
    }

    if reference_images:
        payload = [_prepare_reference_image(image, idx) for idx, image in enumerate(reference_images, start=1)]
        response = await client.images.edit(image=payload, **request)
    else:
        response = await client.images.generate(**request)

    if not response.data:
        logger.warning("绘图API返回空 data")
        return None

    image_b64 = getattr(response.data[0], "b64_json", None)
    if not image_b64:
        logger.warning("绘图API响应缺少 b64_json 字段")
        return None

    return base64.b64decode(image_b64)


async def _paint_with_vertex_gateway(prompt: str, reference_images: list[bytes]) -> bytes | None:
    client = genai.Client(
        api_key=_paint_api_key(),
        vertexai=True,
        http_options=genai_types.HttpOptions(api_version="v1", base_url=_paint_base_url()),
    )
    try:
        if reference_images:
            payload = [
                genai_types.RawReferenceImage(
                    reference_id=idx,
                    reference_image=genai_types.Image(
                        image_bytes=_normalize_reference_image(image),
                        mime_type="image/png",
                    ),
                )
                for idx, image in enumerate(reference_images, start=1)
            ]
            try:
                response = await client.aio.models.edit_image(
                    model=EnvConfig.PAINT_MODEL,
                    prompt=prompt,
                    reference_images=payload,
                )
            except ClientError:
                return
        else:
            try:
                response = await client.aio.models.generate_images(
                    model=EnvConfig.PAINT_MODEL,
                    prompt=prompt,
                )
            except ClientError:
                return
    finally:
        aio_client = getattr(client, "aio", None)
        aclose = getattr(aio_client, "aclose", None)
        if callable(aclose):
            maybe_awaitable = aclose()
            if inspect.isawaitable(maybe_awaitable):
                await maybe_awaitable

        close = getattr(client, "close", None)
        if callable(close):
            maybe_awaitable = close()
            if inspect.isawaitable(maybe_awaitable):
                await maybe_awaitable

    generated_images = getattr(response, "generated_images", None) or []
    if not generated_images:
        logger.warning("Vertex 图片API返回空 generated_images")
        return None

    image = getattr(generated_images[0], "image", None)
    image_bytes = getattr(image, "image_bytes", None)
    if not image_bytes:
        logger.warning("Vertex 图片API响应缺少 image_bytes 字段")
        return None

    return image_bytes


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    reference_images = reference_images or []
    logger.info(
        f"🎨 调用 GPT Image API, model={EnvConfig.PAINT_MODEL}, prompt_length={len(prompt)}, references={len(reference_images)}"
    )

    try:
        if _use_vertex_image_gateway():
            return await _paint_with_vertex_gateway(prompt, reference_images)
        else:
            return await _paint_with_openai_images(prompt, reference_images)
    except Exception as e:
        logger.exception(f"💥 调用 GPT Image API 失败: {e}")
        return None


def _video_result_message(video: VideoGenerationResult | None):
    if video is None:
        return None
    if video.raw:
        return UniMessage.video(raw=video.raw)
    if video.url:
        return UniMessage.video(url=video.url)
    return None


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


def _video_operation_response(operation):
    return getattr(operation, "response", None) or getattr(operation, "result", None)


def _close_genai_client(client) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        maybe_awaitable = close()
        if inspect.isawaitable(maybe_awaitable):
            logger.debug("google genai sync client close returned awaitable; ignored in worker thread")


def _generate_video_sync(prompt: str) -> VideoGenerationResult | None:
    client = genai.Client(
        api_key=_video_api_key(),
        vertexai=True,
        http_options=genai_types.HttpOptions(api_version="v1", base_url=_video_base_url()),
    )
    try:
        operation = client.models.generate_videos(
            model=EnvConfig.VIDEO_MODEL,
            prompt=prompt,
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

        response = _video_operation_response(operation)
        generated_videos = getattr(response, "generated_videos", None) or []
        if not generated_videos:
            logger.warning("HappyHorse 视频API返回空 generated_videos")
            return None

        return _video_result_from_generated_video(client, generated_videos[0])
    finally:
        _close_genai_client(client)


async def generate_video(prompt: str) -> VideoGenerationResult | None:
    logger.info(f"🎬 调用 HappyHorse 视频API, model={EnvConfig.VIDEO_MODEL}, prompt_length={len(prompt)}")

    try:
        return await asyncio.to_thread(_generate_video_sync, prompt)
    except Exception as e:
        logger.exception(f"💥 调用 HappyHorse 视频API失败: {e}")
        return None
