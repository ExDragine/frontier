"""Model input construction and capability-aware filtering."""

import base64
from typing import Literal

from utils.llm_factory import model_supports

VISION_OMITTED_NOTICE = "[图片已省略：当前模型不支持视觉输入]"


def append_vision_notice(text: str) -> str:
    return f"{text}\n\n{VISION_OMITTED_NOTICE}" if text else VISION_OMITTED_NOTICE


def build_user_content(text: str, images: list[bytes] | None, supports_vision: bool = True) -> str | list:
    if not images:
        return text
    if not supports_vision:
        return append_vision_notice(text)
    return [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"}}
        for image in images
    ]


def filter_content_parts_for_text_model(content: list) -> list:
    filtered = [part for part in content if not (isinstance(part, dict) and part.get("type") == "image_url")]
    if len(filtered) == len(content):
        return content
    for index, part in enumerate(filtered):
        if isinstance(part, dict) and part.get("type") == "text":
            updated_part = dict(part)
            updated_part["text"] = append_vision_notice(str(part.get("text", "")))
            return [*filtered[:index], updated_part, *filtered[index + 1 :]]
    return [{"type": "text", "text": VISION_OMITTED_NOTICE}, *filtered]


def filter_messages_for_model_capabilities(
    messages: list[dict],
    model: str,
    *,
    role: Literal["basic", "signal", "advanced"] | None = None,
) -> list[dict]:
    if model_supports(model, "vision", role=role):
        return messages
    filtered_messages = []
    for message in messages:
        if not isinstance(message, dict):
            filtered_messages.append(message)
            continue
        content = message.get("content")
        if isinstance(content, list):
            filtered_messages.append({**message, "content": filter_content_parts_for_text_model(content)})
        else:
            filtered_messages.append(message)
    return filtered_messages
