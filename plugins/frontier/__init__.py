import base64
import os
import time

import dotenv
from git import Repo
from langchain.messages import AIMessage
from nonebot import get_driver, logger, on_command, on_message, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.internal.adapter import Event
from nonebot.permission import SUPERUSER

from plugins.frontier.cognitive import chat_agent
from plugins.frontier.message import (
    message_check,
    message_extract,
    message_gateway,
    send_artifacts,
    send_messages,
)
from plugins.frontier.painter import paint
from utils.database import MessageDatabase
from utils.environment_check import system_check
from utils.slm import slm_cognitive

dotenv.load_dotenv()
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import Target, UniMessage  # noqa: E402

MODEL = os.getenv("OPENAI_MODEL")

driver = get_driver()
messages_db = MessageDatabase()


@driver.on_startup
async def on_startup():
    system_check()
    os.makedirs("./cache", exist_ok=True)


@driver.on_bot_connect
async def on_bot_connect():
    if os.path.exists(".lock"):
        os.remove(".lock")
        await UniMessage.text("✅ 更新完成！").send(target=Target.group(os.getenv("ANNOUNCE_GROUP_ID", "")))


updater = on_command("更新", priority=1, block=True, aliases={"update"}, permission=SUPERUSER)
setting = on_command("model", priority=2, block=True, aliases={"模型", "模型设置"})
painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})
common = on_message(priority=10)


@updater.handle()
async def handle_updater(event: Event):
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


@setting.handle()
async def handle_setting(event: Event):
    text, images = await message_extract(event)
    text = text.replace("/model", "")
    if not text:
        await UniMessage.text(f"当前默认使用的模型为: {MODEL}").send()


@painter.handle()
async def handle_painter(event: Event):
    text, images = await message_extract(event)
    text = text.replace("/画图", "Create a picture about: ")
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
    slm_reply = await slm_cognitive("请生成一段简短的提示语，内容由用户输入决定，不要超过20字。", "正在画图🎨")
    if slm_reply:
        await UniMessage.text(slm_reply).send()
    result = await paint(messages)
    if result:
        if result[0]:
            await UniMessage.text(result[0]).send()
        for image in result[1]:
            await UniMessage.image(raw=image).send()
    else:
        await UniMessage.text("画图失败，请重试。").send()


@common.handle()
async def handle_common(event: GroupMessageEvent | PrivateMessageEvent):
    user_id = event.get_user_id()
    user_name = event.sender.card if event.sender.card else event.sender.nickname
    text, images = await message_extract(event)
    if isinstance(event, GroupMessageEvent):
        group_id = int(event.group_id)
    else:
        group_id = None
    if not text:
        if not event.is_tome():
            await common.finish()
        else:
            text = "Hello"
    await messages_db.insert(
        time=int(time.time() * 1000),
        msg_id=event.message_id,
        user_id=int(user_id),
        group_id=group_id,
        user_name=user_name,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
    )
    messages = await messages_db.prepare_message(
        int(user_id),
        group_id,
    )
    if not await message_gateway(event, messages):
        await common.finish()
    _ = await message_check(text, images)
    messages.append(
        {
            "role": "user",
            "content": [{"type": "text", "text": f"{user_name}:{text}"}]
            + [
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"}
                for image in images
            ],
        }
    )
    result = await chat_agent(messages, user_id, user_name)
    if isinstance(result, dict) and "response" in result:
        response = result["response"]
        artifacts: list[UniMessage] | None = result.get("uni_messages", [])
        if artifacts:
            logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
            await send_artifacts(artifacts)
        if response["messages"] and isinstance(response["messages"][-1], AIMessage):
            await messages_db.insert(
                time=int(time.time() * 1000),
                msg_id=None,
                user_id=int(event.self_id),
                group_id=group_id,
                user_name="Assistant",
                role="assistant",
                content=response["messages"][-1].content,
            )
            await send_messages(response)
        else:
            await UniMessage.text(response["messages"]).send()
