"""地球可视化数据 普通模式工具。

预设场景方案，LLM 匹配场景名 + 提取位置/时间 → 拼接 URL → 截图或录屏返回。
动画播放时返回视频，动画暂停时（空间天气等）返回截图。

触发方式：消息以 "ve" 开头（如 "ve看看广州PM2.5"），LLM 自动路由到本工具。
国内城市走内置坐标字典，国外/特殊位置由 LLM 搜索经纬度后直接传入 lon/lat。
"""

import asyncio
import math
import re
import time as _time

from langchain_core.tools import tool
from nonebot import logger

from utils.ens_gate import _ens_prefix
from utils.alconna import UniMessage
from utils.browser_capture import record_video, screenshot
from utils.tool_helpers import tool_timer

# BAA 等级含义（用于 tool 返回时附带说明，Agent 可据此解读）
_BAA_LEVEL_MEANING: dict[str, str] = {
    "无压力": "海温正常，未超过珊瑚耐热阈值，珊瑚健康无白化风险",
    "珊瑚白化监测": "海温开始偏高，预计未来几周内可能达到白化阈值，需密切关注",
    "珊瑚白化警报": "海温已接近或略微超过白化阈值，白化即将或刚开始发生",
    "警报等级 1": "海温显著超标，白化正在发生但珊瑚尚可存活（DHW≥4）",
    "警报等级 2": "更严重热应力，广泛白化且部分珊瑚开始死亡（DHW≥8）",
    "警报等级 3": "严重白化，大量珊瑚死亡（DHW≥12）",
    "警报等级 4": "极严重白化，多数珊瑚死亡（DHW≥16）",
    "警报等级 5": "灾难级白化，近乎全部珊瑚死亡（DHW≥20）",
}

# 已移除的场景及说明（用于明确拒绝，防止 Agent 回退到其他工具）
# 内存缓存：同一 URL 在 TTL 内直接返回，避免重复生成视频/截图。
# key=url, value=(text, artifact, timestamp)
_ens_cache: dict = {}
_ENS_CACHE_TTL = 60  # 秒


def clear_ens_cache():
    """清理 ENS 工具内存缓存，由 shutdown hook 调用。"""
    _ens_cache.clear()
    logger.info("ENS 缓存已清理")

# ── 场景映射表 ──
# key 为中文场景名，LLM 通过 docstring 中列出的清单做精确匹配。
# anim_state="off" 表示该场景动画默认暂停，应返回截图。

SCENARIO_MAP: dict[str, dict] = {
    # ── 大气模式 wind 区域版（14个）──
    "风速": {
        "mode": "wind",
        "height": "surface",
        "overlay": None,
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "温度": {
        "mode": "wind",
        "height": "surface",
        "overlay": "temp",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "体感温度": {
        "mode": "wind",
        "height": "surface",
        "overlay": "misery_index",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "相对湿度": {
        "mode": "wind",
        "height": "surface",
        "overlay": "relative_humidity",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "3小时降水": {
        "mode": "wind",
        "height": "surface",
        "overlay": "precip_3hr",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "平均海平面压力": {
        "mode": "wind",
        "height": "surface",
        "overlay": "mean_sea_level_pressure",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "紫外线指数": {
        "mode": "wind",
        "height": "surface",
        "overlay": "uv_index",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "CAPE": {
        "mode": "wind",
        "height": "surface",
        "overlay": "cape",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "水汽含量": {
        "mode": "wind",
        "height": "surface",
        "overlay": "total_precipitable_water",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "露点温度": {
        "mode": "wind",
        "height": "surface",
        "overlay": "dew_point_temp",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "湿球温度": {
        "mode": "wind",
        "height": "surface",
        "overlay": "wet_bulb_temp",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "总云水量": {
        "mode": "wind",
        "height": "surface",
        "overlay": "total_cloud_water",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "风功率密度": {
        "mode": "wind",
        "height": "surface",
        "overlay": "wind_power_density",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "大气无叠加": {
        "mode": "wind",
        "height": "surface",
        "overlay": "none",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    # ── 海洋模式 ocean 区域版（14个）──
    "洋流": {
        "mode": "ocean",
        "height": "surface",
        "overlay": None,
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "有效浪高": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "significant_wave_height",
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波峰周期": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "primary_waves",
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "海面温度": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "sea_surface_temp",
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "海面温度异常": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "sea_surface_temp_anomaly",
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "洋流波峰周期": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "primary_waves",
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "洋流珊瑚白化": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "bleaching_alert_area",
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "洋流无叠加": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "none",
        "animation": "currents",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波浪": {
        "mode": "ocean",
        "height": "surface",
        "overlay": None,
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波浪有效浪高": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "significant_wave_height",
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波浪海面温度": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "sea_surface_temp",
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波浪海面温度异常": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "sea_surface_temp_anomaly",
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波浪珊瑚白化": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "bleaching_alert_area",
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "波浪无叠加": {
        "mode": "ocean",
        "height": "surface",
        "overlay": "none",
        "animation": "primary/waves",
        "projection": "orthographic",
        "zoom": 4000,
    },
    # ── 化学污染物模式 chem（4个）──
    "一氧化碳浓度": {
        "mode": "chem",
        "height": "surface",
        "overlay": "cosc",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "二氧化碳浓度": {
        "mode": "chem",
        "height": "surface",
        "overlay": "co2sc",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "二氧化硫质量": {
        "mode": "chem",
        "height": "surface",
        "overlay": "so2smass",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "二氧化氮浓度": {
        "mode": "chem",
        "height": "surface",
        "overlay": "no2",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    # ── 颗粒物模式 particulates（6个）──
    "PM2.5": {
        "mode": "particulates",
        "height": "surface",
        "overlay": "pm2.5",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "PM10": {
        "mode": "particulates",
        "height": "surface",
        "overlay": "pm10",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "PM1": {
        "mode": "particulates",
        "height": "surface",
        "overlay": "pm1",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "尘埃消光": {
        "mode": "particulates",
        "height": "surface",
        "overlay": "duexttau",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "有机物气溶胶": {
        "mode": "particulates",
        "height": "surface",
        "overlay": "organic_matter_aot",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "硫酸盐消光": {
        "mode": "particulates",
        "height": "surface",
        "overlay": "suexttau",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    # ── 空间天气模式 space（1个，默认暂停 → 截图）──
    "极光": {
        "mode": "space",
        "height": "surface",
        "overlay": "aurora",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 1000,
    },
    # ── 生物模式 bio（2个）──
    "珊瑚白化": {
        "mode": "bio",
        "height": "surface",
        "overlay": "bleaching_alert_area",
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
    },
    "活跃火点": {
        "mode": "bio",
        "height": "surface",
        "overlay": None,
        "animation": "level",
        "projection": "orthographic",
        "zoom": 4000,
        "annotation": "fires",
    },
}

# ── 国内城市坐标字典（lon, lat）──
# 参考雷达图 tool 的硬编码映射模式，无需外部 API。

_CITY_COORDS: dict[str, tuple[float, float]] = {
    # 直辖市
    "北京": (116.40, 39.90),
    "北京市": (116.40, 39.90),
    "上海": (121.47, 31.23),
    "上海市": (121.47, 31.23),
    "天津": (117.20, 39.13),
    "天津市": (117.20, 39.13),
    "重庆": (106.55, 29.57),
    "重庆市": (106.55, 29.57),
    # 省会
    "广州": (113.26, 23.13),
    "广州市": (113.26, 23.13),
    "深圳": (114.07, 22.62),
    "深圳市": (114.07, 22.62),
    "成都": (104.07, 30.67),
    "成都市": (104.07, 30.67),
    "杭州": (120.15, 30.28),
    "杭州市": (120.15, 30.28),
    "武汉": (114.30, 30.60),
    "武汉市": (114.30, 30.60),
    "西安": (108.94, 34.26),
    "西安市": (108.94, 34.26),
    "南京": (118.79, 32.06),
    "南京市": (118.79, 32.06),
    "长沙": (112.94, 28.23),
    "长沙市": (112.94, 28.23),
    "郑州": (113.65, 34.76),
    "郑州市": (113.65, 34.76),
    "济南": (117.00, 36.67),
    "济南市": (117.00, 36.67),
    "沈阳": (123.43, 41.80),
    "沈阳市": (123.43, 41.80),
    "哈尔滨": (126.53, 45.80),
    "哈尔滨市": (126.53, 45.80),
    "长春": (125.32, 43.90),
    "长春市": (125.32, 43.90),
    "昆明": (102.83, 24.88),
    "昆明市": (102.83, 24.88),
    "贵阳": (106.71, 26.57),
    "贵阳市": (106.71, 26.57),
    "南宁": (108.37, 22.82),
    "南宁市": (108.37, 22.82),
    "海口": (110.20, 20.04),
    "海口市": (110.20, 20.04),
    "石家庄": (114.51, 38.04),
    "石家庄市": (114.51, 38.04),
    "太原": (112.55, 37.87),
    "太原市": (112.55, 37.87),
    "呼和浩特": (111.75, 40.84),
    "呼和浩特市": (111.75, 40.84),
    "合肥": (117.23, 31.82),
    "合肥市": (117.23, 31.82),
    "南昌": (115.86, 28.68),
    "南昌市": (115.86, 28.68),
    "福州": (119.30, 26.07),
    "福州市": (119.30, 26.07),
    "兰州": (103.83, 36.06),
    "兰州市": (103.83, 36.06),
    "西宁": (101.78, 36.62),
    "西宁市": (101.78, 36.62),
    "银川": (106.23, 38.49),
    "银川市": (106.23, 38.49),
    "拉萨": (91.17, 29.65),
    "拉萨市": (91.17, 29.65),
    "乌鲁木齐": (87.62, 43.82),
    "乌鲁木齐市": (87.62, 43.82),
    # 副省级 / 计划单列市
    "大连": (121.61, 38.91),
    "青岛": (120.38, 36.07),
    "宁波": (121.54, 29.87),
    "厦门": (118.09, 24.48),
    # 长三角 / 珠三角
    "苏州": (120.59, 31.30),
    "无锡": (120.31, 31.49),
    "东莞": (113.75, 23.05),
    "佛山": (113.12, 23.02),
    "珠海": (113.58, 22.27),
    "惠州": (114.42, 23.11),
    "温州": (120.70, 28.00),
    "绍兴": (120.58, 30.03),
    "常州": (119.97, 31.81),
    "南通": (120.89, 32.00),
    # 其他常用城市
    "三亚": (109.51, 18.25),
    "桂林": (110.29, 25.27),
    "大理": (100.23, 25.61),
    "丽江": (100.23, 26.86),
    "烟台": (121.45, 37.46),
    "威海": (122.12, 37.51),
    "徐州": (117.18, 34.27),
    "洛阳": (112.45, 34.62),
    "汕头": (116.68, 23.35),
    "湛江": (110.36, 21.27),
    "北海": (109.12, 21.48),
    "秦皇岛": (119.60, 39.93),
    "延吉": (129.51, 42.91),
    "漠河": (122.54, 53.48),
    "喀什": (75.99, 39.47),
    "伊犁": (81.32, 43.92),
    "台北": (121.53, 25.05),
    "香港": (114.17, 22.30),
    "澳门": (113.55, 22.20),
    # 省级行政区（用于模糊放大范围）
    "广东": (113.26, 23.13),
    "广西": (108.37, 22.82),
    "海南": (110.20, 20.04),
    "福建": (119.30, 26.07),
    "浙江": (120.15, 30.28),
    "江苏": (118.79, 32.06),
    "山东": (117.00, 36.67),
    "河北": (114.51, 38.04),
    "河南": (113.65, 34.76),
    "湖北": (114.30, 30.60),
    "湖南": (112.94, 28.23),
    "江西": (115.86, 28.68),
    "四川": (104.07, 30.67),
    "贵州": (106.71, 26.57),
    "云南": (102.83, 24.88),
    "陕西": (108.94, 34.26),
    "甘肃": (103.83, 36.06),
    "青海": (101.78, 36.62),
    "宁夏": (106.23, 38.49),
    "新疆": (87.62, 43.82),
    "西藏": (91.17, 29.65),
    "内蒙古": (111.75, 40.84),
    "山西": (112.55, 37.87),
    "辽宁": (123.43, 41.80),
    "吉林": (125.32, 43.90),
    "黑龙江": (126.53, 45.80),
    "安徽": (117.23, 31.82),
    "台湾": (121.53, 25.05),
}


# ── 国内近海坐标（已校准）──
# key 为城市/省份名，value 为近海点坐标 (lon, lat)
_COASTAL_SEA_COORDS: dict[str, tuple[float, float]] = {
    "丹东": (124.001, 39.408),
    "大连": (121.7, 38.65),
    "营口": (121.687, 40.350),
    "盘锦": (121.861, 40.499),
    "锦州": (121.184, 40.494),
    "葫芦岛": (121.0, 40.4),
    "秦皇岛": (119.8, 39.7),
    "唐山": (118.658, 38.974),
    "沧州": (118.100, 38.546),
    "天津": (118.105, 38.8),
    "滨州": (118.702, 38.429),
    "东营": (119.222, 37.843),
    "潍坊": (119.5, 37.604),
    "烟台": (121.6, 37.6),
    "威海": (122.2, 37.5),
    "青岛": (120.6, 35.9),
    "日照": (119.875, 35.276),
    "连云港": (119.883, 34.8),
    "盐城": (121.041, 33.6),
    "南通": (122.087, 31.9),
    "苏州": (122.125, 31.3),
    "上海": (122.1, 31.0),
    "嘉兴": (121.707, 30.5),
    "杭州": (121.889, 30.2),
    "绍兴": (121.899, 30.2),
    "宁波": (122.000, 29.731),
    "舟山": (122.633, 30.0),
    "台州": (122.126, 28.6),
    "温州": (121.1, 27.7),
    "宁德": (120.3, 26.7),
    "福州": (120.114, 26.0),
    "莆田": (119.471, 25.122),
    "泉州": (118.9, 24.6),
    "厦门": (118.369, 24.3),
    "漳州": (118.2, 24.1),
    "汕头": (117.155, 23.2),
    "汕尾": (115.7, 22.468),
    "惠州": (114.9, 22.486),
    "深圳": (114.4, 22.3),
    "东莞": (113.862, 21.985),
    "广州": (113.812, 21.966),
    "佛山": (113.596, 21.991),
    "中山": (113.725, 21.959),
    "珠海": (113.7, 22.0),
    "江门": (113.1, 21.8),
    "阳江": (112.1, 21.4),
    "茂名": (111.163, 20.948),
    "湛江": (110.691, 20.806),
    "北海": (109.3, 21.2),
    "钦州": (108.8, 21.443),
    "防城港": (108.5, 21.4),
    "海口": (109.937, 20.056),
    "三亚": (109.6, 17.957),
    "三沙": (112.3, 16.8),
    "台北": (121.899, 25.264),
    "基隆": (121.852, 25.236),
    "高雄": (120.135, 22.353),
    "花莲": (122.085, 24.1),
    "香港": (114.323, 22.223),
    "澳门": (113.7, 22.0),
    "辽宁": (121.7, 38.7),
    "河北": (119.8, 39.5),
    "山东": (120.8, 36.2),
    "江苏": (122.080, 31.9),
    "浙江": (122.505, 29.9),
    "福建": (118.673, 24.557),
    "广东": (113.8, 21.5),
    "广西": (109.3, 21.2),
    "海南": (109.6, 18.0),
    "台湾": (122.052, 23.936),
}


# ── 全球海域坐标（已校准，157 个水体）──
# key 为海域名，value 为水域中心点坐标 (lon, lat)
_GLOBAL_SEA_COORDS: dict[str, tuple[float, float]] = {
    "太平洋": (-151.3, -0.9),
    "大西洋": (-31.5, 4.3),
    "印度洋": (83.4, -24.8),
    "北冰洋": (0.0, 85.0),
    "南大洋": (-40.392, -73.029),
    "加勒比海": (-74.1, 15.3),
    "南海": (112.2, 11.2),
    "阿拉伯海": (62.6, 12.4),
    "白令海": (166.506, 51.340),
    "日本海": (137.466, 39.133),
    "黄海": (123.800, 36.691),
    "东海": (125.1, 28.9),
    "菲律宾海": (133.3, 18.9),
    "珊瑚海": (155.6, -18.7),
    "塔斯曼海": (161.0, -40.5),
    "挪威海": (3.8, 68.8),
    "巴伦支海": (42.5, 74.3),
    "喀拉海": (79.9, 73.8),
    "拉普捷夫海": (118.4, 76.0),
    "东西伯利亚海": (150.816, 73.563),
    "楚科奇海": (-168.600, 73.552),
    "波弗特海": (139.5, 72.4),
    "拉布拉多海": (-57.630, 61.552),
    "格陵兰海": (-9.2, 74.2),
    "安达曼海": (95.6, 11.5),
    "爪哇海": (112.0, -4.7),
    "苏拉威西海": (121.2, 4.3),
    "班达海": (126.8, -4.9),
    "帝汶海": (127.9, -12.0),
    "阿拉弗拉海": (136.5, -10.5),
    "所罗门海": (154.6, -8.3),
    "俾斯麦海": (147.5, -3.4),
    "弗洛勒斯海": (120.0, -7.1),
    "马鲁古海": (125.9, 1.3),
    "哈尔马赫拉海": (129.2, 0.4),
    "萨武海": (121.1, -9.6),
    "塞兰海": (128.984, -2.366),
    "地中海": (18.334, 36.030),
    "红海": (38.6, 20.3),
    "黑海": (34.6, 44.1),
    "波罗的海": (20.0, 59.8),
    "墨西哥湾": (-89.1, 24.4),
    "阿拉斯加湾": (-150.0, 57.9),
    "孟加拉湾": (87.1, 14.6),
    "波斯湾": (52.5, 27.2),
    "亚丁湾": (46.9, 12.8),
    "泰国湾": (102.1, 9.9),
    "几内亚湾": (1.2, 2.9),
    "加利福尼亚湾": (-110.9, 27.4),
    "比斯开湾": (-4.2, 45.6),
    "哈德逊湾": (-85.7, 58.7),
    "圣劳伦斯湾": (-63.1, 48.7),
    "波的尼亚湾": (20.511, 62.849),
    "芬兰湾": (26.6, 60.0),
    "里加湾": (23.1, 58.1),
    "阿曼湾": (59.0, 24.4),
    "大澳大利亚湾": (131.9, -37.5),
    "巴芬湾": (-66.2, 75.9),
    "苏伊士湾": (33.448, 28.150),
    "亚喀巴湾": (34.532, 28.134),
    "芬迪湾": (-65.451, 45.110),
    "托米尼湾": (121.581, -0.373),
    "波尼湾": (121.0, -4.1),
    "北部湾": (107.8, 19.7),
    "卡奔塔利亚湾": (139.5, -14.0),
    "圣乔治湾": (12.323, 54.572),
    "科威特湾": (48.232, 29.405),
    "坎贝湾": (72.4, 21.2),
    "库奇湾": (69.5, 22.7),
    "马纳尔湾": (78.8, 8.5),
    "巴克湾": (80.008, 10.302),
    "阿纳德尔湾": (-179.744, 63.789),
    "舍列霍夫湾": (157.0, 59.0),
    "太梅尔湾": (84.355, 76.105),
    "鄂毕湾": (73.568, 72.514),
    "叶尼塞湾": (80.392, 72.381),
    "哈坦加湾": (107.626, 73.377),
    "直布罗陀海峡": (-5.816, 35.977),
    "马六甲海峡": (99.5, 4.3),
    "新加坡海峡": (104.350, 1.286),
    "望加锡海峡": (118.4, -2.1),
    "莫桑比克海峡": (40.9, -18.7),
    "戴维斯海峡": (-57.0, 64.9),
    "哈德逊海峡": (-70.979, 61.606),
    "英吉利海峡": (-2.0, 49.8),
    "斯卡格拉克海峡": (9.4, 58.5),
    "卡特加特海峡": (11.2, 56.3),
    "丹麦海峡": (-28.0, 67.0),
    "德雷克海峡": (-65.0, -58.5),
    "巴斯海峡": (146.0, -39.5),
    "库克海峡": (174.470, -40.955),
    "对马海峡": (129.617, 34.163),
    "津轻海峡": (140.701, 41.529),
    "宗谷海峡": (142.1, 45.7),
    "鞑靼海峡": (141.5, 50.0),
    "霍尔木兹海峡": (56.3, 26.5),
    "曼德海峡": (43.139, 12.955),
    "达达尼尔海峡": (27.345, 40.539),
    "博斯普鲁斯海峡": (28.980, 40.970),
    "龙目海峡": (115.8, -8.6),
    "巽他海峡": (105.685, -6.054),
    "佛罗里达海峡": (-80.5, 24.0),
    "尤卡坦海峡": (-86.0, 21.5),
    "向风海峡": (-74.5, 19.5),
    "莫纳海峡": (-67.9, 18.3),
    "巴厘海峡": (114.559, -7.965),
    "巴布亚湾海峡": (144.0, -9.0),
    "托雷斯海峡": (142.2, -10.1),
    "亚得里亚海": (16.1, 42.7),
    "爱琴海": (25.4, 38.1),
    "爱奥尼亚海": (19.2, 38.5),
    "第勒尼安海": (12.4, 40.9),
    "阿尔沃兰海": (-3.3, 36.0),
    "利古里亚海": (8.7, 43.7),
    "巴利阿里海": (2.0, 40.3),
    "伊比利亚海": (2.0, 40.3),
    "凯尔特海": (-7.8, 49.4),
    "爱尔兰海": (-4.6, 53.5),
    "马尔马拉海": (28.1, 40.6),
    "白海": (38.082, 65.989),
    "亚速海": (36.5, 46.2),
    "鄂霍次克海": (150.4, 53.0),
    "拉克代夫海": (76.3, 7.0),
    "罗斯海": (-159.388, -76.647),
    "威德尔海": (-40.0, -73.0),
    "阿蒙森海": (-115.0, -72.0),
    "别林斯高晋海": (-80.0, -70.0),
    "斯科舍海": (-40.0, -57.0),
    "苏禄海": (120.0, 8.5),
    "西里伯斯海": (122.6, 3.8),
    "萨马海": (125.803, 11.541),
    "米沙鄢海": (123.815, 11.612),
    "锡布延海": (122.8, 12.3),
    "保和海": (124.502, 9.486),
    "卡莫特斯海": (124.279, 10.5),
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


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两个经纬度点之间的球面距离（公里）。"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# 海域坐标全集缓存（用于最近邻搜索）
_SEA_COORDS_ALL: list[tuple[str, float, float]] | None = None


def _get_sea_coords_all() -> list[tuple[str, float, float]]:
    """返回合并后的全部海域坐标 [(name, lon, lat), ...]，惰性初始化。"""
    global _SEA_COORDS_ALL
    if _SEA_COORDS_ALL is None:
        items: list[tuple[str, float, float]] = []
        for name, (lon, lat) in _COASTAL_SEA_COORDS.items():
            items.append((name, lon, lat))
        for name, (lon, lat) in _GLOBAL_SEA_COORDS.items():
            items.append((name, lon, lat))
        _SEA_COORDS_ALL = items
    return _SEA_COORDS_ALL


def _resolve_sea_coords(location: str) -> tuple[float, float]:
    """解析海域坐标。

    1. 精确匹配 _COASTAL_SEA_COORDS
    2. 精确匹配 _GLOBAL_SEA_COORDS
    3. 模糊匹配（最长优先）_COASTAL_SEA_COORDS
    4. 模糊匹配（最长优先）_GLOBAL_SEA_COORDS
    5. Haversine 最近邻
    """
    if not location or not location.strip():
        raise ValueError("位置不能为空")
    location = location.strip()

    # 1) 精确匹配近海
    if location in _COASTAL_SEA_COORDS:
        return _COASTAL_SEA_COORDS[location]
    # 2) 精确匹配全球海域
    if location in _GLOBAL_SEA_COORDS:
        return _GLOBAL_SEA_COORDS[location]

    # 3) 模糊匹配近海（最长优先）
    for city, coords in sorted(_COASTAL_SEA_COORDS.items(), key=lambda x: -len(x[0])):
        if city in location or location in city:
            return coords
    # 4) 模糊匹配全球海域（最长优先）
    for sea, coords in sorted(_GLOBAL_SEA_COORDS.items(), key=lambda x: -len(x[0])):
        if sea in location or location in sea:
            return coords

    # 5) 兜底：城市坐标 → 最近海域
    city = _CITY_COORDS.get(location)
    if city is None:
        for k, v in sorted(_CITY_COORDS.items(), key=lambda x: -len(x[0])):
            if k in location or location in k:
                city = v
                break
    if city:
        name, lon, lat = _nearest_sea_coords(city[0], city[1])
        logger.info(f"「{location}」→ 最近海域「{name}」({lon}, {lat})")
        return (lon, lat)

    raise ValueError(
        f"未找到「{location}」的海域坐标。请搜索该地经纬度，用 lon/lat 参数直接传入；"
        f"或搜索附近哪个知名海域（如南海、日本海、波斯湾等），用海域名重试。"
    )


def _nearest_sea_coords(lon: float, lat: float) -> tuple[str, float, float]:
    """给定经纬度，返回最近的海域坐标点 (name, lon, lat)。"""
    best_name, best_lon, best_lat = "", lon, lat
    best_dist = float("inf")
    for name, slon, slat in _get_sea_coords_all():
        d = _haversine_km(lon, lat, slon, slat)
        if d < best_dist:
            best_dist = d
            best_name, best_lon, best_lat = name, slon, slat
    return best_name, best_lon, best_lat


def _build_earth_url(params: dict, lon: float, lat: float, time: str) -> str:
    """拼接地球可视化数据的 hash-fragment URL。

    格式: time/mode/height/animation/[annot][anim=off][grid][overlay=xxx]/projection=lon,lat,zoom/loc=lon,lat
    """
    if params["animation"] == "primary/waves":
        segments = [time, params["mode"], params["animation"]]
    else:
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

    url = f"https://earth.nullschool.net/zh-cn/{path}/{view}"
    if not params.get("global_view"):
        url += f"/{loc}"
    return url


_NULLSCHOOL_LOADING_WAIT = (
    "(function(){var l=document.getElementById('load');if(!l)return true;"
    "var s=window.getComputedStyle(l);return s.display==='none'||s.visibility==='hidden';})()"
)


def _format_time_text(time: str) -> str:
    """将 URL 时间片段转为用户可读文本。"""
    if time == "#current":
        return "现在"
    m = re.match(r"^#(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})Z$", time)
    if m:
        y, mo, d, h, mi = m.groups()
        return f"{y}年{int(mo)}月{int(d)}日{h}:{mi}"
    return time


def _normalize_scenario(name: str) -> str:
    """将用户自然表达标准化为场景名。"""
    return name.replace("全世界", "全球").replace("世界", "全球")


def _build_return_text(location: str, time_text: str, scenario: str, page_data: dict) -> str:
    """构建返回给 Agent 的自然语言文本。"""
    # 数据异常：结构化提示给 Agent，由 Agent 决定如何告知用户
    if page_data.get("status_error"):
        return f"[数据获取异常] 站点提示：{page_data['status_error']}"

    # 坐标
    coords_str = f"（{page_data['coords']}）" if page_data.get("coords") else ""

    # 数据值：叠加层（spotB）优先，用户查的就是它；主数据（spotA）作为补充
    values = []
    if page_data.get("spotB.value"):
        label = page_data.get("spotB.label", "")
        if label == "BAA":
            label = "珊瑚白化等级："
            val = page_data["spotB.value"]
            hint = _BAA_LEVEL_MEANING.get(val, "")
            values.append(f"{label}{val}（{hint}）" if hint else f"{label}{val}")
        else:
            values.append(f"{label} {page_data['spotB.value']}" if label else page_data["spotB.value"])
    if page_data.get("spotA.value"):
        label = page_data.get("spotA.label", "")
        values.append(f"{label} {page_data['spotA.value']}" if label else page_data["spotA.value"])
    data_str = "，".join(values) if values else "数据已返回"

    # 数据时间
    time_str = f"，数据时间 {page_data['time']}" if page_data.get("time") else ""

    return (
        f"{location}{coords_str}{time_text}的{scenario}：{data_str}{time_str}"
        f" [本工具只返回{scenario}数据，其他场景请让用户发新的ve查询]"
    )


async def run_ens_normal(
    scenario: str,
    location: str,
    time: str = "#current",
    lon: float | None = None,
    lat: float | None = None,
    zoom: int | None = None,
) -> tuple[str, UniMessage | None]:
    """普通模式核心逻辑。"""
    scenario = _normalize_scenario(scenario)

    params = SCENARIO_MAP.get(scenario)
    if params is None:
        valid = "、".join(SCENARIO_MAP.keys())
        return f"未知场景「{scenario}」。可用场景: {valid}", None

    # 全球视角拒绝
    if scenario.startswith("全球"):
        return (
            f"不支持全球视角查询。请指定具体海域或区域来查看{scenario.replace('全球', '')}数据，"
            "如'南海'、'波斯湾'、'广州沿海'等。",
            None,
        )

    # 硬门控：非 ve 前缀消息触发的调用直接拒绝
    if _ens_prefix.get() != "ve":
        logger.info("ens_normal 被非 ve 前缀触发，拒绝执行")
        return (
            "本次消息未带 ve 前缀，不执行。如需已有数据请传 read_cache=True，"
            "如需新数据请告知用户发送 ve 前缀的新消息。",
            None,
        )

    try:
        from_global_sea = False
        if lon is not None and lat is not None:
            resolved_lon, resolved_lat = lon, lat
        elif params["mode"] == "ocean" or params.get("overlay") == "bleaching_alert_area":
            resolved_lon, resolved_lat = _resolve_sea_coords(location)
            from_global_sea = location.strip() in _GLOBAL_SEA_COORDS
        else:
            resolved_lon, resolved_lat = _resolve_coords(location)

        if zoom is not None:
            params = {**params, "zoom": zoom}

        url = _build_earth_url(params, resolved_lon, resolved_lat, time)

        # 检查内存缓存：同一 URL 60s 内直接返回
        cached = _ens_cache.get(url)
        if cached and (_time.time() - cached[2]) < _ENS_CACHE_TTL:
            logger.info(f"ens_normal 缓存命中: {url}")
            return cached[0], cached[1]  # type: ignore[return-value]

        page_data: dict = {}
        vw, vh = 1920, 1080

        if params.get("anim_state") == "off":
            image_bytes = await screenshot(
                url=url,
                width=vw,
                height=vh,
                wait_until="networkidle",
                timeout=60000,
                wait_selector="canvas",
                wait_function=_NULLSCHOOL_LOADING_WAIT,
                post_wait_ms=5000,
                hard_wait=True,
                ready_timeout=30000,
                page_data_out=page_data,
            )
            time_text = _format_time_text(time)
            text = _build_return_text(location, time_text, scenario, page_data)
            if from_global_sea:
                text += f"（此为{location.strip()}监测点数据）"
            artifact = UniMessage.image(raw=image_bytes)
            _ens_cache[url] = (text, artifact, _time.time())
            return text, artifact
        else:
            video_bytes = await record_video(
                url=url,
                duration=3,
                width=vw,
                height=vh,
                wait_until="networkidle",
                timeout=60000,
                wait_selector="canvas",
                wait_function=_NULLSCHOOL_LOADING_WAIT,
                post_wait_ms=5000,
                hard_wait=True,
                ready_timeout=30000,
                page_data_out=page_data,
            )
            time_text = _format_time_text(time)
            text = _build_return_text(location, time_text, scenario, page_data)
            if from_global_sea:
                text += f"（此为{location.strip()}监测点数据）"
            artifact = UniMessage.video(raw=video_bytes)
            _ens_cache[url] = (text, artifact, _time.time())
            return text, artifact
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
    """地球可视化——将气象/海洋/化学等数据以动画呈现在三维地球上，返回视频或截图。

    ⚠️ 仅在用户消息以 "ve" 开头时调用。严禁在用户未发送 ve 前缀消息时推荐本工具。

    本工具的定位是地球数据可视化，不是常规气象查询。温度、风力、PM2.5 等
    常规数值优先用网络搜索获取，不要主动推荐 ENS。

    不支持全球视角查询。用户说"全世界""全球"等，告知不支持并引导其指定具体海域或区域。

    海洋场景要求位置在海上。Agent 确认目标位置是否沿海，内陆直接告知用户。

    ve 前缀消息触发后，直接调用本工具即可，无需在此之前用 Wikipedia 等搜索地理信息。

    用户询问功能或使用方法，告知发送 /vehelp 命令查看菜单。
    ⚠️ 用户追问历史 ENS 数据时，禁止调本工具。直接回复让其翻聊天记录。

    可用场景清单（scenario 参数必须精确匹配下列名称之一）：
    大气：风速、温度、体感温度、相对湿度、3小时降水、平均海平面压力、
    紫外线指数、CAPE、水汽含量、露点温度、湿球温度、总云水量、
    风功率密度、大气无叠加
    海洋：洋流、有效浪高、波峰周期、海面温度、海面温度异常、
    洋流波峰周期、洋流珊瑚白化、洋流无叠加、
    波浪、波浪有效浪高、波浪海面温度、波浪海面温度异常、
    波浪珊瑚白化、波浪无叠加
    化学：一氧化碳浓度、二氧化碳浓度、二氧化硫质量、二氧化氮浓度
    颗粒物：PM2.5、PM10、PM1、尘埃消光、有机物气溶胶、硫酸盐消光
    空间天气：极光（需指定位置，不可缺省）
    生物：珊瑚白化、活跃火点

    Args:
        scenario: 场景中文名，必须从上方清单中精确选取
        location: 位置描述，国内城市/海域走内置坐标，国外由 Agent 搜坐标后传入
        time: 时间，默认 #current
        lon: 经度，传入后跳过坐标查询
        lat: 纬度
        zoom: 缩放等级，传入后覆盖默认值

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 视频或截图)
    """
    async with tool_timer("ens_normal", {"scenario": scenario, "location": location, "time": time}):
        return await run_ens_normal(
            scenario=scenario,
            location=location,
            time=time,
            lon=lon,
            lat=lat,
            zoom=zoom,
        )
