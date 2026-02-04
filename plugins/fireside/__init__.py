import base64
import time
from typing import Literal

import uuid_utils
from arclet.alconna import Alconna, AllParam, Args
from nonebot import logger, require
from nonebot.adapters.milky.event import MessageEvent
from pydantic import BaseModel, Field

from utils.agents import FrontierCognitive, assistant_agent
from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.memory import MemoryStore
from utils.message import (
    message_check,
    message_extract,
    message_gateway,
    send_artifacts,
    send_messages,
)
from utils.min_heap import RepeatMessageHeap

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage, on_alconna  # noqa: E402

messages_db = MessageDatabase()
f_cognitive = FrontierCognitive()
memory = MemoryStore()

common = on_alconna(
    Alconna(Args["content?", AllParam]),
    priority=10,
    block=False,
    use_cmd_start=False,
)

message_heap = RepeatMessageHeap(capacity=10, threshold=2)


class AgentChoice(BaseModel):
    agent_capability: Literal["minimal", "low", "medium", "high"] = Field(
        description="For simple talk ask ,choose 'minimal'; for lightweight, simple tasks, choose 'low'; for medium complexity, choose 'medium'; for complex tasks, choose 'high'."
    )


class MemoryAnalyze(BaseModel):
    should_memory: bool = Field(description="Indicates whether this message should be stored in memory.")
    memory_content: str = Field(
        description="Concise, factual summary of the specific information to store in long‑term memory (e.g., user preferences, personal details, important decisions, or contextual facts useful for future conversations)."
    )


@common.handle()
async def handle_common(event: MessageEvent):
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
    result = await f_cognitive.chat_agent(messages, user_id, user_name, agent_choice.agent_capability)

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
            try:
                with open("./prompts/memory_analyze.txt", encoding="utf-8") as f:
                    MASP = f.read()
            except FileNotFoundError:
                logger.error("❌ 未找到 memory_analyze.txt 文件")
                return  # 记忆分析失败不影响主流程
            except (PermissionError, OSError, UnicodeDecodeError) as e:
                logger.error(f"❌ 读取 memory_analyze.txt 失败: {e}")
                return
            memory_analyze: MemoryAnalyze = await assistant_agent(
                MASP, f"user: {text}\n assistant: {response['messages'][-1].content}", response_format=MemoryAnalyze
            )
            if memory_analyze.should_memory:
                await memory.add(
                    str(group_id) if group_id else user_id,
                    [memory_analyze.memory_content],
                    [uuid_utils.uuid7()],
                )

        else:
            await UniMessage.text(response["messages"]).send()
