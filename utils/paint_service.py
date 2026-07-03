import inspect
import io
import math
from collections import defaultdict, deque
from dataclasses import dataclass

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError
from nonebot import logger
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


# ── Nano Banana 2 (Gemini 3.1 Flash Image) ─────────────────────────


def _paint_api_key() -> str:
    paint_key = EnvConfig.PAINT_API_KEY.get_secret_value()
    if paint_key:
        return paint_key
    google_key = getattr(EnvConfig, "GOOGLE_API_KEY", None)
    if google_key:
        return google_key.get_secret_value()
    return ""


def _paint_aspect_ratio() -> str:
    return getattr(EnvConfig, "PAINT_ASPECT_RATIO", "1:1")


def _paint_image_size() -> str:
    return getattr(EnvConfig, "PAINT_IMAGE_SIZE", "1K")


def _build_genai_client() -> genai.Client:
    kwargs: dict = {"api_key": _paint_api_key()}
    base_url = EnvConfig.PAINT_BASE_URL
    if base_url:
        kwargs["http_options"] = genai_types.HttpOptions(base_url=base_url)
    return genai.Client(**kwargs)


async def _close_genai_client(client: genai.Client) -> None:
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


async def _paint_with_gemini(prompt: str, reference_images: list[bytes]) -> bytes | None:
    client = _build_genai_client()

    config = genai_types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=genai_types.ImageConfig(
            aspect_ratio=_paint_aspect_ratio(),
            image_size=_paint_image_size(),
        ),
    )

    # 构建 contents：参考图片在前，文本提示词在后
    if reference_images:
        contents = []
        for image in reference_images:
            png_bytes = _normalize_reference_image(image)
            contents.append(genai_types.Part.from_bytes(data=png_bytes, mime_type="image/png"))
        contents.append(genai_types.Part.from_text(text=prompt))
    else:
        contents = prompt

    try:
        response = await client.aio.models.generate_content(
            model=EnvConfig.PAINT_MODEL,
            contents=contents,
            config=config,
        )
    except ClientError as e:
        logger.warning(f"Gemini 图片 API 调用失败: {e}")
        return None
    finally:
        await _close_genai_client(client)

    return _extract_image_from_gemini_response(response)


def _extract_image_from_gemini_response(response) -> bytes | None:
    if not response.candidates:
        logger.warning("Gemini 图片 API 返回空 candidates（可能被安全过滤）")
        return None

    candidate = response.candidates[0]
    if candidate.finish_reason and candidate.finish_reason.name == "SAFETY":
        logger.warning("Gemini 图片 API 因安全原因拒绝: finish_reason=SAFETY")
        return None

    # 从响应中提取图片
    candidate_content = candidate.content
    if candidate_content is None:
        logger.warning("Gemini 图片 API 响应中 candidate.content 为 None")
        return None

    for part in candidate_content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            return part.inline_data.data

    # 没有图片时输出文本用于诊断
    for part in candidate_content.parts:
        if part.text:
            logger.warning(f"Gemini 图片 API 返回文本而非图片: {part.text[:200]}")

    logger.warning("Gemini 图片 API 响应中没有找到图片数据")
    return None


# ── 主入口 ─────────────────────────────────────────────────────────


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    reference_images = reference_images or []

    if not EnvConfig.PAINT_MODEL:
        logger.warning("PAINT_MODEL 未配置，绘画请求失败")
        return None

    logger.info(
        f"🎨 调用 Gemini Nano Banana, model={EnvConfig.PAINT_MODEL}, "
        f"prompt_length={len(prompt)}, references={len(reference_images)}, "
        # f"aspect_ratio={_paint_aspect_ratio()}"
    )

    try:
        return await _paint_with_gemini(prompt, reference_images)
    except Exception as e:
        logger.exception(f"💥 调用 Gemini 图片 API 失败: {e}")
        return None
