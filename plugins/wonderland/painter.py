import base64
import io
from typing import Literal

from nonebot import logger
from openai import AsyncClient
from PIL import Image
from pydantic import BaseModel, Field

from utils.agents import assistant_agent
from utils.configs import EnvConfig

client = AsyncClient(base_url=EnvConfig.OPENAI_BASE_URL, api_key=EnvConfig.OPENAI_API_KEY.get_secret_value())


class PainterConfig(BaseModel):
    aspect_ratio: Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9", "none"] = Field(
        description="提示词中是否包含宽高比信息"
    )
    image_size: Literal["1K", "2K", "4K", "none"] = Field(description="提示词中是否包含图像分辨率信息")


async def extract_image(content_images) -> bytes | None:
    image_url = content_images.get("image_url")
    if not image_url:
        return None
    image_base64 = image_url.get("url")
    _, b64 = image_base64.split(",", 1)
    image_data = base64.b64decode(b64)
    image = Image.open(io.BytesIO(image_data))
    image = image.convert("RGB")
    with io.BytesIO() as output:
        image.save(output, format="JPEG", quality=95)
        return output.getvalue()


async def analyze_config(prompt: str):
    response: PainterConfig = await assistant_agent(
        system_prompt="分析用户发来的消息中的绘图配置", user_prompt=prompt, response_format=PainterConfig
    )
    aspect_ratio = None if response.aspect_ratio == "none" else response.aspect_ratio
    image_size = None if response.image_size == "none" else response.image_size
    return aspect_ratio, image_size


async def paint(
    prompt: list, aspect_ratio: str | None, image_size: str | None
) -> tuple[str | None, list[bytes | None]]:
    image_config = {}
    if aspect_ratio:
        image_config["aspect_ratio"] = aspect_ratio
    if image_size:
        image_config["image_size"] = image_size
    extra_body: dict = {"modalities": ["image", "text"]}
    if image_config:
        extra_body["image_config"] = image_config
    logger.info(f"🎨 调用绘图API, extra_body: {extra_body}")
    response = await client.chat.completions.create(
        model=EnvConfig.PAINT_MODEL,
        messages=prompt,
        stream=False,
        extra_body=extra_body,
    )
    message = response.choices[0].message.model_dump()
    logger.info(f"📦 API 原始响应: {message}")
    content = message.get("content", "")
    try:
        images: list = message.get("images", [])
        logger.info(f"🖼️  API 返回的图片数量: {len(images)}")
        logger.info(f"🔍 图片列表详情: {images}")
        images_list = []
        for idx, i in enumerate(images):
            logger.info(f"⚙️  正在处理第 {idx + 1} 张图片: {i}")
            images_list.append(await extract_image(i))
        logger.info(f"✅ 最终处理完成，共 {len(images_list)} 张图片")
        return content, images_list
    except AttributeError:
        logger.error("回复中没有包含图像")
        return content, []
