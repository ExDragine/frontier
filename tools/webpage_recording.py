"""网页录屏工具。

使用 Playwright 对指定网页进行视频录制，通过 browser_capture 模块复用持久化浏览器实例。
"""

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.browser_capture import record_video


@tool(response_format="content_and_artifact")
async def webpage_recording(
    url: str,
    duration: int = 10,
    width: int = 1920,
    height: int = 1080,
    wait_until: str = "networkidle",
    timeout: int = 30000,
) -> tuple[str, UniMessage | None]:
    """对指定网页进行录屏并返回视频。

    触发关键词：网页录屏、录屏、录制网页、网页录制、record、screen record

    Args:
        url: 目标网页 URL（支持 http/https 协议）
        duration: 录制时长（秒），默认 10
        width: 视口宽度（像素），默认 1920
        height: 视口高度（像素），默认 1080
        wait_until: 页面加载等待策略（load / domcontentloaded / networkidle），默认 networkidle
        timeout: 导航超时毫秒数，默认 30000

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 录屏视频)
    """
    try:
        video_bytes = await record_video(
            url=url,
            duration=duration,
            width=width,
            height=height,
            wait_until=wait_until,
            timeout=timeout,
        )
        summary = f"网页录屏完成: {url} (时长 {duration}s)"
        return summary, UniMessage.video(raw=video_bytes)
    except Exception as e:
        logger.error(f"网页录屏失败 [{url}]: {e}")
        return f"网页录屏失败: {e}", None
