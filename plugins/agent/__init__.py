import base64
import datetime
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nonebot import get_bot, get_driver, logger, on_message, require
from nonebot.adapters.milky.event import MessageEvent
from pydantic import BaseModel, Field

from utils.agent_queue import AgentQueueFullError, AgentQueueManager
from utils.agents import FrontierCognitive, _agent_thread_id, assistant_agent
from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.message import (
    aclose_http_client as message_aclose_http_client,
)
from utils.message import (
    message_check,
    message_extract,
    message_gateway,
    send_artifacts,
    send_messages,
)
from utils.min_heap import RepeatMessageHeap
from utils.reply_context import build_reply_context, reply_seq_from_segments
from utils.staged_artifacts import cleanup_expired_staged_artifacts

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

messages_db = MessageDatabase()
f_cognitive = FrontierCognitive()
driver = get_driver()

common = on_message(priority=10)

message_heap = RepeatMessageHeap(capacity=10, threshold=2)
agent_queue = AgentQueueManager(maxsize=5, idle_ttl_seconds=1800.0, job_timeout_seconds=900.0)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AgentChoice(BaseModel):
    should_reply: bool = Field(
        description=(
            "Whether the assistant should continue the conversation. "
            "False when the latest input is only evaluation, acknowledgement, or a useless statement "
            "after the previous issue has been resolved."
        )
    )


@dataclass(slots=True)
class AgentRequestContext:
    bot: Any
    event: MessageEvent
    user_id: str
    user_name: str
    event_id: int
    group_id: int | None
    msg_time: int
    text: str
    quoted_images: list[bytes]
    images: list[bytes]
    videos: list[bytes]


def _summarize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content or "")

    parts = []
    for item in content:
        if not isinstance(item, dict):
            parts.append(str(item))
        elif item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(part for part in parts if part)


def _build_agent_choice_input(context: AgentRequestContext, history_messages: list[dict]) -> str:
    lines = []
    for message in history_messages[-8:]:
        content = _summarize_message_content(message.get("content", "")).strip()
        if content:
            lines.append(f"{message.get('role', '')}: {content}")
    if context.text.strip():
        lines.append(f"user: {context.text.strip()}")
    return "\n".join(lines)


async def _agent_choice_should_reply(context: AgentRequestContext, history_messages: list[dict]) -> bool:
    try:
        with open(PROJECT_ROOT / "prompts" / "agent_choice.md", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        logger.error("❌ 未找到 agent_choice.md 文件")
        await UniMessage.text("⚙️ 系统配置文件缺失，请联系管理员").send()
        return False
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        logger.error(f"❌ 读取 agent_choice.md 失败: {e}")
        await UniMessage.text("⚙️ 系统配置错误，请联系管理员").send()
        return False

    agent_choice: AgentChoice = await assistant_agent(
        system_prompt,
        _build_agent_choice_input(context, history_messages),
        response_format=AgentChoice,
    )
    return agent_choice.should_reply


async def _process_agent_request(context: AgentRequestContext) -> None:
    messages = await messages_db.prepare_message(
        int(context.user_id),
        context.group_id,
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
        before_time=context.msg_time,
    )
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": str(
                        {
                            "metadata": {
                                "time": datetime.datetime.fromtimestamp(context.msg_time / 1000)
                                .astimezone(datetime.timezone(datetime.timedelta(hours=8)))
                                .strftime("%Y-%m-%d %H:%M:%S"),
                                "user_name": context.user_name,
                            },
                            "content": context.text,
                        }
                    ),
                }
            ]
            + [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"},
                }
                for image in context.quoted_images + context.images
            ],
        }
    )

    capability = EnvConfig.AGENT_CAPABILITY
    result = await f_cognitive.chat_agent(
        messages,
        context.user_id,
        context.user_name,
        capability,
        group_id=context.group_id,
        query_text=context.text,
        image_inputs=context.quoted_images + context.images,
        video_inputs=context.videos,
    )

    if not isinstance(result, dict) or "response" not in result:
        await UniMessage.text(f"{EnvConfig.BOT_NAME}飞升了，暂时不可用").send()
        return

    response = result["response"]
    if not response:
        await UniMessage.text(f"{EnvConfig.BOT_NAME}飞升了，暂时不可用").send()
        return

    artifacts: list[UniMessage] | None = result.get("uni_messages", [])
    if artifacts:
        logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
        await send_artifacts(artifacts)

    if response["messages"] and isinstance(response["messages"], list):
        await messages_db.insert(
            time=int(time.time() * 1000),
            msg_id=None,
            user_id=int(context.event.self_id),
            group_id=context.group_id,
            user_name="Assistant",
            role="assistant",
            content=str(response["messages"][-1].text)
            if hasattr(response["messages"][-1], "text")
            else response["messages"][-1].content,
        )
        await send_messages(context.group_id, context.event_id, response)
    else:
        await UniMessage.text(response["messages"]).send()


@driver.on_startup
async def on_startup():
    if EnvConfig.IMAGE_AUTO_CLEANUP:
        cleaned = await messages_db.cleanup_expired_images()
        logger.info(f"🗑️ 清理过期图片 {cleaned} 张")
    cleaned_artifacts = cleanup_expired_staged_artifacts()
    if cleaned_artifacts:
        logger.info(f"🗑️ 清理过期暂存内容 {cleaned_artifacts} 份")


@driver.on_shutdown
async def on_shutdown():
    from tools import heavens_above, rocket, satellite, space_weather, weather

    await agent_queue.aclose()
    closers = [
        message_aclose_http_client,
        heavens_above.aclose_http_client,
        rocket.aclose_http_client,
        satellite.aclose_http_client,
        space_weather.aclose_http_client,
        weather.aclose_http_client,
    ]
    for closer in closers:
        try:
            await closer()
        except Exception as exc:
            logger.warning(f"关闭 HTTP 客户端失败: {type(exc).__name__}: {exc}")


@common.handle()
async def handle_common(event: MessageEvent):  # noqa: C901
    if EnvConfig.AGENT_MODULE_ENABLED is False:
        await common.finish(f"{EnvConfig.BOT_NAME}飞升了,暂时不可用")
    bot = get_bot()
    user_id = event.get_user_id()
    user_name = event.data.sender.nickname
    event_id = event.data.message_seq
    text, images, _audio, videos = await message_extract(event.data.segments)
    group_id = event.data.group.group_id if event.data.group else None
    quoted_images: list[bytes] = []
    if reply_seq := reply_seq_from_segments(event.data.segments):
        quote_text, quoted_images = await build_reply_context(bot, event, reply_seq, group_id, messages_db)
        if quote_text:
            text += quote_text
    if videos:
        text = f"{text}\n{' '.join('[视频]' for _ in videos)}".strip()
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
        except Exception as e:
            logger.warning(f"⚠️ 图片保存失败（不影响主流程）: {e}")
    messages = await messages_db.prepare_message(
        int(user_id),
        group_id,
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
        before_time=msg_time,
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
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="351", is_add=True
                )
        case "Controversial":
            # 使用表情回复功能
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="32", is_add=True
                )
        case "Unsafe":
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="267", is_add=True
                )

    context = AgentRequestContext(
        bot=bot,
        event=event,
        user_id=user_id,
        user_name=user_name,
        event_id=event_id,
        group_id=group_id,
        msg_time=msg_time,
        text=text,
        quoted_images=quoted_images,
        images=images,
        videos=videos,
    )
    if not await _agent_choice_should_reply(context, messages):
        await common.finish()
    thread_id = _agent_thread_id(user_id, group_id)
    try:
        await agent_queue.submit(thread_id, lambda: _process_agent_request(context))
    except AgentQueueFullError:
        logger.warning(f"⚠️ Agent队列已满 用户{user_id} 群{group_id}")
        await common.finish("前面还有请求在处理，稍等一下")
