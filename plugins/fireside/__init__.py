import asyncio
import base64
import time
from typing import Literal

from nonebot import logger, on_message, require
from nonebot.adapters.milky.event import MessageEvent
from pydantic import BaseModel, Field

from utils.agents import FrontierCognitive, assistant_agent
from utils.configs import EnvConfig
from utils.database import MessageDatabase
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

common = on_message(priority=10)

message_heap = RepeatMessageHeap(capacity=10, threshold=2)


class AgentChoice(BaseModel):
    agent_capability: Literal["minimal", "low", "medium", "high"] = Field(
        description="For simple talk ask ,choose 'minimal'; for lightweight, simple tasks, choose 'low'; for medium complexity, choose 'medium'; for complex tasks, choose 'high'."
    )


async def store_memory_async(user_text: str, user_id: str, group_id: int | None, source_msg_id: int | None):
    if not EnvConfig.MEMORY_ENABLED:
        return
    allow, sanitized_user_text, reason = memory.apply_privacy_filter(user_text)
    if not allow:
        logger.info(f"🔒 记忆写入被隐私策略拒绝 user={user_id} reason={reason}")
        return
    try:
        with open("./prompts/memory_analyze_v2.txt", encoding="utf-8") as f:
            memory_prompt = f.read()
    except FileNotFoundError:
        logger.error("❌ 未找到 memory_analyze_v2.txt 文件")
        return
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        logger.error(f"❌ 读取 memory_analyze_v2.txt 失败: {e}")
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


@common.handle()
async def handle_common(event: MessageEvent):  # noqa: C901
    if EnvConfig.AGENT_MODULE_ENABLED is False:
        await common.finish(f"{EnvConfig.BOT_NAME}飞升了,暂时不可用")
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
    await messages_db.insert(
        time=int(time.time() * 1000),
        msg_id=event_id,
        user_id=int(user_id),
        group_id=group_id,
        user_name=user_name,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
    )
    messages = await messages_db.prepare_message(
        int(user_id),
        group_id,
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
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

    risk_check = await message_check(text, images)
    if not risk_check:
        await common.send("👀")
    messages.append(
        {
            "role": "user",
            "content": [{"type": "text", "text": str({"metadata": {"user_name": user_name}, "content": text})}]
            + [
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"}
                for image in images
            ],
        }
    )

    try:
        with open("prompts/agent_choice.txt", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        logger.error("❌ 未找到 agent_choice.txt 文件")
        await common.finish("⚙️ 系统配置文件缺失，请联系管理员")
        return
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        logger.error(f"❌ 读取 agent_choice.txt 失败: {e}")
        await common.finish("⚙️ 系统配置错误，请联系管理员")
        return
    # ref_history = await memory.mmr_search(str(group_id) if group_id else str(event.user_id), text, 3, filter={"": ""})
    agent_choice: AgentChoice = await assistant_agent(system_prompt, text, response_format=AgentChoice)
    result = await f_cognitive.chat_agent(
        messages,
        user_id,
        user_name,
        agent_choice.agent_capability,
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
                content=response["messages"][-1].content,
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


from . import memory_commands  # noqa: E402, F401
