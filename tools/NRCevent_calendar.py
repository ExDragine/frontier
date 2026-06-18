"""NRC 活动日历图片获取工具。

使用 Playwright 打开 rocom.qq.com，点击"活动日历"导航项，
从页面 DOM 中提取活动日历图片链接，下载到内存后返回。
"""

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client
from utils.markdown_render import _get_browser


TARGET_URL = "https://rocom.qq.com/"
CALENDAR_DATA_INDEX = "4"
NAV_SELECTOR = f'a.nav-item[data-index="{CALENDAR_DATA_INDEX}"]'

httpx_client = get_http_client("nrc_event_calendar")


@tool(response_format="content_and_artifact")
async def get_nrc_event_calendar() -> tuple[str, UniMessage | None]:
    """获取洛克王国 NRC 活动日历图片。

    触发关键词：活动日历、NRC活动、活动排期、rocom活动、近期活动、洛克王国活动

    Returns:
        tuple[str, UniMessage | None]: (文字描述, 活动日历图片)
    """
    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": 1920, "height": 1080})

    try:
        await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        logger.info("NRC 活动日历：已打开 %s", TARGET_URL)

        nav_item = await page.wait_for_selector(NAV_SELECTOR, timeout=10000)
        if nav_item is None:
            return "未找到活动日历导航项，页面结构可能已变更", None

        await nav_item.click()
        logger.info("NRC 活动日历：已点击活动日历导航项")

        await page.wait_for_timeout(2000)
        await page.wait_for_load_state("networkidle", timeout=15000)

        # 从 nav 项的 data-index 动态推导目标 section：part-{index}
        section_class = f".part-{CALENDAR_DATA_INDEX}"
        image_selector = f"{section_class} img.picture-inner"

        img_element = await page.wait_for_selector(image_selector, timeout=10000)
        if img_element is None:
            return "未找到活动日历图片，页面结构可能已变更", None

        image_url = await img_element.get_attribute("src")
        if not image_url:
            return "活动日历图片缺少 src 属性", None

        if image_url.startswith("//"):
            image_url = "https:" + image_url

        logger.info("NRC 活动日历图片链接: %s", image_url)

        resp = await httpx_client.get(image_url)
        resp.raise_for_status()
        image_bytes = resp.content

        logger.info("NRC 活动日历图片已下载，大小: %.1f KB", len(image_bytes) / 1024)

        return "NRC 活动日历", UniMessage.image(raw=image_bytes)

    except Exception as e:
        logger.error(f"NRC 活动日历获取失败: {e}")
        return f"获取活动日历失败: {e}", None

    finally:
        await page.close()
