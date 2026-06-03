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

_DEFAULT_TEXT_MODEL = "Qwen/Qwen3Guard-Gen-0.6B"
_DEFAULT_IMAGE_MODEL = "Falconsai/nsfw_image_detection"


async def _ensure_text_detector(model_name: str):
    global _text_detector
    if _text_detector is not None:
        return _text_detector
    from utils.context_check import TextCheck

    _text_detector = TextCheck(model_name=model_name)
    return _text_detector


async def _ensure_image_detector(model_name: str):
    global _image_detector
    if _image_detector is not None:
        return _image_detector
    from utils.context_check import ImageCheck

    _image_detector = ImageCheck(model_name=model_name)
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
        text_model = self.config.get("text_model", _DEFAULT_TEXT_MODEL)
        image_model = self.config.get("image_model", _DEFAULT_IMAGE_MODEL)

        if snapshot.text and self.config.get("text_enabled", True):
            decision = await self._evaluate_input_text(snapshot.text, text_model)
            if decision is not None:
                return decision

        if snapshot.images and self.config.get("image_enabled", True):
            decision = await self._evaluate_input_images(snapshot.images, image_model)
            if decision is not None:
                return decision

        return Decision.allow(
            "input_safe",
            metadata={"reaction": self.config.get("safe_reaction", 32)},
        )

    async def _evaluate_input_text(self, text: str, text_model: str) -> Decision | None:
        try:
            det = await _ensure_text_detector(text_model)
            safe_label, _categories = await det.predict(text)
        except Exception as exc:
            decision = self._model_error_decision("text_input", exc)
            if decision is not None:
                return decision
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
        return None

    async def _evaluate_input_images(self, image_loaders, image_model: str) -> Decision | None:
        try:
            det = await _ensure_image_detector(image_model)
        except Exception as exc:
            decision = self._model_error_decision("image_init", exc)
            if decision is not None:
                return decision
            raise

        for image_loader in image_loaders:
            image_bytes = image_loader()
            if image_bytes is None:
                continue
            try:
                img = Image.open(BytesIO(image_bytes))
                result = await det.predict(img)
            except Exception as exc:
                decision = self._model_error_decision("image_input", exc)
                if decision is not None:
                    return decision
                raise
            if result == "nsfw":
                return Decision.deny(
                    "unsafe_image_input",
                    message="检测到不安全图片，已拦截",
                    metadata={"reaction": self.config.get("unsafe_reaction", 26)},
                )
        return None

    async def _evaluate_output(self, snapshot: OutputSnapshot) -> Decision:
        if not snapshot.text:
            return Decision.allow("empty_output")
        if not self.config.get("text_enabled", True):
            return Decision.allow("output_text_check_disabled")

        text_model = self.config.get("text_model", _DEFAULT_TEXT_MODEL)
        try:
            det = await _ensure_text_detector(text_model)
            safe_label, _categories = await det.predict(snapshot.text)
        except Exception as exc:
            decision = self._model_error_decision("text_output", exc)
            if decision is not None:
                return decision
            raise  # safety severity → engine turns into deny

        if safe_label == "Unsafe":
            return Decision.deny(
                "unsafe_text_output",
                message=self.config.get("block_message", "⚠️ 内容被安全策略拦截"),
            )
        return Decision.allow("output_safe")

    def _model_error_decision(self, stage: str, exc: Exception) -> Decision | None:
        mode = self.config.get("on_model_error", "deny")
        logger.exception("ContentSafetyPolicy model unavailable at %s", stage)
        if mode == "allow":
            return Decision.allow(
                "content_safety_model_unavailable",
                metadata={"stage": stage, "error": type(exc).__name__},
            )
        if mode == "warn":
            return Decision.warn(
                "content_safety_model_unavailable",
                message="内容安全检查暂时不可用",
                metadata={"stage": stage, "error": type(exc).__name__},
            )
        return None
