"""网页录屏工具。

使用 Playwright 对指定网页进行视频录制，通过 browser_capture 模块复用持久化浏览器实例。
"""

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.browser_capture import PageLoadTimeoutError, record_video


@tool(response_format="content_and_artifact")
async def webpage_recording(
    url: str,
    duration: int = 10,
    width: int = 1920,
    height: int = 1080,
    wait_until: str = "networkidle",
    timeout: int = 30000,
    ready_timeout: int = 15000,
) -> tuple[str, UniMessage | None]:
    """录制网页视频（mp4），不是截图、不是拍照、不是快照。

    仅在用户明确要求以下操作时才调用：
    - 网页录屏 / 录屏 / 录制网页 / 网页录制 / 给网页录屏 / 录制屏幕 / 屏幕录制
    - record screen / screen record / web record
    - 给这个网页录个视频 / 把这个网页录下来 / 录一段网页视频

    绝对不要调用的情况：
    - 用户要的是截图、拍照、快照、截屏（那是另一个工具的事，与此工具无关）
    - 用户只是发了一个链接但没说录屏
    - 用户说"看看"、"打开"、"访问"某个网页
    - 任何不包含上述录屏关键词的请求

    录制过程需要约 10 秒，调用后请等待结果返回，不要中途改用其他工具。

    Args:
        url: 目标网页 URL（支持 http/https 协议）
        duration: 录制时长（秒），默认 10
        width: 视口宽度（像素），默认 1920
        height: 视口高度（像素），默认 1080
        wait_until: 页面加载等待策略（load / domcontentloaded / networkidle），默认 networkidle
        timeout: 导航超时毫秒数，默认 30000
        ready_timeout: 页面就绪超时毫秒数，默认 15000

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
            ready_timeout=ready_timeout,
        )
        summary = f"网页录屏完成: {url} (时长 {duration}s)"
        return summary, UniMessage.video(raw=video_bytes)
    except PageLoadTimeoutError as e:
        logger.warning(f"网页加载超时 [{url}]: {e}")
        return f"网站加载超时，以下是当前状态截图: {url}", UniMessage.image(raw=e.screenshot_bytes)
    except Exception as e:
        logger.error(f"网页录屏失败 [{url}]: {e}")
        return f"网页录屏失败: {e}", None
