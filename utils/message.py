import io

import httpx
from nonebot import logger, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.internal.adapter import Event
from PIL import Image

from utils.agents import cognitive, reply_check
from utils.configs import EnvConfig
from utils.context_check import det, text_det
from utils.markdown_render import markdown_to_image, markdown_to_text

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)


async def message_extract(event: Event):
    message = event.get_message()
    text = event.get_message().extract_plain_text()
    images = []
    if len(message) > 1:
        for attachment in message:
            if attachment.type == "image":
                if image_url := attachment.data.get("url"):
                    response = await httpx_client.get(image_url)
                    image = response.content
                    images.append(image)
    return text, images


async def send_artifacts(artifacts):
    """发送提取到的工件"""
    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            await artifact.send()


async def send_messages(group_id: int | None, response: dict[str, list]):
    last_message = response["messages"][-1]
    if hasattr(last_message, "content") and last_message.content.strip():
        if last_message.content.startswith("系统处理出现错误"):
            result = await cognitive(
                "请告诉用户当前出现了什么问题，简短明了，不要返回敏感信息，不超过50字。", last_message.content
            )
            if result:
                await UniMessage.text(result).send()
            else:
                await UniMessage.text(last_message.content).send()
            return None
        if len(last_message.content) < 500 or str(group_id) in EnvConfig.RAW_MESSAGE_GROUP_ID:
            await UniMessage.text(await markdown_to_text(last_message.content)).send()
        else:
            result = await markdown_to_image(last_message.content)
            if result:
                await UniMessage.image(raw=result).send()


async def message_gateway(event: GroupMessageEvent | PrivateMessageEvent, messages: list):
    if isinstance(event, PrivateMessageEvent):
        return True
    if event.is_tome():
        return True
    if event.get_plaintext().startswith("小李子"):
        return True
    if event.to_me:
        return True
    if str(event.group_id) in EnvConfig.TEST_GROUP_ID:
        messages.append({"role": "user", "content": event.get_plaintext().strip()})
        temp_conv: list[dict] = messages[-5:]
        plain_conv = "\n".join(str(conv.get("content", "")) for conv in temp_conv)
        slm_reply = await reply_check(plain_conv)
        return slm_reply


async def message_check(text: str | None, images: list | None):
    if text:
        safe_label, categories = await text_det.predict(text)
        if safe_label != "Safe":
            warning_msg = (
                f"⚠️ 该消息被检测为 {safe_label}，涉及类别: {', '.join(categories) if categories else '未知'}。"
            )
            logger.info(warning_msg)
            return False
        return True
    if images:
        for image in images:
            image = Image.open(io.BytesIO(image))
            det_result = det.predict(image)[0]
            if det_result["label"] != "normal":
                logger.info(f"检测到图片类型: {det_result['label']}, 置信度为: {det_result['score']:.2f}")
                return False
            return True
