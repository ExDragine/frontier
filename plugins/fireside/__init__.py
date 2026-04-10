import asyncio
import base64
import datetime
import os
import time
from typing import Literal

from nonebot import get_bot, get_driver, logger, on_message, require
from nonebot.adapters.milky.event import MessageEvent
from pydantic import BaseModel, Field

from utils.agents import FrontierCognitive, assistant_agent
from utils.configs import EnvConfig
from utils.database import MessageDatabase, MessageImage
from utils.memory import get_memory_service
from utils.memory_types import MemoryAnalyzeResult
from utils.message import (
    message_check,
    message_extract,
    message_gateway,
    send_artifacts,
    send_messages,
)
from utils.min_heap import RepeatMessageHeap

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

messages_db = MessageDatabase()
f_cognitive = FrontierCognitive()
memory = get_memory_service()
driver = get_driver()

common = on_message(priority=10)

message_heap = RepeatMessageHeap(capacity=10, threshold=2)


class AgentChoice(BaseModel):
    agent_capability: Literal["low", "medium", "high", "xhigh"] = Field(
        description="Choose 'low' for casual chat or simple questions; 'medium' for typical tasks with moderate reasoning; 'high' for complex multi-step tasks; 'xhigh' for deep research or architectural decisions."
    )


async def store_memory_async(user_text: str, user_id: str, group_id: int | None, source_msg_id: int | None):
    if not EnvConfig.MEMORY_ENABLED:
        return
    allow, sanitized_user_text, reason = memory.apply_privacy_filter(user_text)
    if not allow:
        logger.info(f"🔒 记忆写入被隐私策略拒绝 user={user_id} reason={reason}")
        return
    try:
        with open("./prompts/memory_analyze_v2.md", encoding="utf-8") as f:
            memory_prompt = f.read()
    except FileNotFoundError:
        logger.error("❌ 未找到 memory_analyze_v2.md 文件")
        return
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        logger.error(f"❌ 读取 memory_analyze_v2.md 失败: {e}")
        return

    try:
        memory_analyze: MemoryAnalyzeResult = await assistant_agent(
            memory_prompt,
            sanitized_user_text,
            response_format=MemoryAnalyzeResult,
        )
    except Exception as e:
        logger.error(f"❌ 记忆分析失败 user={user_id}: {type(e).__name__}: {e}")
        return

    if not memory_analyze.should_memory:
        return

    try:
        saved_ids = await memory.persist_from_analysis(
            analysis=memory_analyze,
            raw_user_text=sanitized_user_text,
            user_id=user_id,
            group_id=group_id,
            source_msg_id=source_msg_id,
        )
        if saved_ids:
            logger.info(f"🧠 记忆写入成功 user={user_id} ids={saved_ids}")
    except Exception as e:
        logger.error(f"❌ 记忆写入失败 user={user_id}: {type(e).__name__}: {e}")


def schedule_memory_write(user_text: str, user_id: str, group_id: int | None, source_msg_id: int | None):
    task = asyncio.create_task(store_memory_async(user_text, user_id, group_id, source_msg_id))

    def done_callback(done_task: asyncio.Task):
        if done_task.cancelled():
            return
        if exception := done_task.exception():
            logger.error(f"❌ 异步记忆任务异常: {type(exception).__name__}: {exception}")

    task.add_done_callback(done_callback)


async def store_image_summary_async(msg_time: int, user_id: int, group_id: int | None):
    if not EnvConfig.IMAGE_ENABLED:
        return
    try:
        with open("./prompts/image_summary.md", encoding="utf-8") as f:
            summary_prompt = f.read()
    except (FileNotFoundError, OSError) as e:
        logger.error(f"❌ 读取 image_summary.md 失败: {e}")
        return

    from sqlmodel import Session, select

    with Session(messages_db.engine) as session:
        stmt = select(MessageImage).where(MessageImage.msg_time == msg_time).order_by(MessageImage.index)
        img_records = session.exec(stmt).all()

    for img in img_records:
        full_path = os.path.join(os.getcwd(), img.file_path)
        if not os.path.exists(full_path):
            continue
        try:
            with open(full_path, "rb") as f:
                img_bytes = f.read()
            summary = await assistant_agent(
                system_prompt=summary_prompt,
                user_prompt="请描述这张图片。",
                images=[img_bytes],
            )
            if summary:
                with Session(messages_db.engine) as session:
                    record = session.get(MessageImage, img.id)
                    if record:
                        record.ai_summary = summary.strip()
                        session.add(record)
                        session.commit()
                logger.info(f"🖼️ 图片摘要生成成功 msg_time={msg_time} index={img.index}")
        except Exception as e:
            logger.error(f"❌ 图片摘要生成失败 msg_time={msg_time} index={img.index}: {e}")


def schedule_image_summary_write(msg_time: int, user_id: int, group_id: int | None):
    task = asyncio.create_task(store_image_summary_async(msg_time, user_id, group_id))

    def done_callback(done_task: asyncio.Task):
        if done_task.cancelled():
            return
        if exception := done_task.exception():
            logger.error(f"❌ 异步图片摘要任务异常: {type(exception).__name__}: {exception}")

    task.add_done_callback(done_callback)


@driver.on_startup
async def on_startup():
    if EnvConfig.IMAGE_AUTO_CLEANUP:
        cleaned = await messages_db.cleanup_expired_images()
        logger.info(f"🗑️ 清理过期图片 {cleaned} 张")


@common.handle()
async def handle_common(event: MessageEvent):  # noqa: C901
    if EnvConfig.AGENT_MODULE_ENABLED is False:
        await common.finish(f"{EnvConfig.BOT_NAME}飞升了,暂时不可用")
    bot = get_bot()
    user_id = event.get_user_id()
    user_name = event.data.sender.nickname
    event_id = event.data.message_seq
    text, images, *_ = await message_extract(event.data.segments)
    group_id = event.data.group.group_id if event.data.group else None
    if not text:
        if not event.is_tome():
            await common.finish()
        else:
            text = ""
    msg_time = int(time.time() * 1000)
    await messages_db.insert(
        time=msg_time,
        msg_id=event_id,
        user_id=int(user_id),
        group_id=group_id,
        user_name=user_name,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
    )
    if images and EnvConfig.IMAGE_ENABLED:
        try:
            await messages_db.insert_images(msg_time=msg_time, user_id=int(user_id), group_id=group_id, images=images)
            schedule_image_summary_write(msg_time=msg_time, user_id=int(user_id), group_id=group_id)
        except Exception as e:
            logger.warning(f"⚠️ 图片保存失败（不影响主流程）: {e}")
    messages = await messages_db.prepare_message(
        int(user_id),
        group_id,
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
        image_window_size=EnvConfig.IMAGE_WINDOW_SIZE,
    )

    # Bot 自己的消息不参与复读检查
    # if user_id == str(event.self_id):
    #     await common.finish()
    # 复读机检查
    # gid = group_id or 0
    # if text and message_heap.add(gid, text):
    #     logger.info(f"🔁 触发复读：群{gid} 消息「{text[:20]}」")
    #     await UniMessage.text(text).send()
    # await common.finish()

    if not await message_gateway(event, messages):
        await common.finish()
    if EnvConfig.CONTENT_CHECK_ENABLED:
        risk_check = await message_check(text, images)
    else:
        risk_check = "Safe"
    match risk_check:
        case "Safe":
            if group_id:
                try:
                    await bot.send_group_message_reaction(
                        group_id=group_id, message_seq=event_id, reaction="333", is_add=True
                    )
                except Exception as e:
                    logger.warning(f"表情回复发送失败，使用文本消息: {e}")
                    await common.send("🔮")
            else:
                await common.send("🔮")
        case "Controversial":
            # 使用表情回复功能
            if group_id:
                try:
                    await bot.send_group_message_reaction(
                        group_id=group_id, message_seq=event_id, reaction="32", is_add=True
                    )
                except Exception as e:
                    logger.warning(f"表情回复发送失败，使用文本消息: {e}")
                    await common.send("👀")
            else:
                # 私聊场景，直接发送文本
                await common.send("👀")
        case "Unsafe":
            if group_id:
                try:
                    await bot.send_group_message_reaction(
                        group_id=group_id, message_seq=event_id, reaction="267", is_add=True
                    )
                except Exception as e:
                    logger.warning(f"表情回复发送失败，使用文本消息: {e}")
                    await common.send("😅")
            else:
                # 私聊场景，直接发送文本
                await common.send("😅")
    messages.append(
        {
            "role": "user",
            "content": [{"type": "text", "text": str({"metadata": {"time": datetime.datetime.fromtimestamp(msg_time / 1000).astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"), "user_name": user_name}, "content": text})}]
            + [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"}}
                for image in images
            ],
        }
    )

    if EnvConfig.AGENT_CAPABILITY == "auto":
        try:
            with open("prompts/agent_choice.md", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.error("❌ 未找到 agent_choice.md 文件")
            await common.finish("⚙️ 系统配置文件缺失，请联系管理员")
            return
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            logger.error(f"❌ 读取 agent_choice.md 失败: {e}")
            await common.finish("⚙️ 系统配置错误，请联系管理员")
            return
        # ref_history = await memory.mmr_search(str(group_id) if group_id else str(event.user_id), text, 3, filter={"": ""})
        agent_choice: AgentChoice = await assistant_agent(system_prompt, text, response_format=AgentChoice)
        capability = agent_choice.agent_capability
    else:
        capability = EnvConfig.AGENT_CAPABILITY
    result = await f_cognitive.chat_agent(
        messages,
        user_id,
        user_name,
        capability,
        group_id=group_id,
        query_text=text,
    )

    if isinstance(result, dict) and "response" in result:
        response = result["response"]
        if not response:
            await common.finish(f"{EnvConfig.BOT_NAME}飞升了，暂时不可用")

        artifacts: list[UniMessage] | None = result.get("uni_messages", [])

        if artifacts:
            logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
            await send_artifacts(artifacts)

        if response["messages"] and isinstance(response["messages"], list):
            await messages_db.insert(
                time=int(time.time() * 1000),
                msg_id=None,
                user_id=int(event.self_id),
                group_id=group_id,
                user_name="Assistant",
                role="assistant",
                content=str(response["messages"][-1].text) if hasattr(response["messages"][-1], "text") else response["messages"][-1].content,
            )
            await send_messages(group_id, event_id, response)
            schedule_memory_write(
                user_text=text,
                user_id=user_id,
                group_id=group_id,
                source_msg_id=event_id,
            )

        else:
            await UniMessage.text(response["messages"]).send()
