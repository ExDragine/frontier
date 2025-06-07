from playwright.async_api import async_playwright
from langchain_core.tools import tool
from typing import Optional
from nonebot.adapters.qq.message import MessageSegment
from nonebot import logger
import time


@tool(response_format="content_and_artifact")
async def get_china_earthquake() -> tuple[str, Optional[MessageSegment]]:
    """获取中国地震信息

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 图片消息段)
    """
    pic_bytes = await cenc_eq_list_img()
    result = MessageSegment.file_image(pic_bytes)
    return "成功获取中国地震信息", result


@tool(response_format="content_and_artifact")
async def get_japan_earthquake() -> tuple[str, Optional[MessageSegment]]:
    """获取日本地震信息

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 图片消息段)
    """
    pic_bytes = await jma_eq_list_img()
    result = MessageSegment.file_image(pic_bytes)
    return "成功获取日本地震信息", result


async def cenc_eq_list_img():
    async with async_playwright() as p:
        browser = p.chromium
        browser = await browser.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 304, "height": 367})
        await page.goto("https://bs.wolfx.jp/CENCEQList/", timeout=60000, wait_until="networkidle")
        picture = await page.screenshot()
        await browser.close()
        return picture


async def jma_eq_list_img():
    async with async_playwright() as p:
        browser = p.chromium
        browser = await browser.launch()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 310, "height": 555})
        await page.goto("https://bs.wolfx.jp/newJMAEQList/", timeout=60000, wait_until="networkidle")
        picture = await page.screenshot()
        await browser.close()
        return picture
