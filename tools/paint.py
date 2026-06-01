import base64
import time
from typing import Annotated, Literal

from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from nonebot import logger

from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.paint_service import PaintRateLimiter, paint
from utils.paint_service import PaintRateLimitResult as PaintRateLimitResult
from utils.tool_helpers import (
    decode_data_url,
    latest_user_message_content,
    media_part_url,
    state_user_id,
)

PaintMode = Literal["generate", "edit"]
paint_rate_limiter = PaintRateLimiter()


def _reference_images_from_state(state: dict | None) -> list[bytes]:
    content = latest_user_message_content(state)
    if not isinstance(content, list):
        return []

    images: list[bytes] = []
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "image_url":
            continue
        url = media_part_url(part, "image_url")
        if not url:
            continue
        ref = decode_data_url(url, expected_prefix="data:image/")
        if ref:
            images.append(ref.data)
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
        state_user_id(state),
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
