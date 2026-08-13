"""Model input construction and capability-aware filtering."""

from typing import Literal

from utils.llm_factory import model_supports
from utils.media import media_block_kind, resolve_media, standard_media_block

VISION_OMITTED_NOTICE = "[图片已省略：当前模型不支持视觉输入]"
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


def append_vision_notice(text: str) -> str:
    return f"{text}\n\n{VISION_OMITTED_NOTICE}" if text else VISION_OMITTED_NOTICE


def build_user_content(text: str, images: list[bytes] | None, supports_vision: bool = True) -> str | list:
    if not images:
        return text
    if not supports_vision:
        return append_vision_notice(text)
    return [{"type": "text", "text": text}] + [standard_media_block(resolve_media(image, "image")) for image in images]


def filter_content_parts_for_model(content: list, model: str, *, role: str | None = None) -> list:
    omitted_kinds: list[str] = []
    filtered = []
    for part in content:
        kind = media_block_kind(part)
        if kind is None or model_supports(model, MEDIA_CAPABILITIES[kind], role=role):
            filtered.append(part)
            continue
        if kind not in omitted_kinds:
            omitted_kinds.append(kind)

    if not omitted_kinds:
        return content
    notices = "\n".join(MEDIA_OMITTED_NOTICES[kind] for kind in omitted_kinds)
    for index, part in enumerate(filtered):
        if isinstance(part, dict) and part.get("type") == "text":
            updated_part = dict(part)
            original = str(part.get("text", ""))
            updated_part["text"] = f"{original}\n\n{notices}" if original else notices
            return [*filtered[:index], updated_part, *filtered[index + 1 :]]
    return [{"type": "text", "text": notices}, *filtered]


def filter_content_parts_for_text_model(content: list) -> list:
    """Backward-compatible helper retained for callers and older tests."""
    filtered = [part for part in content if media_block_kind(part) != "image"]
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
    filtered_messages = []
    for message in messages:
        if not isinstance(message, dict):
            filtered_messages.append(message)
            continue
        content = message.get("content")
        if isinstance(content, list):
            filtered_messages.append({**message, "content": filter_content_parts_for_model(content, model, role=role)})
        else:
            filtered_messages.append(message)
    return filtered_messages
