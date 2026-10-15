"""Build one explicit current request with a shared budget for inline media."""

from typing import Any

from utils.agents.message_envelope import serialize_agent_payload
from utils.media import MediaKind, resolve_media, standard_media_block
from utils.media_budget import InlineMediaBudget


def build_chat_context(
    *,
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    images: list[bytes],
    audio: list[bytes],
    videos: list[bytes],
    quoted_images: list[bytes],
    recent_images: list[bytes],
    max_bytes: int,
    max_images: int,
) -> list[dict[str, Any]]:
    """Reserve current media first, then quoted/referenced and general history."""
    payload = {
        **payload,
        "response_scope": {
            "kind": "current_request",
            "history": "background_only",
            "instruction": (
                "本轮只回应这条消息；前面的历史与引用仅作背景，不要补答其他人的问题。"
                "当前请求明确要求汇总或一起回答时除外；承接表达可结合相关前文理解。"
            ),
        },
    }
    content: list[dict[str, Any]] = [{"type": "text", "text": serialize_agent_payload(payload)}]
    budget = InlineMediaBudget(max(0, max_bytes), max(0, max_images))
    omitted = []
    groups: tuple[tuple[list[bytes], MediaKind, str, str], ...] = (
        (images, "image", "以下图片来自当前消息：", "当前图片"),
        (audio, "audio", "以下语音来自当前消息：", "当前语音"),
        (videos, "video", "以下视频来自当前消息：", "当前视频"),
        (quoted_images, "image", "以下图片来自上面的引用消息：", "引用图片"),
        (recent_images, "image", "以下图片来自用户刚才发送的历史消息：", "近期图片"),
    )
    for items, kind, label, omitted_label in groups:
        selected = [item for item in items if budget.take(item, kind)]
        if selected:
            content.append({"type": "text", "text": label})
            content.extend(standard_media_block(resolve_media(item, kind)) for item in selected)
        if len(selected) < len(items):
            omitted.append(f"{omitted_label} {len(items) - len(selected)} 项")
    if omitted:
        content.append(
            {
                "type": "text",
                "text": f"[以下媒体因上下文预算未直接内联：{'、'.join(omitted)}；如有附件路径，可按需读取]",
            }
        )
    return [
        *budget.history(history),
        {"role": "user", "content": content[0]["text"] if len(content) == 1 else content},
    ]
