import base64
import inspect
import io
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from urllib.parse import quote

import httpx
from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError
from nonebot import logger
from openai import AsyncClient
from PIL import Image

from utils.configs import EnvConfig


@dataclass(frozen=True)
class PaintRateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0


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


def _normalize_reference_image(image: bytes) -> bytes:
    with Image.open(io.BytesIO(image)) as raw_image:
        mode = "RGBA" if "A" in raw_image.getbands() else "RGB"
        normalized = raw_image.convert(mode)
        with io.BytesIO() as png_bytes:
            normalized.save(png_bytes, format="PNG")
            return png_bytes.getvalue()


def _prepare_reference_image(image: bytes, index: int) -> tuple[str, bytes, str]:
    png_bytes = _normalize_reference_image(image)
    return (f"reference-{index}.png", png_bytes, "image/png")


def _paint_base_url() -> str:
    return EnvConfig.PAINT_BASE_URL


def _paint_api_key() -> str:
    return EnvConfig.PAINT_API_KEY.get_secret_value()


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
                return None
        else:
            try:
                response = await client.aio.models.generate_images(
                    model=EnvConfig.PAINT_MODEL,
                    prompt=prompt,
                )
            except ClientError:
                return None
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


POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt"
POLLINATIONS_FALLBACK_MODEL = "flux"


async def _paint_with_pollinations(prompt: str) -> bytes | None:
    encoded_prompt = quote(prompt, safe="")
    url = f"{POLLINATIONS_IMAGE_URL}/{encoded_prompt}"
    params = {
        "model": POLLINATIONS_FALLBACK_MODEL,
        "nologo": "true",
        "width": 1024,
        "height": 1024,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            logger.warning(f"Pollinations fallback API 返回非 200: {response.status_code}")
            return None
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type:
            logger.warning(f"Pollinations fallback 返回非图片内容: {content_type}")
            return None
        return response.content


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    reference_images = reference_images or []

    if not EnvConfig.PAINT_MODEL:
        if reference_images:
            logger.warning("Pollinations 不支持参考图片，跳过")
            return None
        logger.info(f"🎨 PAINT_MODEL 未配置，使用 Pollinations ({POLLINATIONS_FALLBACK_MODEL})")
        try:
            result = await _paint_with_pollinations(prompt)
            if result:
                logger.info("✅ Pollinations 绘图成功")
            return result
        except Exception as e:
            logger.exception(f"💥 Pollinations 绘图失败: {e}")
            return None

    logger.info(
        f"🎨 调用 GPT Image API, model={EnvConfig.PAINT_MODEL}, prompt_length={len(prompt)}, references={len(reference_images)}"
    )

    try:
        if _use_vertex_image_gateway():
            return await _paint_with_vertex_gateway(prompt, reference_images)
        return await _paint_with_openai_images(prompt, reference_images)
    except Exception as e:
        logger.exception(f"💥 调用 GPT Image API 失败: {e}")
        return None
