"""网页截图工具。

使用 Playwright 对指定网页进行截图，通过 browser_capture 模块复用持久化浏览器实例。
"""

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.browser_capture import screenshot


@tool(response_format="content_and_artifact")
async def webpage_screenshot(
    url: str,
    width: int = 1280,
    height: int = 720,
    full_page: bool = False,
    selector: str | None = None,
    wait_until: str = "networkidle",
    timeout: int = 30000,
) -> tuple[str, UniMessage | None]:
    """对指定网页进行截图并返回图片。

    ⚠️ 仅在用户明确要求对指定网页截图时调用，包括：
    - 明确说"截图"、"网页截图"、"给网页拍照"、"网页快照"等，且给出了具体网址
    - 例："帮我截百度首页的图"、"给 https://example.com 拍个照"

    以下情况绝对不要调用：
    - 用户只是提到"截图"二字但并非要求对网页截图（如"你看这个截图"）
    - 用户问你能不能截图、有没有截图功能
    - 对话中不包含明确网页截图意图

    Args:
        url: 目标网页 URL（支持 http/https 协议）
        width: 视口宽度（像素），默认 1280
        height: 视口高度（像素），默认 720
        full_page: 是否截取完整页面，默认 False 仅截取视口区域
        selector: 仅截取指定 CSS 选择器对应的元素，为 None 时截取整个页面
        wait_until: 页面加载等待策略（load / domcontentloaded / networkidle），默认 networkidle
        timeout: 导航超时毫秒数，默认 30000

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 网页截图)
    """
    try:
        image_bytes = await screenshot(
            url=url,
            width=width,
            height=height,
            full_page=full_page,
            selector=selector,
            wait_until=wait_until,
            timeout=timeout,
        )
        summary = f"网页截图完成: {url}"
        if selector:
            summary += f" (元素: {selector})"
        return summary, UniMessage.image(raw=image_bytes)
    except Exception as e:
        logger.error(f"网页截图失败 [{url}]: {e}")
        return f"网页截图失败: {e}", None
