import time
from typing import Annotated, Literal

from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from nonebot import logger

from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.paint_service import PaintRateLimiter
from utils.paint_service import PaintRateLimitResult as PaintRateLimitResult
from utils.tool_helpers import ToolStateView
from utils.video_service import MediaReference as MediaReference
from utils.video_service import VideoGenerationResult as VideoGenerationResult
from utils.video_service import generate_video

video_rate_limiter = PaintRateLimiter()
VideoInputType = Literal["text", "image", "video"]


@tool(response_format="content_and_artifact")
async def get_video(
    prompt: str,
    input_type: VideoInputType = "text",
    state: Annotated[dict | None, InjectedState] = None,
) -> tuple[str, UniMessage | None]:
    """生成视频。

    Args:
        prompt: 视频生成提示词，描述要生成什么视频
        input_type: text 表示纯文字生成视频，image 表示用当前消息图片生成视频，video 表示用当前消息视频扩展视频

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 视频消息段)
    """
    start_time = time.time()
    logger.info(f"🛠️ 调用工具: video, 参数: prompt={prompt}")

    if EnvConfig.VIDEO_MODULE_ENABLED is False:
        return "视频功能没开", None

    state_view = ToolStateView(state)
    rate_limit = video_rate_limiter.check(
        state_view.user_id,
        now=time.time(),
        max_requests=EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        return f"视频生成得太快了，{rate_limit.retry_after_seconds} 秒后再试吧", None

    image_input = None
    video_input = None
    if input_type == "image":
        image_input = state_view.latest_binary("image_inputs", "image/jpeg")
        image_input = image_input or next(
            state_view.iter_media("image_url", "image_url", "data:image/", reverse=True), None
        )
    if input_type == "video":
        video_input = state_view.latest_binary("video_inputs", "video/mp4")
        video_input = video_input or next(
            state_view.iter_media("video_url", "video_url", "data:video/", reverse=True), None
        )
    if input_type == "image" and image_input is None:
        return "没有可用的图片，请在当前消息中附带图片", None
    if input_type == "video" and video_input is None:
        return "没有可用的视频，请在当前消息中附带视频", None

    generated = await generate_video(prompt, image=image_input, video=video_input)
    result = None
    if generated and generated.raw:
        result = UniMessage.video(raw=generated.raw)
    elif generated and generated.url:
        result = UniMessage.video(url=generated.url)
    end_time = time.time()
    if not result:
        logger.warning(f"⚠️ 工具执行失败: video (耗时: {end_time - start_time:.2f}s)")
        return "视频生成失败了", None

    logger.info(f"✅ 工具执行成功: video (耗时: {end_time - start_time:.2f}s)")
    return f"视频生成OK了，提示词：{prompt}", result
