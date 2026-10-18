"""Local speech synthesis with automatically delivered QQ voice artifacts."""

import time
from typing import cast

from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from nonebot import logger

from utils.agent_context import FrontierRuntimeContext
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.media_access import MEDIA_ACCESS_DENIED, has_media_tool_permission
from utils.milky_tools import configurable
from utils.paint_service import PaintRateLimiter
from utils.speech_synthesis import SpeechSynthesisError, synthesize_speech

speech_rate_limiter = PaintRateLimiter()
_DEFAULT_CONFIG = cast(RunnableConfig, None)
_DEFAULT_RUNTIME = cast(ToolRuntime[FrontierRuntimeContext, dict], None)


@tool(response_format="content_and_artifact")
async def get_speech(
    text: str,
    config: RunnableConfig = _DEFAULT_CONFIG,
    runtime: ToolRuntime[FrontierRuntimeContext, dict] = _DEFAULT_RUNTIME,
) -> tuple[str, UniMessage | None]:
    """将文字转换为本地合成的中文语音，仅在用户明确要求语音或朗读时调用。

    Args:
        text: 要朗读的原文，默认最多 300 字；不要包含排版标记、链接或过程说明。

    Returns:
        语音工件由系统在本轮最终回复时自动发送，无需再调用 send_voice 或 send_audio。
        返回工件不代表已经送达，不要编造文件路径。
    """
    settings = EnvConfig.SPEECH_SYNTHESIS
    if not settings.enabled:
        return "本地语音合成未启用", None
    if not has_media_tool_permission(config, runtime, policy=EnvConfig):
        return MEDIA_ACCESS_DENIED, None
    context = getattr(runtime, "context", None)
    user_id = context.user_id if isinstance(context, FrontierRuntimeContext) else configurable(config).get("user_id")
    limit = speech_rate_limiter.check(
        str(user_id or "anonymous"),
        now=time.time(),
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    if not limit.allowed:
        return f"语音生成太频繁，请 {limit.retry_after_seconds} 秒后再试", None
    try:
        result = await synthesize_speech(text, settings=settings)
    except SpeechSynthesisError as exc:
        logger.warning("本地语音合成失败 code={}", exc.code)
        return f"语音生成失败，错误码：{exc.code}；可改用文字回复。", None
    logger.info(
        "本地语音合成完成 audio_seconds={:.2f} elapsed_seconds={:.2f} chars={}",
        result.audio_seconds,
        result.elapsed_seconds,
        len(text),
    )
    return "语音已加入本轮回复，将自动发送，无需再调用 send_voice 或 send_audio。", UniMessage.voice(raw=result.silk)
