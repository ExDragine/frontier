"""台风信息查询工具。

API 数据 → Jinja2 渲染 HTML → Playwright 截图 → QQ 发送。
"""

import base64
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client
from utils.markdown_render import _get_browser
from utils.reverse_geocode import reverse_geocode

# ── 路径 ──
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
IMAGES_DIR = TEMPLATES_DIR / "images"

# ── API ──
API_URL = "https://mp.wztf121.com/data/wzweather/complex/currMerger.json"
API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

httpx_client = get_http_client("typhoon")

# ── 强度等级 ──
_INTENSITY_KEYS = ["超强台风", "强台风", "台风", "强热带风暴", "热带风暴", "热带低压"]

_INTENSITY_COLORS: dict[str, str] = {
    "热带低压": "#1afa29",
    "热带风暴": "#1296db",
    "强热带风暴": "#f4ea2a",
    "台风": "#FFB300",
    "强台风": "#FB8C00",
    "超强台风": "#E53935",
}

# ── 预报机构固定颜色 ──
_FORECAST_COLORS: dict[str, str] = {
    "中国": "#FF0000",
    "中国台湾": "#00BCD4",
    "中国香港": "#FF5722",
    "日本": "#3F51B5",
    "韩国": "#4CAF50",
    "美国": "#FF9800",
    "菲律宾": "#9C27B0",
}

# ── 图标缓存 ──
_icon_cache: dict[str, str] = {}


# ═══════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════

def _get_level_key(strong: str) -> str:
    for key in _INTENSITY_KEYS:
        if key in strong:
            return key
    return "热带低压"


def _get_level_color(strong: str) -> str:
    return _INTENSITY_COLORS.get(_get_level_key(strong), "#888888")


def _get_icon_base64(level_key: str) -> str:
    """读取对应等级的 PNG 图标并缓存为 base64 data URL。"""
    if level_key not in _icon_cache:
        icon_path = IMAGES_DIR / f"{level_key}.png"
        if icon_path.exists():
            b64 = base64.b64encode(icon_path.read_bytes()).decode("ascii")
            _icon_cache[level_key] = f"data:image/png;base64,{b64}"
        else:
            _icon_cache[level_key] = ""
    return _icon_cache[level_key]





# ═══════════════════════════════════════════════
#  API 请求
# ═══════════════════════════════════════════════

async def _fetch_typhoon_data() -> list[dict] | None:
    try:
        ts = int(datetime.now().timestamp() * 1000)
        resp = await httpx_client.get(API_URL, headers=API_HEADERS, params={"v": ts})
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            logger.warning("台风 API 返回格式异常: %s", type(data))
            return None
        return data
    except Exception as e:
        logger.error(f"台风 API 请求失败: {e}")
        return None


async def _get_typhoon_data() -> list[dict] | None:
    return await _fetch_typhoon_data()


# ═══════════════════════════════════════════════
#  数据处理
# ═══════════════════════════════════════════════

def _format_time(iso_str: str) -> tuple[str, str]:
    """ISO 时间 → (line1: HH:mm, line2: YYYY年MM月DD日)。"""
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S")
        line1 = dt.strftime("%H:%M")
        line2 = dt.strftime("%Y年%m月%d日")
        return line1, line2
    except ValueError:
        return iso_str, iso_str


def _format_coords(lng: float, lat: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lng >= 0 else "W"
    return f"{abs(lng):.1f}°{ew}, {abs(lat):.1f}°{ns}"


def _get_valid_points(points: list[dict]) -> list[dict]:
    return [p for p in points if p.get("lng") is not None and p.get("lat") is not None]


def _process_forecasts(points: list[dict]) -> list[dict[str, Any]]:
    """合并所有历史轨迹点中出现的预报路径（按机构去重）。"""
    seen_agencies: set[str] = set()
    paths: list[dict[str, Any]] = []

    for p in points:
        forecast_raw = p.get("forecast")
        if not forecast_raw:
            continue
        for fc in forecast_raw:
            agency = fc.get("sets", "")
            if not agency or agency in seen_agencies:
                continue
            fc_points = []
            for fcp in fc.get("points", []):
                if fcp.get("lng") is not None and fcp.get("lat") is not None:
                    fc_points.append([fcp["lng"], fcp["lat"]])
            if len(fc_points) >= 2:
                seen_agencies.add(agency)
                paths.append({
                    "agency": agency,
                    "color": _FORECAST_COLORS.get(agency, "#888888"),
                    "points": fc_points,
                })

    return paths


# ═══════════════════════════════════════════════
#  HTML 渲染
# ═══════════════════════════════════════════════

def _load_css() -> str:
    return (TEMPLATES_DIR / "typhoon.css").read_text(encoding="utf-8")


def _build_template_data(typhoon: dict, pos_desc: str) -> dict[str, Any]:
    points = _get_valid_points(typhoon.get("points", []))
    if not points:
        raise ValueError("台风轨迹点数据为空")

    current = points[-1]
    strong = current.get("strong", "")
    level_key = _get_level_key(strong)
    level_color = _INTENSITY_COLORS.get(level_key, "#888888")
    time_l1, time_l2 = _format_time(current.get("time", ""))

    # 历史轨迹
    history_points = [
        {"lat": p["lat"], "lng": p["lng"], "color": _get_level_color(p.get("strong", ""))}
        for p in points
    ]
    history_polyline = [[p["lng"], p["lat"]] for p in points]

    # 预报路径（合并所有时间点）
    forecast_paths = _process_forecasts(points)

    # 风圈
    radius7 = current.get("radius7")
    radius10 = current.get("radius10")
    radius12 = current.get("radius12")

    move_speed = current.get("move_speed")

    # 当前等级图标
    icon_base64 = _get_icon_base64(level_key)

    typhoon_data_json = {
        "historyPoints": history_points,
        "historyPolyline": history_polyline,
        "forecastPaths": forecast_paths,
        "currentPos": [current["lat"], current["lng"]],
        "currentColor": level_color,
        "windRadius7": radius7,
        "windRadius7Quad": current.get("radius7_quad"),
        "windRadius10": radius10,
        "windRadius10Quad": current.get("radius10_quad"),
        "windRadius12": radius12,
        "windRadius12Quad": current.get("radius12_quad"),
        "iconBase64": icon_base64,
    }

    return {
        "css_content": _load_css(),
        "name": typhoon.get("name", ""),
        "ename": typhoon.get("ename", ""),
        "tfbh": typhoon.get("tfbh", ""),
        "begin_time": typhoon.get("begin_time", "")[:10],
        "level_display": strong,
        "level_color": level_color,
        "time_line1": time_l1,
        "time_line2": time_l2,
        "pos_coords": _format_coords(current["lng"], current["lat"]),
        "pos_desc": pos_desc or "未知区域",
        "power": current.get('power', '?'),
        "speed": current.get('speed', '?'),
        "pressure_val": current.get('pressure', '?'),
        "move_speed_val": move_speed,
        "typhoon_data": typhoon_data_json,
    }


def _render_html(template_data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("typhoon.html")
    return template.render(**template_data)


# ═══════════════════════════════════════════════
#  截图
# ═══════════════════════════════════════════════

async def _screenshot_card(html: str) -> bytes:
    cache_file = f"cache/{secrets.token_hex(16)}.html"
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(html)

    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": 1200, "height": 800})
    try:
        await page.goto(f"file://{Path(cache_file).resolve()}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        elem = await page.query_selector("#typhoon-card")
        if elem is None:
            raise RuntimeError("未找到 typhoon-card 元素")

        image = await elem.screenshot(type="png")
        return image
    finally:
        close_fn = getattr(page, "close", None)
        if close_fn:
            await close_fn()
        try:
            Path(cache_file).unlink(missing_ok=True)
        except Exception as e:
            logger.warning("删除临时文件失败: %s", e)


async def _render_single_typhoon(target: dict) -> bytes | None:
    """渲染单个台风信息为 PNG 字节。"""
    points = _get_valid_points(target.get("points", []))
    if not points:
        return None
    current = points[-1]
    pos_desc = await reverse_geocode(current["lat"], current["lng"])
    tmpl_data = _build_template_data(target, pos_desc)
    html = _render_html(tmpl_data)
    return await _screenshot_card(html)


# ═══════════════════════════════════════════════
#  工具
# ═══════════════════════════════════════════════

def _find_typhoon_by_name(data: list[dict], name: str) -> dict | None:
    name_lower = name.strip().lower()
    for t in data:
        if t.get("is_current") != 1:
            continue
        if t.get("name", "").lower() == name_lower or t.get("ename", "").lower() == name_lower:
            return t
        if name_lower in t.get("name", "").lower() or name_lower in t.get("ename", "").lower():
            return t
    return None


@tool(response_format="content_and_artifact")
async def get_typhoon_info(typhoon_name: str | None = None) -> tuple[str, UniMessage | None]:
    """查询当前活跃的台风信息。

    当用户询问「现在有什么台风」「台风路径」「xx台风」时调用此工具。
    返回带地图路径、预报路径和信息面板的截图图片。

    注意：图片已包含所有路径详情，绝对不要追问用户「需要看具体哪个」「要看路径吗」
    之类的问题。直接展示图片即可。

    Args:
        typhoon_name: 可选，台风名称（中文或英文，如「米克拉」或「MEKKHALA」）。
                      不传或为空时返回所有活跃台风的信息。
    """
    data = await _get_typhoon_data()
    if data is None:
        return "获取台风数据失败，请稍后再试", None

    active = [t for t in data if t.get("is_current") == 1]
    if not active:
        return "当前没有活跃的台风", None

    # 确定要展示的台风
    if typhoon_name:
        target = _find_typhoon_by_name(active, typhoon_name)
        if target is None:
            names = "、".join(t.get("name", "?") for t in active)
            return f"未找到台风「{typhoon_name}」。当前活跃台风：{names}", None
        targets = [target]
    else:
        targets = active

    # 并发渲染
    import asyncio

    results = await asyncio.gather(
        *[_render_single_typhoon(t) for t in targets], return_exceptions=True
    )

    images: list[UniMessage] = []
    for t, r in zip(targets, results):
        if isinstance(r, Exception):
            logger.error("台风「%s」渲染失败: %s", t.get("name", "?"), r)
            continue
        if r is not None:
            images.append(UniMessage.image(raw=r))

    if not images:
        return "台风信息渲染失败，请稍后再试", None

    # 拼接文字摘要（路径详情已包含在图片中）
    if len(active) == 1:
        summary = f"当前活跃台风「{active[0]['name']}」，路径情况如下："
    else:
        names_str = "、".join(t.get("name", "?") for t in active)
        summary = f"当前活跃台风有 {names_str}，路径情况如下："

    # 拼接所有图片
    result_msg = images[0]
    for m in images[1:]:
        result_msg += m

    return summary, result_msg
