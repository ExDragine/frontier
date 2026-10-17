import time
from typing import Annotated, Literal, cast

from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from nonebot import logger

from utils.agent_context import FrontierRuntimeContext
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.media_access import MEDIA_ACCESS_DENIED, has_media_tool_permission
from utils.paint_service import PaintRateLimiter, paint
from utils.paint_service import PaintRateLimitResult as PaintRateLimitResult
from utils.tool_helpers import ToolStateView

PaintMode = Literal["generate", "edit"]
paint_rate_limiter = PaintRateLimiter()
_DEFAULT_CONFIG = cast(RunnableConfig, None)
_DEFAULT_RUNTIME = cast(ToolRuntime[FrontierRuntimeContext, dict], None)


@tool(response_format="content_and_artifact")
async def get_paint(
    prompt: str,
    mode: PaintMode = "generate",
    state: Annotated[dict | None, InjectedState] = None,
    config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
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
    if not has_media_tool_permission(config, runtime, policy=EnvConfig):
        return MEDIA_ACCESS_DENIED, None

    state_view = ToolStateView(state)
    rate_limit = paint_rate_limiter.check(
        state_view.user_id,
        now=time.time(),
        max_requests=EnvConfig.PAINT_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.PAINT_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        return f"画得太快了，{rate_limit.retry_after_seconds} 秒后再试吧", None

    reference_images = (
        [media.data for media in state_view.iter_media("image_url", "image_url", "data:image/")]
        if mode == "edit"
        else []
    )
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
