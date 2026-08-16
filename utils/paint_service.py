import base64
import binascii
import io
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Literal, cast

from nonebot import logger
from openai import APIError, AsyncOpenAI
from openai.types.responses import EasyInputMessageParam, ResponseInputParam
from openai.types.responses.response_create_params import ResponseCreateParamsNonStreaming
from openai.types.responses.response_input_image_param import ResponseInputImageParam
from openai.types.responses.response_input_message_content_list_param import ResponseInputContentParam
from openai.types.responses.response_input_text_param import ResponseInputTextParam
from openai.types.responses.tool_choice_types_param import ToolChoiceTypesParam
from openai.types.responses.tool_param import ImageGeneration
from PIL import Image

from utils.configs import EnvConfig, get_provider_profile


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


def _image_bytes_from_response(response: Any) -> bytes | None:
    output = _response_value(response, "output") or []
    for item in output:
        if _response_value(item, "type") != "image_generation_call":
            continue
        encoded = _response_value(item, "result")
        if not isinstance(encoded, str) or not encoded.strip():
            continue
        encoded = encoded.strip()
        if encoded.startswith("data:"):
            _, separator, encoded = encoded.partition(",")
            if not separator:
                continue
        try:
            return base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            logger.warning("Responses image_generation 返回了无效的 base64 图片")
            continue

    logger.warning("Responses API 响应中没有 image_generation_call 结果")
    return None


async def _paint_with_openai(prompt: str, reference_images: list[bytes]) -> bytes | None:
    client = _build_openai_client()
    try:
        # sub2api accepts the image model in both positions, then rewrites the
        # top-level model to its Codex host model while preserving the tool model.
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
    except APIError as exc:
        logger.warning(f"Responses image_generation 调用失败: {exc}")
        return None
    finally:
        await client.close()


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    reference_images = reference_images or []

    if not EnvConfig.PAINT_MODEL:
        logger.warning("PAINT_MODEL 未配置，绘画请求失败")
        return None

    logger.info(
        f"🎨 调用 Responses image_generation, model={EnvConfig.PAINT_MODEL}, "
        f"prompt_length={len(prompt)}, references={len(reference_images)}"
    )

    try:
        return await _paint_with_openai(prompt, reference_images)
    except Exception as exc:
        logger.exception(f"💥 调用 Responses image_generation 失败: {exc}")
        return None
