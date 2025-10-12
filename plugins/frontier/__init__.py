import os
import secrets
import time

import dotenv
from git import Repo
from langchain.schema import AIMessage
from nonebot import get_driver, logger, on_command, on_message, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.internal.adapter import Event
from nonebot.permission import SUPERUSER

from plugins.frontier.cognitive import intelligent_agent
from plugins.frontier.context_check import text_det
from plugins.frontier.database import MessageDatabase
from plugins.frontier.environment_check import system_check
from plugins.frontier.markdown_render import markdown_to_image
from plugins.frontier.painter import paint
from plugins.frontier.slm import slm_cognitive
from plugins.frontier.utils import message_extract, send_artifacts, send_messages

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
async def handle_common(event: GroupMessageEvent):
    user_id = event.get_user_id()
    user_name = event.sender.card if event.sender.card else event.sender.nickname
    texts, images = await message_extract(event)
    if not texts:
        await common.finish()
    await messages_db.insert(
        time=int(time.time() * 1000),
        msg_id=event.message_id,
        user_id=int(user_id),
        group_id=int(event.group_id) if event.group_id else None,
        user_name=user_name,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=texts,
    )
    messages = await messages_db.prepare_message(
        group_id=int(event.group_id) if event.group_id else None, user_id=int(user_id)
    )
    if not event.is_tome():
        if event.get_plaintext().startswith("小李子"):
            pass
        else:
            if secrets.randbelow(100) != 1:
                await common.finish()
            temp_conv: list[dict] = messages[-5:] + [{"role": "user", "content": f"{user_name}: {texts}"}]
            plain_conv = "\n".join(str(conv.get("content", "")) for conv in temp_conv)
            slm_reply = await slm_cognitive(
                "请判断当前对话内容是否适合插话，是则返回 YES 不是则返回 NO, 只返回这两个结果",
                plain_conv,
            )
            if slm_reply == "YES":
                pass
            else:
                await common.finish()
    messages.append({"role": "user", "content": [{"type": "text", "text": f"{user_name}:{texts}"}] + images})
    safe_label, categories = await text_det.predict(texts)
    if safe_label != "Safe":
        warning_msg = f"⚠️ 该消息被检测为 {safe_label}，涉及类别: {', '.join(categories) if categories else '未知'}。"
        slm_reply = await slm_cognitive(
            "根据系统给出的提示说一段怪话，拟人的用词，简短明了，不超过30字。", warning_msg
        )
        if slm_reply:
            await UniMessage.text(slm_reply).send()
        else:
            await UniMessage.text(warning_msg).send()

    try:
        result = await intelligent_agent(messages, user_id, user_name)
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
                    group_id=int(event.group_id) if event.group_id else None,
                    user_name="Assistant",
                    role="assistant",
                    content=response["messages"][-1].content,
                )
                await send_messages(response)
            else:
                await UniMessage.text(response["messages"]).send()

    except Exception as e:
        result = await markdown_to_image(e)
        if result:
            await UniMessage.image(raw=result).send()
            await common.finish("处理过程中发生错误，已生成错误图片")

        await UniMessage.text(f"貌似什么东西坏了: {e}").send()
