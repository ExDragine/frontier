import base64
import inspect
import io
import re

from google import genai
from google.genai import types as genai_types
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
PAINT_COMMAND_PREFIXES = ("帮我画一张图", "画一张图", "画图", "绘图", "paint")
messages_db = MessageDatabase()


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
    image = await paint(prompt, reference_images)
    if image:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.image(raw=image)).send()
    else:
        await UniMessage.text("这里空空如也，什么都没有画出来。").send()


def strip_paint_prompt(text: str) -> str:
    stripped = text.strip()
    for prefix in PAINT_COMMAND_PREFIXES:
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
            response = await client.aio.models.edit_image(
                model=EnvConfig.PAINT_MODEL,
                prompt=prompt,
                reference_images=payload,
            )
        else:
            response = await client.aio.models.generate_images(
                model=EnvConfig.PAINT_MODEL,
                prompt=prompt,
            )
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
