"""ENS（earth.nullschool.net）普通模式与专业模式共享的构造与格式化逻辑。

两个工具原先各自复制了一份页面等待条件、时间文案、返回文本、捕获参数和
URL 拼接；这里收拢为唯一实现，两个模块只保留各自确有差异的分支
（普通模式的 ``global_view``、专业模式的 ``primary/waves`` 动画与暂停标记）。
"""

import json
import re
from pathlib import Path

# 页面就绪判定：地球可视化站的 #load 遮罩隐藏即视为加载完成。
EARTH_LOADING_WAIT = (
    "(function(){var l=document.getElementById('load');if(!l)return true;"
    "var s=window.getComputedStyle(l);return s.display==='none'||s.visibility==='hidden';})()"
)

_ENS_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ens"


def _load_coords_table(name: str) -> dict[str, tuple[float, float]]:
    """读取 (lon, lat) 坐标表，还原为 tuple 以保持原有类型。"""
    raw = json.loads((_ENS_DATA_DIR / name).read_text(encoding="utf-8"))
    return {key: tuple(value) for key, value in raw.items()}


# 城市名 → (lon, lat)；普通模式与专业模式共用同一张表。
CITY_COORDS: dict[str, tuple[float, float]] = _load_coords_table("city_coords.json")


def earth_capture_options(url: str, page_data_out: dict) -> dict:
    """统一的浏览器捕获参数（截图与录屏共用，宽度/等待条件/超时全部一致）。"""
    return {
        "url": url,
        "width": 1920,
        "height": 1080,
        "wait_until": "networkidle",
        "timeout": 60000,
        "wait_selector": "canvas",
        "wait_function": EARTH_LOADING_WAIT,
        "post_wait_ms": 5000,
        "hard_wait": True,
        "ready_timeout": 30000,
        "page_data_out": page_data_out,
    }


def format_time_text(time: str) -> str:
    """将 URL 时间片段转为用户可读文本。"""
    if time == "#current":
        return "现在"
    m = re.match(r"^#(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})Z$", time)
    if m:
        y, mo, d, h, mi = m.groups()
        return f"{y}年{int(mo)}月{int(d)}日{h}:{mi}"
    return time


def build_earth_url(
    *,
    time: str,
    mode: str,
    height: str,
    animation: str,
    projection: str,
    lon: float,
    lat: float,
    zoom: int,
    annot: str | None = None,
    anim_state: str | None = None,
    grid: int | str | None = None,
    overlay: str | None = None,
    include_loc: bool = True,
) -> str:
    """拼接 hash-fragment URL。

    格式: ``time/mode/height/animation/[annot][anim=off][grid][overlay=xxx]/projection=lon,lat,zoom[/loc=lon,lat]``

    ``animation == "primary/waves"`` 时省略 height 段落（专业模式波浪动画）；
    ``include_loc=False`` 用于普通模式的全球视角，不追加 ``loc`` 段落。
    """
    segments = (
        [time, mode, animation] if animation == "primary/waves" else [time, mode, height, animation]
    )

    if annot:
        segments.append(f"annot={annot}")
    if anim_state:
        segments.append(f"anim={anim_state}")
    if grid:
        segments.append(f"grid={grid}")
    if overlay is not None:
        segments.append(f"overlay={overlay}")

    path = "/".join(segments)
    url = f"https://earth.nullschool.net/zh-cn/{path}/{projection}={lon},{lat},{zoom}"
    if include_loc:
        url += f"/loc={lon},{lat}"
    return url


def match_coord_entry(
    location: str, coords_table: dict[str, tuple[float, float]]
) -> tuple[str, tuple[float, float]] | None:
    """按名称最长优先做模糊匹配，返回 ``(名称, 坐标)``；精确匹配由调用方先行处理。"""
    for name, coords in sorted(coords_table.items(), key=lambda item: -len(item[0])):
        if name in location or location in name:
            return name, coords
    return None


def match_coords(location: str, coords_table: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    """按名称最长优先做模糊匹配，只返回坐标；精确匹配由调用方先行处理。"""
    entry = match_coord_entry(location, coords_table)
    return entry[1] if entry is not None else None


def build_return_text(
    location_text: str,
    time_text: str,
    subject: str,
    page_data: dict,
    *,
    prefix: str,
    report_status_error: bool = False,
    baa_level_meanings: dict[str, str] | None = None,
) -> str:
    """构建返回给 Agent 的自然语言文本。

    Args:
        location_text: 位置展示文本（普通模式为原始输入，专业模式为解析结果）。
        time_text: 已格式化的时间文案。
        subject: 普通模式为场景名，专业模式为模式名。
        page_data: 浏览器抽取的页面数据。
        prefix: 触发前缀，``"ve"`` 或 ``"vep"``，只影响结尾提示文案。
        report_status_error: 是否把站点 ``status_error`` 作为数据异常返回（普通模式）。
        baa_level_meanings: 提供时对 ``BAA`` 叠加层补充等级说明（普通模式）。

    Returns:
        str: 可直接给模型使用的返回文本。
    """
    if report_status_error and page_data.get("status_error"):
        return f"[数据获取异常] 站点提示：{page_data['status_error']}"

    coords_str = f"（{page_data['coords']}）" if page_data.get("coords") else ""

    # 数据值：叠加层（spotB）优先，用户查的就是它；主数据（spotA）作为补充
    values = []
    if page_data.get("spotB.value"):
        label = page_data.get("spotB.label", "")
        if baa_level_meanings is not None and label == "BAA":
            label = "珊瑚白化等级："
            val = page_data["spotB.value"]
            hint = baa_level_meanings.get(val, "")
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
        f"{location_text}{coords_str}{time_text}的{subject}：{data_str}{time_str}"
        f" [本工具只返回{subject}数据，其他场景请让用户发新的{prefix}查询]"
    )
