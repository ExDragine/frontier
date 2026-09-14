"""Build one explicit current request with a shared budget for inline media."""

from dataclasses import dataclass
from typing import Any

from utils.agents.message_envelope import serialize_agent_payload
from utils.media import MediaKind, inline_media_bytes, media_block_kind, resolve_media, standard_media_block


@dataclass(slots=True)
class InlineMediaBudget:
    remaining_bytes: int
    remaining_images: int

    def take(self, data: bytes, kind: str) -> bool:
        if len(data) > self.remaining_bytes or (kind == "image" and self.remaining_images <= 0):
            return False
        self.remaining_bytes -= len(data)
        if kind == "image":
            self.remaining_images -= 1
        return True

    def history(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Spend the remaining budget on newest history, without mutating it."""
        selected = []
        for message in reversed(messages):
            content = message.get("content")
            if not isinstance(content, list):
                selected.append(message)
                continue
            blocks = []
            omitted = False
            for block in content:
                kind = media_block_kind(block)
                if kind is None:
                    blocks.append(block)
                    continue
                inline = inline_media_bytes(block)
                # History contains stored bytes. Unknown-size remote URLs must
                # not silently bypass the byte budget or trigger downloads here.
                if inline is not None and self.take(inline[0], kind):
                    blocks.append(block)
                else:
                    omitted = True
            if omitted:
                blocks.append({"type": "text", "text": "[历史媒体未内联；如有附件路径，可按需读取]"})
            selected.append({**message, "content": blocks})
        return list(reversed(selected))


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
