import base64

from nonebot import on_command, require
from nonebot.internal.adapter import Event

from plugins.wonderland.painter import paint
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
    text, images = await paint(messages)
    if not text and not images:
        await UniMessage.text("这里空空如也，什么都没有画出来。").send()
    if text:
        await UniMessage.text(text).send()
    if images:
        for image in images:
            await UniMessage.image(raw=image).send()
