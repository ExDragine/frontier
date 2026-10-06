"""地球可视化数据 普通模式工具。

预设场景方案，LLM 匹配场景名 + 提取位置/时间 → 拼接 URL → 截图或录屏返回。
动画播放时返回视频，动画暂停时（空间天气等）返回截图。

触发方式：用户直接问气象数据即可（如"北京PM2.5多少"），LLM 自动路由到本工具。
国内城市走内置坐标字典，国外/特殊位置由 LLM 搜索经纬度后直接传入 lon/lat。
"""

import json
import math
from pathlib import Path

from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.browser_capture import fetch_data_only, record_video, screenshot
from utils.ens_common import (
    CITY_COORDS,
    build_earth_url,
    build_return_text,
    earth_capture_options,
    match_coords,
)
from utils.ens_common import EARTH_LOADING_WAIT as _EARTH_LOADING_WAIT
from utils.ens_common import format_time_text as _format_time_text
from utils.tool_helpers import tool_timer

# BAA 等级含义（用于 tool 返回时附带说明，Agent 可据此解读）
_BAA_LEVEL_MEANING: dict[str, str] = {
    "无压力": "海温正常，未超过珊瑚耐热阈值，珊瑚健康无白化风险",
    "No Stress": "海温正常，未超过珊瑚耐热阈值，珊瑚健康无白化风险",
    "珊瑚白化监测": "海温开始偏高，预计未来几周内可能达到白化阈值，需密切关注",
    "Bleaching Watch": "海温开始偏高，预计未来几周内可能达到白化阈值，需密切关注",
    "珊瑚白化警报": "海温已接近或略微超过白化阈值，白化即将或刚开始发生",
    "Bleaching Warning": "海温已接近或略微超过白化阈值，白化即将或刚开始发生",
    "警报等级 1": "海温显著超标，白化正在发生但珊瑚尚可存活（DHW≥4）",
    "Alert Level 1": "海温显著超标，白化正在发生但珊瑚尚可存活（DHW≥4）",
    "警报等级 2": "更严重热应力，广泛白化且部分珊瑚开始死亡（DHW≥8）",
    "Alert Level 2": "更严重热应力，广泛白化且部分珊瑚开始死亡（DHW≥8）",
    "警报等级 3": "严重白化，大量珊瑚死亡（DHW≥12）",
    "Alert Level 3": "严重白化，大量珊瑚死亡（DHW≥12）",
    "警报等级 4": "极严重白化，多数珊瑚死亡（DHW≥16）",
    "Alert Level 4": "极严重白化，多数珊瑚死亡（DHW≥16）",
    "警报等级 5": "灾难级白化，近乎全部珊瑚死亡（DHW≥20）",
    "Alert Level 5": "灾难级白化，近乎全部珊瑚死亡（DHW≥20）",
}


# ── 数据表（data/ens/*.json）──
# 场景映射表：key 为中文场景名，LLM 通过 docstring 中列出的清单做精确匹配。
# anim_state="off" 表示该场景动画默认暂停，应返回截图。
_ENS_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ens"


def _load_ens_data(name: str) -> object:
    """读取 data/ens/ 下的 JSON 数据表。"""
    return json.loads((_ENS_DATA_DIR / name).read_text(encoding="utf-8"))


def _load_coords_table(name: str) -> dict[str, tuple[float, float]]:
    """读取 (lon, lat) 坐标表，还原为 tuple 以保持原有类型。"""
    return {key: tuple(value) for key, value in _load_ens_data(name).items()}


SCENARIO_MAP: dict[str, dict] = _load_ens_data("scenario_map.json")
# ── 国内城市坐标字典（lon, lat）── 与专业模式共用 utils/ens_common.py 中的同一张表
_CITY_COORDS: dict[str, tuple[float, float]] = CITY_COORDS
# ── 近海 / 全球海域坐标字典（lon, lat）──
_COASTAL_SEA_COORDS: dict[str, tuple[float, float]] = _load_coords_table("coastal_sea_coords.json")
_GLOBAL_SEA_COORDS: dict[str, tuple[float, float]] = _load_coords_table("global_sea_coords.json")


def _resolve_coords(location: str) -> tuple[float, float]:
    """根据位置文本解析经纬度（纯字典查找，不需要外部 API）。"""
    if not location or not location.strip():
        raise ValueError("位置不能为空")

    location = location.strip()

    # 1) 精确匹配
    if location in _CITY_COORDS:
        return _CITY_COORDS[location]

    # 2) 模糊匹配（最长优先）
    match = match_coords(location, _CITY_COORDS)
    if match is not None:
        return match

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


def _match_location(location: str, coords_table: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    """按最长名称优先查找模糊匹配，精确匹配由调用方先处理。"""
    return match_coords(location, coords_table)


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

    # 保持近海优先、名称最长优先的模糊匹配顺序。
    for coords_table in (_COASTAL_SEA_COORDS, _GLOBAL_SEA_COORDS):
        match = _match_location(location, coords_table)
        if match is not None:
            return match

    # 5) 兜底：城市坐标 → 最近海域
    city = _CITY_COORDS.get(location) or _match_location(location, _CITY_COORDS)
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
    """拼接地球可视化数据的 hash-fragment URL。"""
    return build_earth_url(
        time=time,
        mode=params["mode"],
        height=params["height"],
        animation=params["animation"],
        projection=params["projection"],
        lon=lon,
        lat=lat,
        zoom=params["zoom"],
        annot=params.get("annotation"),
        anim_state=params.get("anim_state"),
        grid=params.get("grid"),
        overlay=params.get("overlay"),
        include_loc=not params.get("global_view"),
    )


def _build_return_text(location: str, time_text: str, scenario: str, page_data: dict) -> str:
    """构建返回给 Agent 的自然语言文本。"""
    return build_return_text(
        location,
        time_text,
        scenario,
        page_data,
        prefix="ve",
        report_status_error=True,
        baa_level_meanings=_BAA_LEVEL_MEANING,
    )


async def _capture_query_result(url: str, params: dict, no_video: bool) -> tuple[dict, bytes, bool]:
    """按输出模式获取数据或媒体，统一浏览器等待条件。"""
    if no_video:
        page_data = await fetch_data_only(
            url=url, wait_selector="canvas", wait_function=_EARTH_LOADING_WAIT,
        )
        return page_data, b"", False

    page_data: dict = {}
    capture_options = earth_capture_options(url, page_data)
    if params.get("anim_state") == "off":
        return page_data, await screenshot(**capture_options), False
    return page_data, await record_video(duration=3, **capture_options), True


async def _execute_single_query(
    scenario: str,
    location: str,
    time: str = "#current",
    lon: float | None = None,
    lat: float | None = None,
    zoom: int | None = None,
    no_video: bool = False,
) -> tuple[str, bytes, bool]:
    """执行单个 ENS 查询。no_video=True 时仅提取数据不录制，返回空 bytes。"""
    scenario = scenario.replace("全世界", "全球").replace("世界", "全球")

    if scenario == "活跃火点":
        no_video = False

    params = SCENARIO_MAP.get(scenario)
    if params is None:
        valid = "、".join(SCENARIO_MAP.keys())
        raise ValueError(f"未知场景「{scenario}」。可用场景: {valid}")

    if scenario.startswith("全球"):
        raise ValueError(
            f"不支持全球视角查询。请指定具体区域来查看{scenario.replace('全球', '')}数据。"
        )

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

    page_data, media, is_video = await _capture_query_result(url, params, no_video)
    text = _build_return_text(location, _format_time_text(time), scenario, page_data)
    if from_global_sea:
        text += f"（此为{location.strip()}监测点数据）"
    return text, media, is_video


def _build_batch_artifact(raw_parts: list[tuple[bytes, bool]]) -> UniMessage | None:
    artifact: UniMessage | None = None
    if raw_parts:
        first_bytes, first_is_video = raw_parts[0]
        artifact = (
            UniMessage.video(raw=first_bytes) if first_is_video
            else UniMessage.image(raw=first_bytes)
        )
        for raw, is_video in raw_parts[1:]:
            if is_video:
                artifact.video(raw=raw)
            else:
                artifact.image(raw=raw)

    return artifact


async def _execute_query_batch(queries: list[dict], time: str, no_video: bool) -> tuple[str, UniMessage | None]:
    if len(queries) > 3:
        return f"最多支持同时查询 3 个地点，当前传入了 {len(queries)} 个。请精简后重试。", None
    if len(queries) == 0:
        return "查询列表为空，请提供至少一个地点。", None

    texts: list[str] = []
    raw_parts: list[tuple[bytes, bool]] = []

    for q in queries:
        q_scenario = q.get("scenario", "")
        q_location = q.get("location", "")
        try:
            t, raw, is_video = await _execute_single_query(
                q_scenario, q_location, time, no_video=no_video,
            )
            texts.append(t)
            if raw:
                raw_parts.append((raw, is_video))
        except Exception as e:
            logger.error(f"ens_normal 多地点失败 [{q_location}{q_scenario}]: {e}")
            texts.append(f"[{q_location}{q_scenario}获取失败: {e}]")

    artifact = _build_batch_artifact(raw_parts)

    summary = "\n\n".join(texts)
    summary += "\n\n——以上为本次多地点查询的全部结果。"
    return summary, artifact


async def run_ens_normal(
    scenario: str = "",
    location: str = "",
    time: str = "#current",
    lon: float | None = None,
    lat: float | None = None,
    zoom: int | None = None,
    queries: list[dict] | None = None,
    no_video: bool = False,
) -> tuple[str, UniMessage | None]:
    """普通模式核心逻辑。"""

    if queries is not None:
        return await _execute_query_batch(queries, time, no_video)

    # ── 单地点分支 ──
    try:
        text, raw_bytes, is_video = await _execute_single_query(
            scenario, location, time, lon, lat, zoom, no_video=no_video,
        )
        if no_video and not raw_bytes:
            return text, None
        artifact = UniMessage.video(raw=raw_bytes) if is_video else UniMessage.image(raw=raw_bytes)
        return text, artifact
    except Exception as e:
        logger.error(f"ens_normal 失败 [{scenario}/{location}]: {e}")
        return f"获取失败: {e}", None


@tool(response_format="content_and_artifact")
async def ens_normal(
    scenario: str = "",
    location: str = "",
    queries: str | list | None = None,
    no_video: bool = False,
    time: str = "#current",
    lon: float | None = None,
    lat: float | None = None,
    zoom: int | None = None,
) -> tuple[str, UniMessage | None]:
    """地球气象数据查询。

    默认文字模式：用户问"北京PM2.5""广州体感温度"等 → 直接调用，no_video=True，只返文字。
    多地点：queries 参数传 JSON 数组（最多3个）。
    用户要看视频/动画时 no_video=False，会录制视频返回。

    不支持全球视角。地点不在字典时 Agent 搜经纬度用 lon/lat 重调。用户问功能 → /vehelp。
    活跃火点只能看图，no_video 无效始终返回视频。

    可用场景清单（scenario 参数必须精确匹配下列名称之一）：
    大气：风速、温度、体感温度、相对湿度、3小时降水、平均海平面压力、
    紫外线指数、CAPE、水汽含量、露点温度、湿球温度、总云水量、
    风功率密度、大气无叠加
    海洋：洋流、有效浪高、波峰周期、海面温度、海面温度异常、
    洋流波峰周期、洋流珊瑚白化（别名BAA）、洋流无叠加、
    波浪、波浪有效浪高、波浪海面温度、波浪海面温度异常、
    波浪珊瑚白化、波浪无叠加
    化学：一氧化碳浓度、二氧化碳浓度、二氧化硫质量、二氧化氮浓度
    颗粒物：PM2.5、PM10、PM1、尘埃消光、有机物气溶胶、硫酸盐消光
    空间天气：极光（需指定位置，不可缺省）
    生物：珊瑚白化、活跃火点

    Args:
        scenario: 场景中文名（单地点模式），必须从上方清单中精确选取
        location: 位置描述（单地点模式），国内城市/海域走内置坐标
        queries: 多地点查询 JSON 数组（多地点模式），如 [{"scenario":"PM2.5","location":"北京"}]
        no_video: 用户明确说不要视频/只要数据时设为 True，只返回文字不返回媒体
        cache_only: 缓存复用场景设为 True，缓存未命中直接返回过期提示而不重新录制
        time: 时间，默认 #current
        lon: 经度，传入后跳过坐标查询
        lat: 纬度
        zoom: 缩放等级，传入后覆盖默认值

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 视频或截图)
    """
    parsed_queries: list[dict] | None = None
    if queries is not None:
        if isinstance(queries, list):
            parsed_queries = queries
        elif isinstance(queries, str):
            try:
                parsed_queries = json.loads(queries)
            except json.JSONDecodeError:
                return f"queries 参数 JSON 解析失败: {queries}", None
        else:
            return f"queries 参数类型不支持（需要 JSON 字符串或数组），收到: {type(queries)}", None

    async with tool_timer("ens_normal", {"scenario": scenario, "location": location, "queries": parsed_queries, "no_video": no_video, "time": time}):
        return await run_ens_normal(
            scenario=scenario,
            location=location,
            time=time,
            lon=lon,
            lat=lat,
            zoom=zoom,
            queries=parsed_queries,
            no_video=no_video,
        )
