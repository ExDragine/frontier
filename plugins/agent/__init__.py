import base64
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from nonebot import get_bot, get_driver, logger, on_message, require
from nonebot.adapters.milky.event import MessageEvent

from utils.agent_queue import AgentQueueFullError, AgentQueueManager
from utils.agents import NO_REPLY_SENTINEL, FrontierCognitive, _agent_thread_id
from utils.configs import EnvConfig
from utils.database import MessageDatabase, build_message_metadata
from utils.message import (
    aclose_http_client as message_aclose_http_client,
)
from utils.message import (
    message_check,
    message_extract,
    message_gateway,
    outgoing_message_content,
    sanitize_outgoing_text,
    send_artifacts,
    send_messages,
)
from utils.min_heap import RepeatMessageHeap
from utils.reply_context import build_reply_context, reply_seq_from_segments

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

messages_db = MessageDatabase()
f_cognitive = FrontierCognitive()
driver = get_driver()

common = on_message(priority=10)

message_heap = RepeatMessageHeap(capacity=10, threshold=2)
agent_queue = AgentQueueManager(
    maxsize=5,
    idle_ttl_seconds=1800.0,
    job_timeout_seconds=EnvConfig.AGENT_JOB_TIMEOUT_SECONDS,
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_NO_REPLY_SENTINEL = NO_REPLY_SENTINEL
# 匹配原始回复文本中的哨兵：独立文本或 JSON 字符串值
_AGENT_NO_REPLY_RE = re.compile(rf'^\s*{re.escape(NO_REPLY_SENTINEL)}\s*$|"{re.escape(NO_REPLY_SENTINEL)}"')


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



async def _process_agent_request(context: AgentRequestContext, history_messages: list[dict] | None = None) -> bool:
    messages = list(history_messages or [])
    messages += [
        {
            "role": "user",
            "content": ("以上是对话历史，仅用于理解上下文。"),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "metadata": build_message_metadata(
                                timestamp_ms=context.msg_time,
                                user_id=context.user_id,
                                group_id=context.group_id,
                                user_name=context.user_name,
                            ),
                            "is_current": True,
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
        },
    ]
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
        return True

    response = result["response"]
    if not response:
        await UniMessage.text(f"{EnvConfig.BOT_NAME}飞升了，暂时不可用").send()
        return True

    if result.get("error"):
        logger.warning("Agent returned error response: %s", result["error"])

    if response["messages"] and isinstance(response["messages"], list):
        raw_text = str(getattr(response["messages"][-1], "text", "") or "")
        if _AGENT_NO_REPLY_RE.search(raw_text):
            logger.info("Agent chose not to reply to the latest message.")
            return False

    artifacts: list[UniMessage] | None = result.get("uni_messages", [])
    if artifacts:
        logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
        await send_artifacts(artifacts)

    if response["messages"] and isinstance(response["messages"], list):
        response_content = outgoing_message_content(response["messages"][-1])
        sanitized_response = await sanitize_outgoing_text(response_content)
        if sanitized_response != response_content:
            response["messages"][-1] = SimpleNamespace(text=sanitized_response)
        await messages_db.insert(
            time=int(time.time() * 1000),
            msg_id=None,
            user_id=int(context.event.self_id),
            group_id=context.group_id,
            user_name="Assistant",
            role="assistant",
            content=outgoing_message_content(response["messages"][-1]),
        )
        await send_messages(context.group_id, context.event_id, response)
    else:
        await UniMessage.text(response["messages"]).send()
    return True


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
                    group_id=group_id, message_seq=event_id, reaction="32", is_add=True
                )
        case "Controversial":
            # 使用表情回复功能
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="212", is_add=True
                )
        case "Unsafe":
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="26", is_add=True
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
    thread_id = _agent_thread_id(user_id, group_id)
    try:
        # if group_id:
        #     await bot.send_group_message_reaction(group_id=group_id, message_seq=event_id, reaction="351", is_add=True)
        agent_queue.job_timeout_seconds = EnvConfig.AGENT_JOB_TIMEOUT_SECONDS
        replied = await agent_queue.submit(thread_id, lambda: _process_agent_request(context, messages))
        if group_id:
            # await bot.send_group_message_reaction(
            #     group_id=group_id, message_seq=event_id, reaction="351", is_add=False
            # )
            if not replied:
                if not group_id:
                    return
                match risk_check:
                    case "Safe":
                        await bot.send_group_message_reaction(
                            group_id=group_id, message_seq=event_id, reaction="32", is_add=False
                        )
                    case "Controversial":
                        await bot.send_group_message_reaction(
                            group_id=group_id, message_seq=event_id, reaction="212", is_add=False
                        )
                    case "Unsafe":
                        await bot.send_group_message_reaction(
                            group_id=group_id, message_seq=event_id, reaction="26", is_add=False
                        )
                await common.finish()
            await bot.send_group_message_reaction(group_id=group_id, message_seq=event_id, reaction="32", is_add=False)
    except AgentQueueFullError:
        logger.warning(f"⚠️ Agent队列已满 用户{user_id} 群{group_id}")
        await common.finish("前面还有请求在处理，稍等一下")
