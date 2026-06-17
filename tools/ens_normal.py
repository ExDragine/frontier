"""Earth Nullschool 普通模式工具。

预设场景方案，LLM 匹配场景名 + 提取位置/时间 → 拼接 URL → 截图或录屏返回。
动画播放时返回 10 秒视频，动画暂停时（空间天气等）返回截图。

触发方式：消息以 "ve" 开头（如 "ve看看广州PM2.5"），LLM 自动路由到本工具。
国内城市走内置坐标字典，国外/特殊位置由 LLM 搜索经纬度后直接传入 lon/lat。
"""

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.browser_capture import record_video, screenshot
from utils.tool_helpers import tool_timer

# ── 场景映射表 ──
# key 为中文场景名，LLM 通过 docstring 中列出的清单做精确匹配。
# anim_state="off" 表示该场景动画默认暂停，应返回截图。

SCENARIO_MAP: dict[str, dict] = {
    # ── 大气模式 wind（地表 surface，10个）──
    "风速":         {"mode": "wind", "height": "surface", "overlay": None,                       "animation": "level", "projection": "orthographic", "zoom": 1850},
    "温度":         {"mode": "wind", "height": "surface", "overlay": "temp",                      "animation": "level", "projection": "orthographic", "zoom": 1850},
    "体感温度":     {"mode": "wind", "height": "surface", "overlay": "misery_index",              "animation": "level", "projection": "orthographic", "zoom": 1850},
    "相对湿度":     {"mode": "wind", "height": "surface", "overlay": "relative_humidity",         "animation": "level", "projection": "orthographic", "zoom": 1850},
    "3小时降水":    {"mode": "wind", "height": "surface", "overlay": "precip_3hr",                "animation": "level", "projection": "orthographic", "zoom": 1850},
    "平均海平面压力": {"mode": "wind", "height": "surface", "overlay": "mean_sea_level_pressure", "animation": "level", "projection": "orthographic", "zoom": 1850},
    "紫外线指数":   {"mode": "wind", "height": "surface", "overlay": "uv_index",                  "animation": "level", "projection": "orthographic", "zoom": 1850},
    "CAPE":         {"mode": "wind", "height": "surface", "overlay": "cape",                      "animation": "level", "projection": "orthographic", "zoom": 1850},
    "水汽含量":     {"mode": "wind", "height": "surface", "overlay": "total_precipitable_water",  "animation": "level", "projection": "orthographic", "zoom": 1850},
    "露点温度":     {"mode": "wind", "height": "surface", "overlay": "dew_point_temp",            "animation": "level", "projection": "orthographic", "zoom": 1850},

    # ── 海洋模式 ocean（5个）──
    "洋流":         {"mode": "ocean", "height": "surface", "overlay": None,                       "animation": "currents",      "projection": "equirectangular", "zoom": 80},
    "有效浪高":     {"mode": "ocean", "height": "surface", "overlay": "significant_wave_height",  "animation": "currents",      "projection": "equirectangular", "zoom": 80},
    "波峰周期":     {"mode": "ocean", "height": "surface", "overlay": "primary_waves",            "animation": "primary/waves", "projection": "equirectangular", "zoom": 80},
    "海面温度":     {"mode": "ocean", "height": "surface", "overlay": "sea_surface_temp",         "animation": "currents",      "projection": "equirectangular", "zoom": 80},
    "海面温度异常": {"mode": "ocean", "height": "surface", "overlay": "sea_surface_temp_anomaly", "animation": "currents",      "projection": "equirectangular", "zoom": 80},

    # ── 化学污染物模式 chem（4个）──
    "一氧化碳浓度": {"mode": "chem", "height": "surface", "overlay": "cosc",    "animation": "level", "projection": "orthographic", "zoom": 1850},
    "二氧化碳浓度": {"mode": "chem", "height": "surface", "overlay": "co2sc",   "animation": "level", "projection": "orthographic", "zoom": 1850},
    "二氧化硫质量": {"mode": "chem", "height": "surface", "overlay": "so2smass", "animation": "level", "projection": "orthographic", "zoom": 1850},
    "二氧化氮浓度": {"mode": "chem", "height": "surface", "overlay": "no2",     "animation": "level", "projection": "orthographic", "zoom": 1850},

    # ── 颗粒物模式 particulates（6个）──
    "PM2.5":        {"mode": "particulates", "height": "surface", "overlay": "pm2.5",              "animation": "level", "projection": "orthographic", "zoom": 1850},
    "PM10":         {"mode": "particulates", "height": "surface", "overlay": "pm10",               "animation": "level", "projection": "orthographic", "zoom": 1850},
    "PM1":          {"mode": "particulates", "height": "surface", "overlay": "pm1",                "animation": "level", "projection": "orthographic", "zoom": 1850},
    "尘埃消光":     {"mode": "particulates", "height": "surface", "overlay": "duexttau",          "animation": "level", "projection": "orthographic", "zoom": 1850},
    "有机物气溶胶": {"mode": "particulates", "height": "surface", "overlay": "organic_matter_aot", "animation": "level", "projection": "orthographic", "zoom": 1850},
    "硫酸盐消光":   {"mode": "particulates", "height": "surface", "overlay": "suexttau",          "animation": "level", "projection": "orthographic", "zoom": 1850},

    # ── 空间天气模式 space（1个，默认暂停 → 截图）──
    "极光": {"mode": "space", "height": "surface", "overlay": "aurora", "animation": "level", "projection": "orthographic", "zoom": 300},

    # ── 生物模式 bio（2个）──
    "珊瑚白化": {"mode": "bio", "height": "surface", "overlay": "bleaching_alert_area", "animation": "level", "projection": "orthographic", "zoom": 300},
    "活跃火点": {"mode": "bio", "height": "surface", "overlay": None,                    "animation": "level", "projection": "orthographic", "zoom": 300, "annotation": "fires"},
}

# ── 国内城市坐标字典（lon, lat）──
# 参考雷达图 tool 的硬编码映射模式，无需外部 API。

_CITY_COORDS: dict[str, tuple[float, float]] = {
    # 直辖市
    "北京": (116.40, 39.90), "北京市": (116.40, 39.90),
    "上海": (121.47, 31.23), "上海市": (121.47, 31.23),
    "天津": (117.20, 39.13), "天津市": (117.20, 39.13),
    "重庆": (106.55, 29.57), "重庆市": (106.55, 29.57),
    # 省会
    "广州": (113.26, 23.13), "广州市": (113.26, 23.13),
    "深圳": (114.07, 22.62), "深圳市": (114.07, 22.62),
    "成都": (104.07, 30.67), "成都市": (104.07, 30.67),
    "杭州": (120.15, 30.28), "杭州市": (120.15, 30.28),
    "武汉": (114.30, 30.60), "武汉市": (114.30, 30.60),
    "西安": (108.94, 34.26), "西安市": (108.94, 34.26),
    "南京": (118.79, 32.06), "南京市": (118.79, 32.06),
    "长沙": (112.94, 28.23), "长沙市": (112.94, 28.23),
    "郑州": (113.65, 34.76), "郑州市": (113.65, 34.76),
    "济南": (117.00, 36.67), "济南市": (117.00, 36.67),
    "沈阳": (123.43, 41.80), "沈阳市": (123.43, 41.80),
    "哈尔滨": (126.53, 45.80), "哈尔滨市": (126.53, 45.80),
    "长春": (125.32, 43.90), "长春市": (125.32, 43.90),
    "昆明": (102.83, 24.88), "昆明市": (102.83, 24.88),
    "贵阳": (106.71, 26.57), "贵阳市": (106.71, 26.57),
    "南宁": (108.37, 22.82), "南宁市": (108.37, 22.82),
    "海口": (110.20, 20.04), "海口市": (110.20, 20.04),
    "石家庄": (114.51, 38.04), "石家庄市": (114.51, 38.04),
    "太原": (112.55, 37.87), "太原市": (112.55, 37.87),
    "呼和浩特": (111.75, 40.84), "呼和浩特市": (111.75, 40.84),
    "合肥": (117.23, 31.82), "合肥市": (117.23, 31.82),
    "南昌": (115.86, 28.68), "南昌市": (115.86, 28.68),
    "福州": (119.30, 26.07), "福州市": (119.30, 26.07),
    "兰州": (103.83, 36.06), "兰州市": (103.83, 36.06),
    "西宁": (101.78, 36.62), "西宁市": (101.78, 36.62),
    "银川": (106.23, 38.49), "银川市": (106.23, 38.49),
    "拉萨": (91.17, 29.65), "拉萨市": (91.17, 29.65),
    "乌鲁木齐": (87.62, 43.82), "乌鲁木齐市": (87.62, 43.82),
    # 副省级 / 计划单列市
    "大连": (121.61, 38.91), "青岛": (120.38, 36.07),
    "宁波": (121.54, 29.87), "厦门": (118.09, 24.48),
    # 长三角 / 珠三角
    "苏州": (120.59, 31.30), "无锡": (120.31, 31.49),
    "东莞": (113.75, 23.05), "佛山": (113.12, 23.02),
    "珠海": (113.58, 22.27), "惠州": (114.42, 23.11),
    "温州": (120.70, 28.00), "绍兴": (120.58, 30.03),
    "常州": (119.97, 31.81), "南通": (120.89, 32.00),
    # 其他常用城市
    "三亚": (109.51, 18.25), "桂林": (110.29, 25.27),
    "大理": (100.23, 25.61), "丽江": (100.23, 26.86),
    "烟台": (121.45, 37.46), "威海": (122.12, 37.51),
    "徐州": (117.18, 34.27), "洛阳": (112.45, 34.62),
    "汕头": (116.68, 23.35), "湛江": (110.36, 21.27),
    "北海": (109.12, 21.48), "秦皇岛": (119.60, 39.93),
    "延吉": (129.51, 42.91), "漠河": (122.54, 53.48),
    "喀什": (75.99, 39.47), "伊犁": (81.32, 43.92),
    "台北": (121.53, 25.05), "香港": (114.17, 22.30),
    "澳门": (113.55, 22.20),
    # 省级行政区（用于模糊放大范围）
    "广东": (113.26, 23.13), "广西": (108.37, 22.82),
    "海南": (110.20, 20.04), "福建": (119.30, 26.07),
    "浙江": (120.15, 30.28), "江苏": (118.79, 32.06),
    "山东": (117.00, 36.67), "河北": (114.51, 38.04),
    "河南": (113.65, 34.76), "湖北": (114.30, 30.60),
    "湖南": (112.94, 28.23), "江西": (115.86, 28.68),
    "四川": (104.07, 30.67), "贵州": (106.71, 26.57),
    "云南": (102.83, 24.88), "陕西": (108.94, 34.26),
    "甘肃": (103.83, 36.06), "青海": (101.78, 36.62),
    "宁夏": (106.23, 38.49), "新疆": (87.62, 43.82),
    "西藏": (91.17, 29.65), "内蒙古": (111.75, 40.84),
    "山西": (112.55, 37.87), "辽宁": (123.43, 41.80),
    "吉林": (125.32, 43.90), "黑龙江": (126.53, 45.80),
    "安徽": (117.23, 31.82), "台湾": (121.53, 25.05),
}


def _resolve_coords(location: str) -> tuple[float, float]:
    """根据位置文本解析经纬度（纯字典查找，不需要外部 API）。"""
    if not location or not location.strip():
        raise ValueError("位置不能为空")

    location = location.strip()

    # 1) 精确匹配
    if location in _CITY_COORDS:
        return _CITY_COORDS[location]

    # 2) 模糊匹配（最长优先）
    for city, coords in sorted(_CITY_COORDS.items(), key=lambda x: -len(x[0])):
        if city in location or location in city:
            return coords

    raise ValueError(
        f"未找到「{location}」的坐标。"
        f"国内城市请使用标准名称（如：北京、广州）。"
        f"国外地点请让 LLM 搜索经纬度后直接传入 lon/lat 参数。"
    )


def _build_earth_url(params: dict, lon: float, lat: float, time: str) -> str:
    """拼接 earth.nullschool.net 的 hash-fragment URL。

    格式: time/mode/height/animation/[annot][anim=off][grid][overlay=xxx]/projection=lon,lat,zoom/loc=lon,lat
    """
    segments = [time, params["mode"], params["height"], params["animation"]]

    annotation = params.get("annotation")
    if annotation:
        segments.append(f"annot={annotation}")

    anim_state = params.get("anim_state")
    if anim_state:
        segments.append(f"anim={anim_state}")

    grid = params.get("grid")
    if grid:
        segments.append(f"grid={grid}")

    overlay = params.get("overlay")
    if overlay is not None:
        segments.append(f"overlay={overlay}")

    path = "/".join(segments)
    projection = params["projection"]
    zoom = params["zoom"]
    view = f"{projection}={lon},{lat},{zoom}"
    loc = f"loc={lon},{lat}"

    return f"https://earth.nullschool.net/zh-cn/{path}/{view}/{loc}"


async def run_ens_normal(
    scenario: str,
    location: str,
    time: str = "#current",
    lon: float | None = None,
    lat: float | None = None,
    zoom: int | None = None,
) -> tuple[str, UniMessage | None]:
    """普通模式核心逻辑。"""
    params = SCENARIO_MAP.get(scenario)
    if params is None:
        valid = "、".join(SCENARIO_MAP.keys())
        return f"未知场景「{scenario}」。可用场景: {valid}", None

    try:
        if lon is not None and lat is not None:
            resolved_lon, resolved_lat = lon, lat
        else:
            resolved_lon, resolved_lat = _resolve_coords(location)

        if zoom is not None:
            params = {**params, "zoom": zoom}

        url = _build_earth_url(params, resolved_lon, resolved_lat, time)

        if params.get("anim_state") == "off":
            image_bytes = await screenshot(
                url=url, width=1920, height=1080,
                wait_until="domcontentloaded", timeout=60000,
            )
            return f"{scenario} - {location}（静态截图）\n💡 vep 专业模式自定义参数 | /vehelp 查看参数菜单", UniMessage.image(raw=image_bytes)
        else:
            video_bytes = await record_video(
                url=url, duration=10, width=1920, height=1080,
                wait_until="domcontentloaded", timeout=60000,
            )
            return f"{scenario} - {location}（10秒视频）\n💡 vep 专业模式自定义参数 | /vehelp 查看参数菜单", UniMessage.video(raw=video_bytes)
    except Exception as e:
        logger.error(f"ens_normal 失败 [{scenario}/{location}]: {e}")
        return f"获取失败: {e}", None


@tool(response_format="content_and_artifact")
async def ens_normal(
    scenario: str,
    location: str,
    time: str = "#current",
    lon: float | None = None,
    lat: float | None = None,
    zoom: int | None = None,
) -> tuple[str, UniMessage | None]:
    """Earth Nullschool 普通模式——通过预设场景快速查看地球可视化数据。

    触发关键词：ve、地球可视化、earth nullschool
    用户消息以 "ve" 开头时优先匹配本工具（如 "ve看看广州PM2.5"）。

    适用场景：用户用自然语言描述想看的内容，本工具自动匹配预设场景并返回截图或 10 秒录屏。

    可用场景清单（scenario 参数必须精确匹配下列名称之一）：
    风速、温度、体感温度、相对湿度、3小时降水、平均海平面压力、
    紫外线指数、CAPE、水汽含量、露点温度、
    洋流、有效浪高、波峰周期、海面温度、海面温度异常、
    一氧化碳浓度、二氧化碳浓度、二氧化硫质量、二氧化氮浓度、
    PM2.5、PM10、PM1、尘埃消光、有机物气溶胶、硫酸盐消光、
    极光、珊瑚白化、活跃火点

    Args:
        scenario: 场景中文名，必须从上方的可用场景清单中精确选取
        location: 位置描述。国内城市（如"北京"、"广州"）走内置坐标字典；
                  国外/特殊位置由 LLM 搜索经纬度后通过 lon/lat 参数传入
        time: 时间，格式 "#current"（当前）或 "#YYYY/MM/DD/HHMMZ"，默认当前
        lon: 经度，传入后跳过内置坐标查询
        lat: 纬度，传入后跳过内置坐标查询
        zoom: 缩放等级，传入后覆盖场景默认值（局部默认 1850，宏观 80~300）

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 视频或截图)
    """
    async with tool_timer("ens_normal", {"scenario": scenario, "location": location, "time": time}):
        return await run_ens_normal(
            scenario=scenario, location=location, time=time,
            lon=lon, lat=lat, zoom=zoom,
        )
