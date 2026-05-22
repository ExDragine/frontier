import base64
import time
from typing import Annotated, Literal

from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from nonebot import logger, require

from utils.configs import EnvConfig
from utils.paint_service import PaintRateLimiter, paint
from utils.paint_service import PaintRateLimitResult as PaintRateLimitResult

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

PaintMode = Literal["generate", "edit"]
paint_rate_limiter = PaintRateLimiter()


def _state_user_id(state: dict | None) -> str:
    if not isinstance(state, dict):
        return "tool"
    user_id = state.get("user_id")
    if user_id is None and isinstance(state.get("context"), dict):
        user_id = state["context"].get("user_id")
    return str(user_id or "tool")


def _message_role(message) -> str | None:
    if isinstance(message, dict):
        role = message.get("role")
    else:
        role = getattr(message, "role", None) or getattr(message, "type", None)
    return str(role) if role is not None else None


def _message_content(message):
    if isinstance(message, dict):
        return message.get("content")
    return getattr(message, "content", None)


def _latest_user_message_content(state: dict | None):
    if not isinstance(state, dict):
        return None
    messages = state.get("messages")
    if not isinstance(messages, list):
        return None
    for message in reversed(messages):
        if _message_role(message) in {"user", "human"}:
            return _message_content(message)
    return None


def _decode_data_image_url(url: str) -> bytes | None:
    if not url.startswith("data:image/") or "," not in url:
        return None
    header, payload = url.split(",", 1)
    if ";base64" not in header:
        return None
    try:
        return base64.b64decode(payload, validate=True)
    except Exception:
        return None


def _image_part_url(part: dict) -> str | None:
    image_url = part.get("image_url")
    if isinstance(image_url, str):
        return image_url
    if isinstance(image_url, dict):
        url = image_url.get("url")
        return url if isinstance(url, str) else None
    return None


def _reference_images_from_state(state: dict | None) -> list[bytes]:
    content = _latest_user_message_content(state)
    if not isinstance(content, list):
        return []

    images: list[bytes] = []
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "image_url":
            continue
        url = _image_part_url(part)
        if not url:
            continue
        if image := _decode_data_image_url(url):
            images.append(image)
    return images


@tool(response_format="content_and_artifact")
async def get_paint(
    prompt: str,
    mode: PaintMode = "generate",
    state: Annotated[dict | None, InjectedState] = None,
) -> tuple[str, UniMessage | None]:
    """生成或编辑图片。

    Args:
        prompt: 绘画提示词，描述要生成或修改成什么样子
        mode: generate 表示纯文字生成图片，edit 表示使用当前消息或引用消息中的图片作为参考进行编辑

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 图片消息段)
    """
    start_time = time.time()
    logger.info(f"🛠️ 调用工具: paint, 参数: mode={mode}, prompt={prompt}")

    if EnvConfig.PAINT_MODULE_ENABLED is False:
        return "绘画功能未启用", None

    rate_limit = paint_rate_limiter.check(
        _state_user_id(state),
        now=time.time(),
        max_requests=EnvConfig.PAINT_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.PAINT_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        return f"画得太快了，{rate_limit.retry_after_seconds} 秒后再试吧", None

    reference_images = _reference_images_from_state(state) if mode == "edit" else []
    if mode == "edit" and not reference_images:
        return "没有可编辑的图片，请在当前消息中附带图片或回复引用一张图片", None

    image = await paint(prompt, reference_images)
    end_time = time.time()
    if not image:
        logger.warning(f"⚠️ 工具执行失败: paint (耗时: {end_time - start_time:.2f}s)")
        return "图片生成失败", None

    result = UniMessage.image(raw=image)
    action = "编辑" if mode == "edit" else "生成"
    logger.info(f"✅ 工具执行成功: paint (耗时: {end_time - start_time:.2f}s)")
    return f"成功{action}图片，提示词：{prompt}", result
