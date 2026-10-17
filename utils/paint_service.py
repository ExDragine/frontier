import base64
import binascii
import io
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from nonebot import logger
from openai import APIError, AsyncOpenAI
from openai.types.image_edit_params import ImageEditParamsNonStreaming
from openai.types.image_generate_params import ImageGenerateParamsNonStreaming
from openai.types.responses import EasyInputMessageParam, ResponseInputParam
from openai.types.responses.response_create_params import ResponseCreateParamsNonStreaming
from openai.types.responses.response_input_image_param import ResponseInputImageParam
from openai.types.responses.response_input_message_content_list_param import ResponseInputContentParam
from openai.types.responses.response_input_text_param import ResponseInputTextParam
from openai.types.responses.tool_choice_types_param import ToolChoiceTypesParam
from openai.types.responses.tool_param import ImageGeneration
from PIL import Image

from utils.configs import EnvConfig, get_provider_profile
from utils.http_client import get_http_client
from utils.markdown_media import PublicFetcher, failure_reason

_MAX_IMAGE_BYTES = 20_000_000


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
    api_key = str(profile.get("api_key", ""))
    base_url = str(profile.get("base_url", "")).strip()
    if base_url:
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    return AsyncOpenAI(api_key=api_key)


def _image_generation_tool(reference_images: list[bytes]) -> ImageGeneration:
    tool: ImageGeneration = {
        "type": "image_generation",
        "action": "edit" if reference_images else "generate",
        "model": EnvConfig.PAINT_MODEL,
        "output_format": "png",
    }
    if size := str(EnvConfig.PAINT_SIZE).strip():
        tool["size"] = size
    if quality := str(EnvConfig.PAINT_QUALITY).strip():
        tool["quality"] = cast(Literal["low", "medium", "high", "auto"], quality)
    return tool


def _responses_input(prompt: str, reference_images: list[bytes]) -> ResponseInputParam:
    content: list[ResponseInputContentParam] = [ResponseInputTextParam(type="input_text", text=prompt)]
    for image in reference_images:
        encoded = base64.b64encode(_normalize_reference_image(image)).decode("ascii")
        content.append(
            cast(
                ResponseInputImageParam,
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{encoded}",
                },
            )
        )
    return cast(ResponseInputParam, [EasyInputMessageParam(type="message", role="user", content=content)])


def _response_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _decode_image_base64(encoded: Any) -> bytes | None:
    if not isinstance(encoded, str) or not encoded.strip():
        return None
    encoded = encoded.strip()
    if encoded.startswith("data:"):
        _, separator, encoded = encoded.partition(",")
        if not separator:
            return None
    try:
        return base64.b64decode(encoded, validate=True) or None
    except (binascii.Error, ValueError):
        logger.warning("绘图 API 返回了无效的 base64 图片")
        return None


def _image_bytes_from_response(response: Any) -> bytes | None:
    output = _response_value(response, "output") or []
    for item in output:
        if _response_value(item, "type") != "image_generation_call":
            continue
        if image := _decode_image_base64(_response_value(item, "result")):
            return image

    logger.warning("Responses API 响应中没有 image_generation_call 结果")
    return None


async def _image_bytes_from_images_response(response: Any) -> bytes | None:
    for item in _response_value(response, "data") or []:
        if image := _decode_image_base64(_response_value(item, "b64_json")):
            return image
        url = _response_value(item, "url")
        if not isinstance(url, str) or not url:
            continue
        fetcher = PublicFetcher(
            get_http_client("paint_service"), Path("cache/paint"),
            fake_ip_fallback=EnvConfig.MESSAGE_MEDIA_FAKE_IP_FALLBACK,
        )
        try:
            image, _mime = await fetcher.get(url, limit=_MAX_IMAGE_BYTES)
            with Image.open(io.BytesIO(image)) as decoded:
                decoded.verify()
            return image
        except Exception as exc:
            # Signed image URLs and provider credentials must stay out of logs.
            logger.warning("下载生成图片失败: {}", failure_reason(exc))
    logger.warning("Images API 响应中没有可用的图片")
    return None


async def _paint_images(client: AsyncOpenAI, prompt: str, reference_images: list[bytes]) -> bytes | None:
    params = ImageGenerateParamsNonStreaming(
        model=EnvConfig.PAINT_MODEL, prompt=prompt, n=1, output_format="png", stream=False,
    )
    if size := str(EnvConfig.PAINT_SIZE).strip():
        params["size"] = size
    if quality := str(EnvConfig.PAINT_QUALITY).strip():
        params["quality"] = cast(Literal["low", "medium", "high", "auto", "xhigh", "max"], quality)
    if reference_images:
        images = [
            (f"reference-{index}.png", _normalize_reference_image(image), "image/png")
            for index, image in enumerate(reference_images, start=1)
        ]
        edit_params = cast(ImageEditParamsNonStreaming, {**params, "image": images})
        response = await client.images.edit(**edit_params)
    else:
        response = await client.images.generate(**params)
    return await _image_bytes_from_images_response(response)


async def _paint_responses(client: AsyncOpenAI, prompt: str, reference_images: list[bytes]) -> bytes | None:
    # Preserve the sub2api route, which rewrites the top-level image model to
    # its host model while leaving the image_generation tool model intact.
    params = ResponseCreateParamsNonStreaming(
        model=EnvConfig.PAINT_MODEL,
        input=_responses_input(prompt, reference_images),
        tools=[_image_generation_tool(reference_images)],
        tool_choice=ToolChoiceTypesParam(type="image_generation"),
        store=False,
        stream=False,
    )
    response = await client.responses.create(**params)
    return _image_bytes_from_response(response)


async def _paint_with_openai(prompt: str, reference_images: list[bytes]) -> bytes | None:
    api_mode = get_provider_profile(EnvConfig.PAINT_MODEL_PROVIDER).get("api_mode", "chat_completions")
    logger.info(
        "🎨 调用 {} 绘图 API, model={}, prompt_length={}, references={}",
        "Responses" if api_mode == "responses" else "Images",
        EnvConfig.PAINT_MODEL, len(prompt), len(reference_images),
    )
    client = _build_openai_client()
    try:
        if api_mode == "responses":
            return await _paint_responses(client, prompt, reference_images)
        return await _paint_images(client, prompt, reference_images)
    except APIError as exc:
        logger.warning(f"绘图 {api_mode} API 调用失败: {exc}")
        return None
    finally:
        await client.close()


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    reference_images = reference_images or []

    if not EnvConfig.PAINT_MODEL:
        logger.warning("PAINT_MODEL 未配置，绘画请求失败")
        return None

    try:
        return await _paint_with_openai(prompt, reference_images)
    except Exception as exc:
        logger.exception(f"💥 调用绘图 API 失败: {exc}")
        return None
