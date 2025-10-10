import base64
import io

import httpx
from nonebot import require
from nonebot.internal.adapter import Event
from PIL import Image

from plugins.frontier.context_check import det
from plugins.frontier.local_slm import slm_cognitive
from plugins.frontier.markdown_render import markdown_to_image, markdown_to_text

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402


async def message_extract(event: Event):
    message = event.get_message()
    texts = event.get_message().extract_plain_text()
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
                            slm_reply = await slm_cognitive(
                                "请根据系统给出的提示说一段怪话，拟人的用词，简短明了，不超过30字。",
                                f"图片里面有怪东西，置信度{det_result['score']:.2f}。",
                            )
                            if slm_reply:
                                await UniMessage.text(slm_reply).send()
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
