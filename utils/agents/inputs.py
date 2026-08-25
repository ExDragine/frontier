"""Model input construction and capability-aware filtering."""

import logging
from typing import Literal

from utils.llm_factory import model_supports
from utils.media import (
    inline_media_bytes,
    media_block_kind,
    normalize_image_for_model,
    resolve_media,
    standard_media_block,
)

VISION_OMITTED_NOTICE = "[图片已省略：当前模型不支持视觉输入]"
INVALID_IMAGE_NOTICE = "[图片已省略：图片无效或无法转换为受支持的格式]"
MEDIA_OMITTED_NOTICES = {
    "image": VISION_OMITTED_NOTICE,
    "audio": "[语音已保存：当前模型不支持音频输入]",
    "video": "[视频已保存：当前模型不支持视频输入]",
    "file": "[文件已保存：当前模型不支持文件输入]",
}
MEDIA_CAPABILITIES = {
    "image": "vision",
    "audio": "audio",
    "video": "video",
    "file": "file",
}
logger = logging.getLogger(__name__)


def append_vision_notice(text: str) -> str:
    return f"{text}\n\n{VISION_OMITTED_NOTICE}" if text else VISION_OMITTED_NOTICE


def build_user_content(text: str, images: list[bytes] | None, supports_vision: bool = True) -> str | list:
    if not images:
        return text
    if not supports_vision:
        return append_vision_notice(text)
    return [{"type": "text", "text": text}] + [standard_media_block(resolve_media(image, "image")) for image in images]


def _normalize_inline_image_part(part: object) -> tuple[object | None, bool]:
    decoded = inline_media_bytes(part)
    if decoded is None:
        if _has_inline_payload(part):
            logger.warning("忽略无法解码的内联图片")
            return None, True
        return part, False

    normalized = normalize_image_for_model(decoded[0])
    if normalized is None:
        logger.warning("忽略 Pillow 无法识别或转换的图片")
        return None, True
    return standard_media_block(normalized), False


def _add_media_notices(filtered: list, omitted_kinds: list[str], invalid_image: bool) -> list:
    notices = [MEDIA_OMITTED_NOTICES[kind] for kind in omitted_kinds]
    if invalid_image:
        notices.append(INVALID_IMAGE_NOTICE)
    if not notices:
        return filtered
    notice_text = "\n".join(notices)
    for index, part in enumerate(filtered):
        if isinstance(part, dict) and part.get("type") == "text":
            updated_part = dict(part)
            original = str(part.get("text", ""))
            updated_part["text"] = f"{original}\n\n{notice_text}" if original else notice_text
            return [*filtered[:index], updated_part, *filtered[index + 1 :]]
    return [{"type": "text", "text": notice_text}, *filtered]


def filter_content_parts_for_model(content: list, model: str, *, role: str | None = None) -> list:
    omitted_kinds: list[str] = []
    invalid_image = False
    filtered = []
    for part in content:
        kind = media_block_kind(part)
        if kind is None:
            filtered.append(part)
            continue
        if not model_supports(model, MEDIA_CAPABILITIES[kind], role=role):
            if kind not in omitted_kinds:
                omitted_kinds.append(kind)
            continue
        if kind != "image":
            filtered.append(part)
            continue
        normalized_part, part_invalid = _normalize_inline_image_part(part)
        invalid_image = invalid_image or part_invalid
        if normalized_part is not None:
            filtered.append(normalized_part)
    return _add_media_notices(filtered, omitted_kinds, invalid_image)


def _collapse_plain_text_parts(content: list) -> str | list:
    """Use the universally supported string form when no native media remains."""
    texts: list[str] = []
    for part in content:
        if isinstance(part, str):
            texts.append(part)
            continue
        if not isinstance(part, dict) or part.get("type") not in {"text", "output_text"}:
            return content
        if set(part) - {"type", "text"}:
            return content
        texts.append(str(part.get("text", "")))
    return "\n".join(texts)


def _has_inline_payload(part: object) -> bool:
    if not isinstance(part, dict):
        return False
    if "base64" in part:
        return True
    block_type = part.get("type")
    value = part.get(block_type) if block_type == "image_url" else part.get("url")
    if isinstance(value, dict):
        value = value.get("url")
    return isinstance(value, str) and value.startswith("data:")


def filter_messages_for_model_capabilities(
    messages: list[dict],
    model: str,
    *,
    role: Literal["basic", "signal", "advanced", "daily_news"] | None = None,
) -> list[dict]:
    filtered_messages = []
    for message in messages:
        if not isinstance(message, dict):
            filtered_messages.append(message)
            continue
        content = message.get("content")
        if isinstance(content, list):
            filtered_content = filter_content_parts_for_model(content, model, role=role)
            filtered_messages.append({**message, "content": _collapse_plain_text_parts(filtered_content)})
        else:
            filtered_messages.append(message)
    return filtered_messages
