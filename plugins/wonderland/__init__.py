import base64

from nonebot import on_command, require
from nonebot.internal.adapter import Event

from plugins.wonderland.painter import paint
from utils.configs import EnvConfig
from utils.message import message_extract

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})


@painter.handle()
async def handle_painter(event: Event):
    if EnvConfig.PAINT_MODULE_ENABLED is False:
        await painter.finish("么得画了，等升级哇!")
    text, images = await message_extract(event)
    text = text.replace("/画图", "")
    if not text:
        await UniMessage.text("你想画点什么？").send()
    with open("./prompts/system_prompt_image.txt", encoding="utf-8") as f:
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
    image = await paint(messages)
    if image:
        await UniMessage.image(raw=image).send()
    else:
        await UniMessage.text("这里空空如也，什么都没有画出来。").send()
