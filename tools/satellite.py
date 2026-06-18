import time
from typing import Literal

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client

httpx_client = get_http_client("satellite")


@tool(response_format="content_and_artifact")
async def get_fy4b_cloud_map(area: str, t: str) -> tuple[str, UniMessage | None]:
    """获取卫星云图

    Args:
        area (str): 地区英文名称。可选值包括：
            - "china": 中国地区
            - "xibei": 西北
            - "huabei": 华北
            - "neimeng": 内蒙
            - "dongbei": 东北
            - "huanghuai": 黄淮
            - "jianghuai": 江淮
            - "jiangnan": 江南
            - "jianghan": 江汉
            - "huanan": 华南
            - "xinan": 西南
            - "xizang": 西藏
            - "sea": 海域地区
            - "sea.bohai": 渤海
            - "sea.yellow": 黄海
            - "sea.east": 东海
            - "sea.taiwan.strait": 台湾海峡
            - "sea.taiwan.east": 台湾东侧
            - "sea.bashi": 巴士海峡
            - "sea.beibu": 北部湾
            - "sea.south": 南海
            如果不存在则返回全国云图

        t (str): 云图时间长度。可选值包括：
            - "3h": 3小时
            - "6h": 6小时
            - "12h": 12小时
            - "24h": 24小时
            - "48h": 48小时
            - "72h": 72小时

    Returns:
        tuple[str, Optional[MessageSegment]]: 返回一个元组，包含描述信息和视频消息段
    """
    start_time = time.time()
    logger.info(f"🛠️ 调用工具: get_fy4b_cloud_map, 参数: area={area}")

    try:
        url = f"https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/VIDEO/FY4B.{area}.{t}.mp4"
        file = (await httpx_client.get(url)).content
        result = UniMessage.video(raw=file)
        end_time = time.time()
        logger.info(f"✅ 工具执行成功: get_fy4b_cloud_map (耗时: {end_time - start_time:.2f}s)")
        return f"成功获取{area}地区的卫星云图动画（最近3小时）", result
    except Exception as e:
        end_time = time.time()
        logger.error(f"💥 工具执行异常: get_fy4b_cloud_map - {str(e)} (耗时: {end_time - start_time:.2f}s)")
        return f"获取{area}地区云图失败: {str(e)}", None


@tool(response_format="content_and_artifact")
async def get_fy4b_geos_cloud_map(
    fn: Literal["MOS", "COL", "GRA", "WVX"] | str,
    t: Literal["24h", "48h", "72h", "168h"] | str,
):
    """获取FY4B卫星全地球视角云图视频

    Args:
        fn (Literal["MOS", "COL", "GRA", "WVX"]): 云图类型: MOS, COL, GRA, WVX
        t (Literal["24h", "48h", "72h", "168h"]): 云图时长: 24h, 48h, 72h, 168h

    Returns:
        tuple[str, Optional[MessageSegment]]: 返回一个元组，包含描述信息和视频消息段
    """
    url: dict[str, str] = {
        "MOS": f"https://img.nsmc.org.cn/CLOUDIMAGE/GEOS/MOS/IRX/VIDEO/GEOS.MOS.IRX.GBAL.{t}.mp4",
        "COL": f"https://img.nsmc.org.cn/CLOUDIMAGE/GEOS/COL/IRX/VIDEO/GEOS.COL.IRX.GBAL.{t}.mp4",
        "GRA": f"https://img.nsmc.org.cn/CLOUDIMAGE/GEOS/GRA/IRX/VIDEO/GEOS.GRA.IRX.GBAL.{t}.mp4",
        "WVX": f"https://img.nsmc.org.cn/CLOUDIMAGE/GEOS/MOS/WVX/VIDEO/GEOS.MOS.WVX.GBAL.{t}.mp4",
    }
    fn2url: str | None = url.get(fn)
    if fn2url is None:
        return None
    try:
        response = await httpx_client.get(fn2url)
        response.raise_for_status()
        video_bytes: bytes = response.content
        if video_bytes:
            return "成功获取FY4B卫星全地球视角云图视频", UniMessage.video(raw=video_bytes)
    except Exception:
        return "获取FY4B卫星全地球视角云图视频失败", None


@tool(response_format="content_and_artifact")
async def get_himawari_satellite_image() -> tuple[str, UniMessage | None]:
    """获取Himawari静止气象卫星最新可见光合成图像

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 图片消息段)
    """
    start_time = time.time()
    logger.info("🛠️ 调用工具: get_himawari_satellite_image")
    try:
        result = UniMessage.image(
            url="https://www.storm-chasers.cn/wp-content/uploads/satimgs/Composite_TVIS_FDLK.jpg"
        )
        end_time = time.time()
        logger.info(f"✅ 工具执行成功: get_himawari_satellite_image (耗时: {end_time - start_time:.2f}s)")
        return "成功获取Himawari静止气象卫星最新可见光合成图像", result
    except Exception as e:
        end_time = time.time()
        logger.error(f"💥 工具执行异常: get_himawari_satellite_image - {str(e)} (耗时: {end_time - start_time:.2f}s)")
        return f"获取Himawari卫星图像失败: {str(e)}", None
