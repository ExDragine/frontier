"""内容安全策略 — 替代 utils.message.message_check() 和 sanitize_outgoing_text()。"""

from __future__ import annotations

import logging
from io import BytesIO

from PIL import Image

from policy.base import BasePolicy
from policy.decisions import Decision
from policy.snapshots import InputSnapshot, OutputSnapshot

logger = logging.getLogger(__name__)

# 延迟导入/初始化，避免启动时加载模型
_text_detector = None
_image_detector = None


async def _ensure_text_detector(model_name: str):
    global _text_detector
    if _text_detector is not None:
        return _text_detector
    from utils.context_check import TextCheck

    _text_detector = TextCheck(model_name=model_name)
    return _text_detector


async def _ensure_image_detector():
    global _image_detector
    if _image_detector is not None:
        return _image_detector
    from utils.context_check import ImageCheck

    _image_detector = ImageCheck()
    return _image_detector


class ContentSafetyPolicy(BasePolicy):
    name = "content_safety"
    severity = "safety"

    def configure(self, config: dict) -> None:
        super().configure(config)
        direction = config.get("direction", "input")
        if direction == "input":
            self._handler = self._evaluate_input  # type: ignore[assignment]
        else:
            self._handler = self._evaluate_output  # type: ignore[assignment]

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        return await self._handler(snapshot)  # type: ignore[arg-type]

    async def _evaluate_input(self, snapshot: InputSnapshot) -> Decision:
        text_model = self.config.get("text_model", "Qwen3Guard-Gen-0.6B")

        # 文本安全检查
        if snapshot.text:
            try:
                det = await _ensure_text_detector(text_model)
                safe_label, _categories = await det.predict(snapshot.text)
            except Exception:
                logger.exception("ContentSafetyPolicy text check failed")
                raise  # safety severity → engine turns into deny

            if safe_label == "Unsafe":
                return Decision.deny(
                    "unsafe_text_input",
                    message="检测到不安全内容，已拦截",
                    metadata={"reaction": self.config.get("unsafe_reaction", 26)},
                )
            if safe_label == "Controversial":
                return Decision.warn(
                    "controversial_text_input",
                    message="检测到争议内容",
                    metadata={"reaction": self.config.get("controversial_reaction", 212)},
                )

        # 图片安全检查（延迟加载）
        if snapshot.images:
            try:
                det = await _ensure_image_detector()
            except Exception:
                logger.exception("ContentSafetyPolicy image model init failed")
                raise

            for image_loader in snapshot.images:
                image_bytes = image_loader()
                if image_bytes is None:
                    continue
                try:
                    img = Image.open(BytesIO(image_bytes))
                    result = await det.predict(img)
                except Exception:
                    logger.exception("ContentSafetyPolicy image check failed")
                    raise
                if result == "nsfw":
                    return Decision.deny(
                        "unsafe_image_input",
                        message="检测到不安全图片，已拦截",
                        metadata={"reaction": self.config.get("unsafe_reaction", 26)},
                    )

        return Decision.allow(
            "input_safe",
            metadata={"reaction": self.config.get("safe_reaction", 32)},
        )

    async def _evaluate_output(self, snapshot: OutputSnapshot) -> Decision:
        if not snapshot.text:
            return Decision.allow("empty_output")

        text_model = self.config.get("text_model", "Qwen3Guard-Gen-0.6B")
        try:
            det = await _ensure_text_detector(text_model)
            safe_label, _categories = await det.predict(snapshot.text)
        except Exception:
            logger.exception("ContentSafetyPolicy output check failed")
            raise  # safety severity → engine turns into deny

        if safe_label == "Unsafe":
            return Decision.deny(
                "unsafe_text_output",
                message=self.config.get("block_message", "⚠️ 内容被安全策略拦截"),
            )
        return Decision.allow("output_safe")
