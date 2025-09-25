import base64
import io
import os

import dotenv
import httpx
from git import Repo
from nonebot import get_driver, logger, on_command, on_message, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.internal.adapter import Event
from PIL import Image

from plugins.frontier.cognitive import intelligent_agent
from plugins.frontier.context_check import det, text_det
from plugins.frontier.database import databases, init
from plugins.frontier.environment_check import system_check
from plugins.frontier.markdown_render import markdown_to_image
from plugins.frontier.painter import paint

dotenv.load_dotenv()
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (  # noqa: E402
    UniMessage,
)

MODEL = os.getenv("OPENAI_MODEL")

driver = get_driver()


@driver.on_startup
async def on_startup():
    system_check()
    os.makedirs("./cache", exist_ok=True)
    for i in databases.values():
        if not os.path.exists(f"./cache/{i}.db"):
            os.mkdir(f"./cache/{i}.db")
            await init()


@driver.on_bot_connect
async def on_bot_connect():
    pass
    # if os.path.exists(".lock"):
    #     os.remove(".lock")
    #     await UniMessage.text("✅ 更新完成！").send()


updater = on_command(
    "更新",
    aliases={"update"},
    priority=1,
    block=True,
)

painter = on_command("画图", priority=2, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})

model_tools = on_command("model", priority=3, block=True, aliases={"模型", "模型设置"})


@model_tools.handle()
async def handlen_model_tools(event: Event):
    texts, images = await message_extract(event)
    texts = texts.replace("/model", "")
    if not texts:
        await UniMessage.text(f"当前默认使用的模型为: {MODEL}").send()


@painter.handle()
async def handle_painter(event: Event):
    texts, images = await message_extract(event)
    texts = texts.replace("/画图", "Create a picture about: ")
    if not texts:
        await UniMessage.text("你想画点什么？").send()
    with open("./configs/system_prompt_image.txt") as f:
        img_sys_prompt = f.read()
    messages = [
        {"role": "system", "content": img_sys_prompt},
        {"role": "user", "content": [{"type": "text", "text": texts}] + images},
    ]
    await UniMessage.text("正在画图🎨").send()
    result = await paint(messages)
    if result:
        if result[0]:
            await UniMessage.text(result[0]).send()
        for image in result[1]:
            await UniMessage.image(raw=image).send()
    else:
        await UniMessage.text("画图失败，请重试。").send()


common = on_message(priority=10)


@updater.handle()
async def handle_updater():
    """处理更新命令"""
    try:
        logger.info("开始执行更新操作...")
        with open(".lock", "w") as f:
            f.write("lock")
        await UniMessage.text("🔄 开始更新...").send()

        repo = Repo(".")
        repo.git.checkout()
        pull_result = repo.git.pull(rebase=True)
        logger.info(f"Git pull 结果: {pull_result}")

    except Exception as e:
        logger.error(f"更新失败: {e}")
        await UniMessage.text(f"❌ 更新失败: {str(e)}").send()


async def message_extract(event: Event):
    message = event.get_message()
    texts = event.get_message().extract_plain_text()
    images = []
    if len(message) > 1:
        for attachment in message:
            if attachment.type == "image":
                if image_url := attachment.data.get("url"):
                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.get(image_url)
                        except httpx.ReadTimeout:
                            response = await client.get(image_url)
                        sample = response.content
                        image = Image.open(io.BytesIO(sample))
                        det_result = det.predict(image)[0]
                        await UniMessage.text(
                            "不是瑟瑟"
                            if det_result["label"] == "normal"
                            else "是瑟瑟" + f"置信度: {det_result['score']:.2f}"
                        ).send()
                        images.append(
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64.b64encode(sample).decode()}",
                            }
                        )
    return texts, images


async def send_artifacts(artifacts):
    """发送提取到的工件"""
    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            await artifact.send()


async def send_messages(response: dict):
    last_message = response["messages"][-1]
    if hasattr(last_message, "content") and last_message.content.strip():
        if len(last_message.content) > 500:
            try:
                result = await markdown_to_image(last_message.content)
                if result:
                    await UniMessage.image(raw=result).send()
            except Exception as e:
                await UniMessage.text(f"貌似出了点问题: {e}").send()
        else:
            try:
                await UniMessage.text(last_message.content).send()
            except Exception:
                # await UniMessage.text(f"貌似出了点问题: {e}").send()
                result = await markdown_to_image(last_message.content)
                if result:
                    await UniMessage.image(raw=result).send()


@common.handle()
async def handle_common(event: GroupMessageEvent):
    if not event.is_tome():
        if event.get_plaintext().startswith("小李子"):
            pass
        else:
            await common.finish()
    """处理普通消息"""
    try:
        user_id = event.get_user_id()
    except Exception:
        user_id = event.get_user_id()
    texts, images = await message_extract(event)
    messages = [{"role": "user", "content": [{"type": "text", "text": texts}] + images}]
    safe_label, categories = await text_det.predict(texts)
    if safe_label != "Safe":
        warning_msg = f"⚠️ 该消息被检测为 {safe_label}，涉及类别: {', '.join(categories) if categories else '未知'}。"
        await UniMessage.text(warning_msg).send()
        # await common.finish()

    try:
        result = await intelligent_agent(messages, user_id)

        # 处理新的返回值结构
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
            artifacts: list[UniMessage] | None = result.get("uni_messages", [])

            # 首先发送所有的 UniMessage 工件（图片、视频等）
            if artifacts:
                logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
                await send_artifacts(artifacts)

            # 然后发送文本响应
            if "messages" in response and response["messages"]:
                await send_messages(response)

    except Exception as e:
        result = await markdown_to_image(e)
        if result:
            await UniMessage.image(raw=result).send()
            await common.finish("处理过程中发生错误，已生成错误图片")

        await UniMessage.text(f"貌似什么东西坏了: {e}").send()
