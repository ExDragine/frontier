import base64
import io
import re

from nonebot import logger, on_command, require
from nonebot.adapters.milky.event import MessageEvent
from openai import AsyncClient
from PIL import Image

from utils.configs import EnvConfig
from utils.message import message_extract

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})
PAINT_COMMAND_PREFIXES = ("帮我画一张图", "画一张图", "画图", "绘图", "paint")


@painter.handle()
async def handle_painter(event: MessageEvent):
    if EnvConfig.PAINT_MODULE_ENABLED is False:
        await painter.finish("么得画了，等升级哇!")
    text, images, *_ = await message_extract(event.data.segments)
    prompt = strip_paint_prompt(text)
    if not prompt:
        tip = "你想怎么修改这张图？" if images else "你想画点什么？"
        await UniMessage.text(tip).send()
        return
    image = await paint(prompt, images)
    if image:
        await UniMessage.image(raw=image).send()
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
    with Image.open(io.BytesIO(image)) as raw_image:
        mode = "RGBA" if "A" in raw_image.getbands() else "RGB"
        normalized = raw_image.convert(mode)
        with io.BytesIO() as png_bytes:
            normalized.save(png_bytes, format="PNG")
            return (f"reference-{index}.png", png_bytes.getvalue(), "image/png")


async def paint(prompt: str, reference_images: list[bytes] | None = None) -> bytes | None:
    client = AsyncClient(base_url=EnvConfig.OPENAI_BASE_URL, api_key=EnvConfig.OPENAI_API_KEY.get_secret_value())
    request = {
        "model": EnvConfig.PAINT_MODEL,
        "prompt": prompt,
        "response_format": "b64_json",
    }
    reference_images = reference_images or []
    logger.info(
        f"🎨 调用 GPT Image API, model={EnvConfig.PAINT_MODEL}, prompt_length={len(prompt)}, references={len(reference_images)}"
    )

    try:
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
    except Exception as e:
        logger.exception(f"💥 调用 GPT Image API 失败: {e}")
        return None
