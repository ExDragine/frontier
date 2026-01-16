import base64
import io
import json

from nonebot import logger
from openai import AsyncClient
from PIL import Image

from utils.configs import EnvConfig


async def paint(prompt: list) -> bytes:
    client = AsyncClient(base_url=EnvConfig.OPENAI_BASE_URL, api_key=EnvConfig.OPENAI_API_KEY.get_secret_value())
    extra_body: dict = {"modalities": ["image"]}
    logger.info(f"🎨 调用绘图API, extra_body: {extra_body}")
    response = await client.chat.completions.create(
        model="black-forest-labs/flux.2-klein-4b",
        messages=[{"role": "user", "content": prompt}],
        extra_body=extra_body,
    )
    messages = json.loads(response.choices[0].message.model_dump_json(indent=4))
    image = messages.get("images")[0].get("image_url").get("url").split(",", 1)[1]
    with io.BytesIO() as img_bytes:
        Image.open(io.BytesIO(base64.b64decode(image))).convert("RGB").save(img_bytes, format="JPEG")
        return img_bytes.getvalue()
