import base64
import io
import os

import dotenv
from openai import AsyncClient
from PIL import Image

dotenv.load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "google/gemini-2.5-flash-image-preview"

client = AsyncClient(base_url=BASE_URL, api_key=API_KEY)


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


async def paint(prompt) -> tuple[str | None, list[bytes | None]]:
    response = await client.chat.completions.create(model=MODEL, messages=prompt, stream=False, temperature=0.7)
    message = response.choices[0].message.content
    try:
        images = response.choices[0].message.images  # type: ignore
    except AttributeError:
        images = None
    if images:  # type: ignore
        if isinstance(images, list):
            images_list = []
            for i in images:
                images_list.append(await extract_image(i))
            return message, images_list
        return message, [await extract_image(images)]  # type: ignore
    else:
        return message, []
