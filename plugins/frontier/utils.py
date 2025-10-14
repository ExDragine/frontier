import base64
import io
import os
import secrets

import dotenv
import httpx
from nonebot import logger, require
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent
from nonebot.internal.adapter import Event
from PIL import Image

from plugins.frontier.context_check import det, text_det
from plugins.frontier.markdown_render import markdown_to_image, markdown_to_text
from plugins.frontier.slm import slm_cognitive

dotenv.load_dotenv()
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

TEST_TARGET = os.getenv("TEST_TARGET", "")


async def message_extract(event: Event):
    message = event.get_message()
    texts = event.get_message().extract_plain_text()
    safe_label, categories = await text_det.predict(texts)
    if safe_label != "Safe":
        warning_msg = f"⚠️ 该消息被检测为 {safe_label}，涉及类别: {', '.join(categories) if categories else '未知'}。"
        logger.info(warning_msg)
    images = []
    if len(message) > 1:
        for attachment in message:
            if attachment.type == "image":
                if image_url := attachment.data.get("url"):
                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.get(image_url)
                        except httpx.ReadTimeout:
                            response = await client.get(image_url)
                        sample = response.content
                        image = Image.open(io.BytesIO(sample))
                        det_result = det.predict(image)[0]
                        if det_result["label"] != "normal":
                            logger.info(f"检测到图片类型: {det_result['label']}, 置信度为: {det_result['score']:.2f}")
                        images.append(
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64.b64encode(sample).decode()}",
                            }
                        )
    return texts, images


async def send_artifacts(artifacts):
    """发送提取到的工件"""
    for artifact in artifacts:
        if isinstance(artifact, UniMessage):
            await artifact.send()


async def send_messages(response: dict[str, list]):
    last_message = response["messages"][-1]
    if hasattr(last_message, "content") and last_message.content.strip():
        if last_message.content.startswith("系统处理出现错误"):
            result = await slm_cognitive(
                "请告诉用户当前出现了什么问题，简短明了，不要返回敏感信息，不超过50字。", last_message.content
            )
            if result:
                await UniMessage.text(result).send()
            else:
                await UniMessage.text(last_message.content).send()
            return None
        if len(last_message.content) > 500:
            try:
                result = await markdown_to_image(last_message.content)
                if result:
                    await UniMessage.image(raw=result).send()
            except Exception as e:
                await UniMessage.text(f"貌似出了点问题: {e}").send()
        else:
            try:
                await UniMessage.text(await markdown_to_text(last_message.content)).send()
            except Exception:
                # await UniMessage.text(f"貌似出了点问题: {e}").send()
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
    if event.group_id == int(TEST_TARGET) and secrets.randbelow(5) == 1:
        messages.append({"role": "user", "content": event.get_plaintext().strip()})
        temp_conv: list[dict] = messages[-5:]
        plain_conv = "\n".join(str(conv.get("content", "")) for conv in temp_conv)
        slm_reply = await slm_cognitive(
            "请判断当前对话内容是否适合插话，是则返回 YES 不是则返回 NO, 只返回这两个结果",
            plain_conv,
        )
        if slm_reply == "YES":
            return True
    return False
