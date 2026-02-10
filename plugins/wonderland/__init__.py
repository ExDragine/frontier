import base64
import io
import json

from nonebot import logger, on_command, require
from nonebot.adapters.milky.event import MessageEvent
from openai import AsyncClient
from PIL import Image

from utils.configs import EnvConfig
from utils.message import message_extract

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})


@painter.handle()
async def handle_painter(event: MessageEvent):
    if EnvConfig.PAINT_MODULE_ENABLED is False:
        await painter.finish("么得画了，等升级哇!")
    text, images, *_ = await message_extract(event.data.segments)
    text = text.replace("/画图", "")
    if not text:
        await UniMessage.text("你想画点什么？").send()
    image = await paint(text)
    if image:
        await UniMessage.image(raw=image).send()
    else:
        await UniMessage.text("这里空空如也，什么都没有画出来。").send()


async def paint(prompt: str) -> bytes:
    client = AsyncClient(base_url=EnvConfig.OPENAI_BASE_URL, api_key=EnvConfig.OPENAI_API_KEY.get_secret_value())
    extra_body: dict = {"modalities": ["image"]}
    logger.info(f"🎨 调用绘图API, extra_body: {extra_body}")
    response = await client.chat.completions.create(
        model=EnvConfig.PAINT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        extra_body=extra_body,
    )
    messages = json.loads(response.choices[0].message.model_dump_json(indent=4))
    image = messages.get("images")[0].get("image_url").get("url").split(",", 1)[1]
    with io.BytesIO() as img_bytes:
        Image.open(io.BytesIO(base64.b64decode(image))).convert("RGB").save(img_bytes, format="JPEG")
        return img_bytes.getvalue()
