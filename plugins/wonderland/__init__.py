import base64

from nonebot import logger, on_command, require
from nonebot.internal.adapter import Event

from plugins.wonderland.painter import analyze_config, paint
from utils.message import message_extract

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})


@painter.handle()
async def handle_painter(event: Event):
    text, images = await message_extract(event)
    text = text.replace("/画图", "")
    if not text:
        await UniMessage.text("你想画点什么？").send()
    with open("./configs/system_prompt_image.txt") as f:
        img_sys_prompt = f.read()
    messages = [
        {"role": "system", "content": img_sys_prompt},
        {
            "role": "user",
            "content": [{"type": "text", "text": text}]
            + [
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"}
                for image in images
            ],
        },
    ]
    aspect_ratio, image_size = await analyze_config(text)
    text, images = await paint(messages, aspect_ratio, image_size)
    if not text and not images:
        await UniMessage.text("这里空空如也，什么都没有画出来。").send()
    if text:
        await UniMessage.text(text).send()
    if images:
        logger.info(f"生成了 {len(images)} 张图片")
        for image in images:
            await UniMessage.image(raw=image).send()
