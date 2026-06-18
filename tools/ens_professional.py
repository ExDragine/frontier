"""Earth Nullschool 专业模式工具。

数字参数接口：用户通过编号选择选项，LLM/用户按 "vep" 触发。
所有模式默认播放动画，用户可传 animoff 暂停。
"""

import re

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.browser_capture import record_video, screenshot
from utils.tool_helpers import tool_timer

# ── 模式编号 → 中文名 ──
_MODE_NAMES = {1: "大气", 2: "海洋", 3: "大气化学", 4: "颗粒物", 5: "空间天气", 6: "生物"}

_NULLSCHOOL_LOADING_WAIT = (
    "(function(){var l=document.getElementById('load');if(!l)return true;"
    "var s=window.getComputedStyle(l);return s.display==='none'||s.visibility==='hidden';})()"
)

# ── 参数映射表 ──

_MODE = {1: "wind", 2: "ocean", 3: "chem", 4: "particulates", 5: "space", 6: "bio"}

_HEIGHT = {
    0: "surface",
    1: "isobaric/10hPa",
    2: "isobaric/70hPa",
    3: "isobaric/250hPa",
    4: "isobaric/500hPa",
    5: "isobaric/700hPa",
    6: "isobaric/850hPa",
    7: "isobaric/1000hPa",
}

_ANIM = {1: "level", 2: "currents", 3: "primary/waves"}

_PROJ = {
    1: "orthographic",
    2: "equirectangular",
    3: "conic_equidistant",
    4: "atlantis",
    5: "patterson",
    6: "stereographic",
    7: "waterman",
    8: "winkel3",
}

# 叠加层按模式分表
_OVERLAY = {
    "wind": {
        0: None,
        1: None,
        2: "temp",
        3: "relative_humidity",
        4: "dew_point_temp",
        5: "wet_bulb_temp",
        6: "precip_3hr",
        7: "cape",
        8: "total_precipitable_water",
        9: "total_cloud_water",
        10: "mean_sea_level_pressure",
        11: "misery_index",
        12: "uv_index",
        13: "wind_power_density",
    },
    "ocean": {
        0: None,
        1: None,
        2: "primary_waves",
        3: "significant_wave_height",
        4: "sea_surface_temp",
        5: "sea_surface_temp_anomaly",
        6: "bleaching_alert_area",
    },
    "chem": {1: "cosc", 2: "co2sc", 3: "so2smass", 4: "no2"},
    "particulates": {1: "duexttau", 2: "pm1", 3: "pm2.5", 4: "pm10", 5: "organic_matter_aot", 6: "suexttau"},
    "space": {1: "aurora"},
    "bio": {0: None, 1: "bleaching_alert_area"},
}

_BIO_ANNOT = {0: None, 1: "fires"}

_ZOOM_DEFAULT = {"wind": 4500, "ocean": 300, "chem": 4500, "particulates": 4500, "space": 800, "bio": 1500}

# 测试环境无法跨文件导入 _CITY_COORDS 时的 fallback
_CITY_COORDS_FALLBACK: dict[str, tuple[float, float]] = {
    "北京": (116.40, 39.90),
    "上海": (121.47, 31.23),
    "广州": (113.26, 23.13),
    "深圳": (114.07, 22.62),
    "成都": (104.07, 30.67),
    "杭州": (120.15, 30.28),
}


def _build_professional_url(
    mode: str,
    animation: str,
    projection: str,
    lon: float,
    lat: float,
    zoom: int,
    time: str = "#current",
    height: str = "surface",
    overlay: str | None = None,
    annot: str | None = None,
    paused: bool = False,
) -> str:
    """拼接 hash-fragment URL。"""
    segments = [time, mode, height, animation]

    if annot:
        segments.append(f"annot={annot}")
    if paused:
        segments.append("anim=off")
    if overlay is not None:
        segments.append(f"overlay={overlay}")

    path = "/".join(segments)
    view = f"{projection}={lon},{lat},{zoom}"
    loc = f"loc={lon},{lat}"

    return f"https://earth.nullschool.net/zh-cn/{path}/{view}/{loc}"


def _parse_time(raw: str) -> str:
    """将 YYYYMMDD.HHMM 转为 #YYYY/MM/DD/HHMMZ。空或'0'返回 #current。"""
    if not raw or raw.strip() in ("", "0"):
        return "#current"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})\.(\d{2})(\d{2})$", raw.strip())
    if not m:
        raise ValueError(f"时间格式错误: {raw}，应为 YYYYMMDD.HHMM（如 20261001.1200）")
    return f"#{m[1]}/{m[2]}/{m[3]}/{m[4]}{m[5]}Z"


def _format_time_text(time: str) -> str:
    """将 URL 时间片段转为用户可读文本。"""
    if time == "#current":
        return "现在"
    m = re.match(r"^#(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})Z$", time)
    if m:
        y, mo, d, h, mi = m.groups()
        return f"{y}年{int(mo)}月{int(d)}日{h}:{mi}"
    return time


async def run_ens_professional(
    p1: int = 1,
    p2: int = 0,
    p3: int = 1,
    p4: int = 0,
    p5: int = 1,
    p6: str = "0",
    p7: str = "0",
    p8: int = 0,
    p9: str = "0",
    p10: str = "0",
    bio_annot: int = 0,
) -> tuple[str, UniMessage | None]:
    """专业模式核心逻辑。"""
    try:
        mode = _MODE.get(p1)
        if mode is None:
            return f"无效模式编号: {p1}（1-6）", None

        height = _HEIGHT.get(p2, "surface")
        animation = _ANIM.get(p3)
        if animation is None:
            return f"无效动画编号: {p3}（1-3）", None

        projection = _PROJ.get(p5)
        if projection is None:
            return f"无效投影编号: {p5}（1-8）", None

        overlay_table = _OVERLAY.get(mode, {})
        overlay = overlay_table.get(p4)
        if p4 != 0 and overlay is None and p4 not in overlay_table:
            return f"无效叠加层编号: {p4}（该模式下无此选项）", None

        annot = None
        if mode == "bio" and bio_annot:
            annot = _BIO_ANNOT.get(bio_annot)
            if annot is None:
                return f"无效生物注释编号: {bio_annot}（0-1）", None

        # 坐标解析：支持数字经纬度或城市名
        location_text: str  # 用于返回消息
        try:
            lon = float(p6)
            lat = float(p7)
            if lon == 0 and lat == 0:
                return "请提供有效的经纬度坐标或城市名（如：北京、广州）", None
            location_text = f"({lon}, {lat})"
        except ValueError:
            # 非数字 → 作为城市名查找。优先用 ens_normal 字典，测试环境 fallback 小字典
            try:
                from .ens_normal import _CITY_COORDS as _coords
            except ImportError:
                try:
                    from tools.ens_normal import _CITY_COORDS as _coords  # type: ignore[no-redef]
                except ImportError:
                    _coords = _CITY_COORDS_FALLBACK
            location = p6.strip()
            if not location:
                return "请提供有效的经纬度坐标或城市名", None
            location_text = location
            if location in _coords:
                lon, lat = _coords[location]
            else:
                matched = None
                for city, coords in sorted(_coords.items(), key=lambda x: -len(x[0])):
                    if city in location or location in city:
                        matched = coords
                        location_text = city
                        break
                if matched:
                    lon, lat = matched
                else:
                    return f"未找到「{location}」的坐标，国内城市请用标准名，国外请让 LLM 搜经纬度后直接输入数字", None

        zoom = p8 if p8 > 0 else _ZOOM_DEFAULT.get(mode, 1850)
        time = _parse_time(p9)
        paused = p10.strip().lower() == "animoff"

        url = _build_professional_url(
            mode=mode,
            animation=animation,
            projection=projection,
            lon=p6,
            lat=p7,
            zoom=zoom,
            time=time,
            height=height,
            overlay=overlay,
            annot=annot,
            paused=paused,
        )

        mode_name = _MODE_NAMES.get(p1, mode)
        time_text = _format_time_text(time)

        if paused:
            image_bytes = await screenshot(
                url=url,
                width=1920,
                height=1080,
                wait_until="networkidle",
                timeout=60000,
                wait_selector="canvas",
                wait_function=_NULLSCHOOL_LOADING_WAIT,
                post_wait_ms=5000,
                hard_wait=True,
                ready_timeout=30000,
            )
            return f"你要的{location_text}{time_text}的{mode_name}数据已返回", UniMessage.image(raw=image_bytes)
        else:
            video_bytes = await record_video(
                url=url,
                duration=10,
                width=1920,
                height=1080,
                wait_until="networkidle",
                timeout=60000,
                wait_selector="canvas",
                wait_function=_NULLSCHOOL_LOADING_WAIT,
                post_wait_ms=5000,
                hard_wait=True,
                ready_timeout=30000,
            )
            return f"你要的{location_text}{time_text}的{mode_name}数据已返回", UniMessage.video(raw=video_bytes)
    except Exception as e:
        logger.error(f"ens_professional 失败: {e}")
        return f"获取失败: {e}", None


@tool(response_format="content_and_artifact")
async def ens_professional(
    p1: int = 1,
    p2: int = 0,
    p3: int = 1,
    p4: int = 0,
    p5: int = 1,
    p6: str = "0",
    p7: str = "0",
    p8: int = 0,
    p9: str = "0",
    p10: str = "0",
    bio_annot: int = 0,
) -> tuple[str, UniMessage | None]:
    """Earth Nullschool 专业模式——数字参数方式查看地球可视化数据。

    触发关键词：vep、专业模式
    用户消息以 "vep" 开头时优先匹配本工具（如 "vep 1,0,1,0,1,116.4,39.9,1850"）。

    参数（按顺序，逗号/空格分隔均可）：
    p1 - 观察模式：1=大气 2=海洋 3=大气化学 4=颗粒物 5=空间天气 6=生物
    p2 - 高度：0=地表 1=10hPa 2=70hPa 3=250hPa 4=500hPa 5=700hPa 6=850hPa 7=1000hPa
    p3 - 动画：1=风 2=洋流 3=波浪
    p4 - 叠加层（按模式）：
         大气 0=默认 1=风 2=温度 3=相对湿度 4=露点 5=湿球温度 6=3HPA 7=CAPE
              8=水汽含量 9=云中总水量 10=MSLP 11=体感温度 12=UVI 13=WPD
         海洋 0=默认 1=洋流 2=波峰周期 3=浪高 4=海面温度 5=海温偏差值 6=珊瑚白化
         化学 1=COsc 2=CO2sc 3=SO2sm 4=NO2
         颗粒物 1=尘埃消光 2=PM1 3=PM2.5 4=PM10 5=OMaot 6=SO4ex
         空间 1=极光
         生物 0=默认 1=珊瑚白化
    p5 - 投影：1=正射 2=等距圆柱 3=等距圆锥 4=亚特兰蒂斯 5=帕特森 6=立体 7=蝴蝶 8=温克尔Ⅲ
    p6 - 经度或城市名（数字如 116.4，或城市名如"北京"、"广州"）
    p7 - 纬度（p6 为城市名时可填 0）
    p8 - 缩放（int，0=自动根据模式选默认值，越高越近）
    p9 - 时间：0=当前 或 YYYYMMDD.HHMM（如 20261001.1200）
    p10 - 暂停："animoff"=暂停，其他=播放
    bio_annot - 生物注释：仅生物模式时需要。0=无 1=活跃火点

    使用示例：vep 1,0,1,11,1,114.15,24.87,1850,20261001.1200,animoff

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 视频或截图)
    """
    async with tool_timer("ens_professional", {"p1": p1, "p4": p4, "p6": p6, "p7": p7}):
        return await run_ens_professional(
            p1=p1,
            p2=p2,
            p3=p3,
            p4=p4,
            p5=p5,
            p6=p6,
            p7=p7,
            p8=p8,
            p9=p9,
            p10=p10,
            bio_annot=bio_annot,
        )
