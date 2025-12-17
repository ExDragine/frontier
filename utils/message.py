import ast
import asyncio

import httpx
from nonebot import logger, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import ActionFailed
from nonebot.internal.adapter import Event
from pydantic import BaseModel, Field

from utils.agents import assistant_agent
from utils.configs import EnvConfig

# from utils.context_check import ImageCheck, TextCheck
from utils.markdown_render import markdown_to_image, markdown_to_text

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)
# text_det = TextCheck()
# image_det = ImageCheck()


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with true, either reply with false"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


async def message_extract(event: Event):
    message = event.get_message()
    text = event.get_message().extract_plain_text()
    images, audio, video, shared_link = [], [], [], []
    if len(message) > 1:
        for attachment in message:
            match attachment.type:
                case "image":
                    if image_url := attachment.data.get("url"):
                        images.append((await httpx_client.get(image_url)).content)
                case "record":
                    if image_url := attachment.data.get("url"):
                        audio.append((await httpx_client.get(image_url)).content)
                case "video":
                    if image_url := attachment.data.get("url"):
                        video.append((await httpx_client.get(image_url)).content)
                case "share":
                    if image_url := attachment.data.get("url"):
                        shared_link.append((await httpx_client.get(image_url)).content)
                case _:
                    pass
    return text, images


async def send_artifacts(artifacts):
    """发送提取到的工件（并行发送）"""

    tasks = []
    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            try:
                tasks.append(asyncio.create_task(artifact.send()))
            except Exception as e:
                logger.exception("创建发送任务失败: %s", e)

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            logger.exception("发送工件时发生错误: %s", res)


async def send_messages(group_id: int | None, message_id, response: dict[str, list]):
    if content := response["messages"][-1].content:
        try:
            content = ast.literal_eval(content)["content"]
        except Exception:
            content = content
        # _ = await text_det.predict(content)
        if len(content) < 500 or group_id in EnvConfig.RAW_MESSAGE_GROUP_ID:
            messages = UniMessage.reply(str(message_id)) + UniMessage.text(
                (await markdown_to_text(content)).rstrip("\r\n").strip()
            )
            try:
                await messages.send()
            except ActionFailed:
                result = await markdown_to_image(content)
                messages = UniMessage.reply(str(message_id)) + UniMessage.image(raw=result)
                if result:
                    await messages.send()
        else:
            result = await markdown_to_image(content)
            messages = UniMessage.reply(str(message_id)) + UniMessage.image(raw=result)
            if result:
                await messages.send()


async def message_gateway(event: GroupMessageEvent | PrivateMessageEvent, messages: list):
    group_id = event.group_id if isinstance(event, GroupMessageEvent) else 0
    if EnvConfig.AGENT_WITHELIST_MODE and group_id in EnvConfig.AGENT_WITHELIST_GROUP_LIST:
        pass
    if group_id in EnvConfig.AGENT_BLACKLIST_GROUP_LIST:
        return False
    if EnvConfig.AGENT_WITHELIST_MODE and event.user_id in EnvConfig.AGENT_WITHELIST_PERSON_LIST:
        pass
    if event.user_id in EnvConfig.AGENT_BLACKLIST_PERSON_LIST:
        return False
    if event.is_tome() or event.to_me:
        return True
    if event.get_plaintext().startswith(EnvConfig.BOT_NAME):
        return True
    if group_id in EnvConfig.TEST_GROUP_ID:
        messages.append({"role": "user", "content": str({"metadata": {}, "content": event.get_plaintext().strip()})})
        temp_conv: list[dict] = messages[-5:]
        plain_conv = "\n".join(str(conv.get("content", "")) for conv in temp_conv)
        with open("prompts/reply_check.txt") as f:
            system_prompt = f.read().format(name={EnvConfig.BOT_NAME})
        reply_check: ReplyCheck = await assistant_agent(system_prompt, plain_conv, response_format=ReplyCheck)
        return True if reply_check.should_reply == "true" and reply_check.confidence > 0.5 else False
    return False


# async def message_check(text: str | None, images: list | None):
#     if text:
#         safe_label, categories = await text_det.predict(text)
#         if safe_label != "Safe":
#             warning_msg = (
#                 f"⚠️ 该消息被检测为 {safe_label}，涉及类别: {', '.join(categories) if categories else '未知'}。"
#             )
#             logger.info(warning_msg)
#             return False
#         return True
#     if images:
#         for image in images:
#             image = Image.open(io.BytesIO(image))
#             det_result = await image_det.predict(image)
#             if not det_result:
#                 return True
#             if det_result["label"] == "nsfw":
#                 logger.info(f"检测到瑟瑟, 置信度为: {det_result['score']:.2f}")
#                 return False
#             return True
#     return True
