"""Bound inline media without mutating persisted messages."""

from dataclasses import dataclass
from typing import Any

from utils.media import inline_media_bytes, media_block_kind


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
                if inline is not None and self.take(inline[0], kind):
                    blocks.append(block)
                else:
                    omitted = True
            if omitted:
                blocks.append({"type": "text", "text": "[媒体未内联：超出本次预算或大小未知；如有附件路径，可分批读取]"})
            selected.append({**message, "content": blocks})
        return list(reversed(selected))
