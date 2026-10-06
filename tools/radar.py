import json
import time
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from nonebot import logger
from playwright.async_api import async_playwright

from utils.alconna import UniMessage


@tool(response_format="content")
def get_available_china_radar_areas() -> str:
    """获取静态中国雷达图支持的全部地区名称。

    当不确定 get_static_china_radar 的 area 参数时，先调用本工具。

    Returns:
        str: 按类别和多行排列的可用地区名称
    """
    area_names = list(areas)
    overview_areas = area_names[:8]
    station_areas = area_names[8:]
    lines = [
        f"可用雷达地区（{len(area_names)} 个）：",
        f"全国及分区：{'、'.join(overview_areas)}",
        "省、市及雷达站：",
    ]
    lines.extend("、".join(station_areas[index : index + 16]) for index in range(0, len(station_areas), 16))
    return "\n".join(lines)


@tool(response_format="content_and_artifact")
async def get_static_china_radar(area: str) -> tuple[Any, UniMessage | None]:
    """获取静态中国雷达图

    Args:
        area: 查询的地区名称，必须使用可用名称；不确定时先调用 get_available_china_radar_areas

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 雷达图消息段)
    """
    start_time = time.time()
    logger.info(f"🛠️ 调用工具: get_static_china_radar, 参数: area={area}")

    try:
        result = await china_static_radar(area)
        end_time = time.time()

        if result:
            logger.info(f"✅ 工具执行成功: get_static_china_radar (耗时: {end_time - start_time:.2f}s)")
            return f"成功获取{area}地区的雷达图", UniMessage.image(url=result)
        logger.info(f"❌ 工具执行失败: get_static_china_radar - 地区不存在 (耗时: {end_time - start_time:.2f}s)")
        return f"抱歉，找不到{area}地区的雷达图数据", None
    except Exception as e:
        end_time = time.time()
        logger.error(f"💥 工具执行异常: get_static_china_radar - {str(e)} (耗时: {end_time - start_time:.2f}s)")
        return f"获取{area}雷达图失败: {str(e)}", None


async def china_static_radar(area: str):
    if area not in areas:
        return None

    url = f"http://www.nmc.cn/publish/{areas[area]}"
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
            # 等待页面里目标元素出现
            try:
                await page.wait_for_selector("div.col-xs-12.time", timeout=7000)
            except Exception as e:
                # 如果超时则继续尝试获取（可能页面以不同方式渲染）
                logger.error(e)

            elements = await page.query_selector_all("div.col-xs-12.time")
            for el in elements:
                img_attr = await el.get_attribute("data-img")
                if img_attr:
                    await browser.close()
                    return img_attr

            await browser.close()
            return None
    except Exception as exc:
        logger.error(f"china_static_radar playwright error: {exc}")
        return None


# 地区名 → NMC 静态雷达页面路径；数据表见 data/radar_areas.json（保持插入顺序）。
areas: dict[str, str] = json.loads(
    (Path(__file__).resolve().parent.parent / "data" / "radar_areas.json").read_text(encoding="utf-8")
)
