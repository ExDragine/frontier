import base64
import time
from typing import Annotated, Literal

from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from nonebot import logger, require

from utils.configs import EnvConfig
from utils.paint_service import PaintRateLimiter
from utils.paint_service import PaintRateLimitResult as PaintRateLimitResult
from utils.staged_artifacts import stage_artifact_response
from utils.video_service import MediaReference, VideoGenerationResult, generate_video

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

video_rate_limiter = PaintRateLimiter()
VideoInputType = Literal["text", "image", "video"]


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


def _decode_data_url(url: str, *, expected_prefix: str) -> MediaReference | None:
    if not url.startswith(expected_prefix) or "," not in url:
        return None
    header, payload = url.split(",", 1)
    if ";base64" not in header:
        return None
    mime_type = header.removeprefix("data:").split(";", 1)[0]
    try:
        return MediaReference(data=base64.b64decode(payload, validate=True), mime_type=mime_type)
    except Exception:
        return None


def _media_part_url(part: dict, key: str) -> str | None:
    value = part.get(key)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        url = value.get("url")
        return url if isinstance(url, str) else None
    return None


def _latest_media_from_state(state: dict | None, *, part_type: str, key: str, expected_prefix: str) -> MediaReference | None:
    content = _latest_user_message_content(state)
    if not isinstance(content, list):
        return None

    for part in reversed(content):
        if not isinstance(part, dict) or part.get("type") != part_type:
            continue
        url = _media_part_url(part, key)
        if not url:
            continue
        if media := _decode_data_url(url, expected_prefix=expected_prefix):
            return media
    return None


def _latest_image_from_state(state: dict | None) -> MediaReference | None:
    if isinstance(state, dict):
        image_inputs = state.get("image_inputs")
        if isinstance(image_inputs, list):
            for image in reversed(image_inputs):
                if isinstance(image, bytes):
                    return MediaReference(data=image, mime_type="image/jpeg")
    return _latest_media_from_state(
        state,
        part_type="image_url",
        key="image_url",
        expected_prefix="data:image/",
    )


def _latest_video_from_state(state: dict | None) -> MediaReference | None:
    if isinstance(state, dict):
        video_inputs = state.get("video_inputs")
        if isinstance(video_inputs, list):
            for video in reversed(video_inputs):
                if isinstance(video, bytes):
                    return MediaReference(data=video, mime_type="video/mp4")
    return _latest_media_from_state(
        state,
        part_type="video_url",
        key="video_url",
        expected_prefix="data:video/",
    )


def _video_result_message(video: VideoGenerationResult | None) -> UniMessage | None:
    if video is None:
        return None
    if video.raw:
        return UniMessage.video(raw=video.raw)
    if video.url:
        return UniMessage.video(url=video.url)
    return None


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

    rate_limit = video_rate_limiter.check(
        _state_user_id(state),
        now=time.time(),
        max_requests=EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        return f"视频生成得太快了，{rate_limit.retry_after_seconds} 秒后再试吧", None

    image_input = _latest_image_from_state(state) if input_type == "image" else None
    video_input = _latest_video_from_state(state) if input_type == "video" else None
    if input_type == "image" and image_input is None:
        return "没有可用的图片，请在当前消息中附带图片", None
    if input_type == "video" and video_input is None:
        return "没有可用的视频，请在当前消息中附带视频", None

    generated = await generate_video(prompt, image=image_input, video=video_input)
    result = _video_result_message(generated)
    end_time = time.time()
    if not result:
        logger.warning(f"⚠️ 工具执行失败: video (耗时: {end_time - start_time:.2f}s)")
        return "视频生成失败了", None

    logger.info(f"✅ 工具执行成功: video (耗时: {end_time - start_time:.2f}s)")
    return stage_artifact_response(f"视频生成OK了，提示词：{prompt}", result)
