import base64
import binascii
import io
import math
from collections import defaultdict, deque
from dataclasses import dataclass

from nonebot import logger
from openai import APIError, AsyncOpenAI
from PIL import Image

from utils.configs import EnvConfig, get_provider_profile
from utils.http_client import get_http_client

httpx_client = get_http_client("paint_service")


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


def _build_openai_client() -> AsyncOpenAI:
    profile = get_provider_profile(EnvConfig.PAINT_MODEL_PROVIDER)
    if str(profile.get("type", "")).strip().lower() != "openai":
        raise ValueError("paint_model_provider 必须引用 type = 'openai' 的 provider")
    kwargs = {"api_key": str(profile.get("api_key", ""))}
    if base_url := str(profile.get("base_url", "")).strip():
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def _image_request_options() -> dict[str, str]:
    options: dict[str, str] = {}
    if size := str(EnvConfig.PAINT_SIZE).strip():
        options["size"] = size
    if quality := str(EnvConfig.PAINT_QUALITY).strip():
        options["quality"] = quality
    return options


async def _image_bytes_from_response(response) -> bytes | None:
    data = getattr(response, "data", None) or []
    if not data:
        logger.warning("OpenAI 图片 API 返回空 data")
        return None

    image = data[0]
    if encoded := getattr(image, "b64_json", None):
        try:
            return base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            logger.warning("OpenAI 图片 API 返回了无效的 base64 图片")
            return None

    if url := getattr(image, "url", None):
        try:
            download = await httpx_client.get(url)
            download.raise_for_status()
            return await download.aread()
        except Exception as exc:
            logger.warning(f"下载 OpenAI 图片结果失败: {exc}")
            return None

    logger.warning("OpenAI 图片 API 响应中没有 b64_json 或 url")
    return None


async def _paint_with_openai(prompt: str, reference_images: list[bytes]) -> bytes | None:
    client = _build_openai_client()
    try:
        options = _image_request_options()
        if reference_images:
            images = [
                (f"reference_{index}.png", _normalize_reference_image(image), "image/png")
                for index, image in enumerate(reference_images)
            ]
            response = await client.images.edit(
                model=EnvConfig.PAINT_MODEL,
                image=images,
                prompt=prompt,
                **options,
            )
        else:
            response = await client.images.generate(
                model=EnvConfig.PAINT_MODEL,
                prompt=prompt,
                **options,
            )
        return await _image_bytes_from_response(response)
    except APIError as exc:
        logger.warning(f"OpenAI 图片 API 调用失败: {exc}")
        return None
    finally:
        await client.close()


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    reference_images = reference_images or []

    if not EnvConfig.PAINT_MODEL:
        logger.warning("PAINT_MODEL 未配置，绘画请求失败")
        return None

    logger.info(
        f"🎨 调用 OpenAI 图片 API, model={EnvConfig.PAINT_MODEL}, "
        f"prompt_length={len(prompt)}, references={len(reference_images)}"
    )

    try:
        return await _paint_with_openai(prompt, reference_images)
    except Exception as exc:
        logger.exception(f"💥 调用 OpenAI 图片 API 失败: {exc}")
        return None
