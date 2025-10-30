import base64
import time

from nonebot import logger, on_message, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent

from utils.agents import FrontierCognitive
from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.message import (
    message_check,
    message_extract,
    message_gateway,
    send_artifacts,
    send_messages,
)

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

messages_db = MessageDatabase()
cognitive = FrontierCognitive()

common = on_message(priority=10)


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
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
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
    result = await cognitive.chat_agent(messages, user_id, user_name)
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
            await send_messages(group_id, response)
        else:
            await UniMessage.text(response["messages"]).send()
