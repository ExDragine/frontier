"""洛克王国精灵蛋孵蛋查询工具。

根据用户提供的直径和重量数据，查询可能孵化的精灵信息。
API 数据 → Jinja2 模板渲染 HTML → Playwright 截图 → QQ 发送。
"""


from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client
from utils.markdown_render import html_to_image

from ._nrc_common import (
    API_HEADERS,
    get_danzu_color,
    load_css,
    parse_danzu_names,
    render_template,
)

API_URL = "https://ap.xiaopidd.com/api.AppletXCX/getXcxfdcaijiListByZjzl"
IMAGE_BASE = "https://images.xiaopiaa.com/static/storage/"

httpx_client = get_http_client("nrc_eggs")


async def fetch_eggs_data(zj: str, zl: str, istc: str = "2") -> list[dict] | None:
    """获取孵蛋数据。失败返回 None。

    API 响应结构: {"code": 0, "data": {"data": [...]}}，本函数提取内层列表。
    """
    try:
        resp = await httpx_client.get(
            API_URL,
            params={"zj": zj, "zl": zl, "istc": istc},
            headers=API_HEADERS,
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict):
            return payload.get("data", {}).get("data", [])
        return payload if isinstance(payload, list) else []
    except Exception as e:
        logger.error(f"孵蛋 API 请求失败: {e}")
        return None


def _parse_danzu(danzu_raw) -> str:
    """将蛋组数字（可能逗号分隔）转为中文名称，用斜杠连接。"""
    return parse_danzu_names(danzu_raw)


def _get_danzu_color(danzu_raw) -> str:
    """获取第一个蛋组对应的颜色。"""
    return get_danzu_color(danzu_raw)


def _parse_prob(prob_raw) -> str:
    """将概率值（科学计数法或普通数字）转为百分数字符串，截断到两位小数（不四舍五入）。

    例如: 0.156 → "15.60", 1e-11 → "0.00", 0 → "0.00"
    """
    if prob_raw is None:
        return "0.00"
    try:
        value = float(str(prob_raw)) * 100
    except ValueError, TypeError:
        return "0.00"
    # 截断到两位小数：将浮点数展开到高精度字符串，取前两位小数
    s = f"{value:.10f}"
    dot = s.find(".")
    if dot == -1:
        return f"{s}.00"
    integer_part = s[:dot]
    decimal_part = s[dot + 1 : dot + 3]
    return f"{integer_part}.{decimal_part}"


def _prob_width(prob_raw) -> str:
    """概率 → 进度条宽度百分比（0-100）。"""
    try:
        value = float(str(prob_raw)) * 100
    except ValueError, TypeError:
        return "0"
    clamped = max(0, min(100, int(value)))
    return str(clamped)


def _prob_color(prob_raw) -> str:
    """根据概率返回进度条颜色。"""
    try:
        value = float(str(prob_raw)) * 100
    except ValueError, TypeError:
        return "#ef4444"
    if value >= 50:
        return "#10b981"
    if value >= 30:
        return "#f59e0b"
    if value >= 10:
        return "#f97316"
    return "#ef4444"


_RANK_BADGE_COLORS = {
    0: ("#dc2626", "#ffffff"),
    1: ("#ef4444", "#ffffff"),
    2: ("#f97316", "#ffffff"),
}


def _rank_badge_style(rank: int) -> tuple[str, str]:
    """返回 (背景色, 文字色)。"""
    bg, fg = _RANK_BADGE_COLORS.get(rank, ("#6b7280", "#ffffff"))
    return bg, fg


def _build_items(items: list[dict]) -> list[dict]:
    """将 API 返回的 items 转为模板所需字段。只取前 10 个。"""
    result = []
    for idx, item in enumerate(items[:10]):
        name = item.get("name", "?")
        danzu_raw = item.get("danzu", "")
        prob_raw = item.get("prob", "0")
        pic = item.get("pic", "")

        prob_display = _parse_prob(prob_raw)
        rank_bg, rank_fg = _rank_badge_style(idx)

        result.append(
            {
                "name": name,
                "danzu_display": _parse_danzu(danzu_raw),
                "danzu_color": _get_danzu_color(danzu_raw),
                "prob_display": prob_display,
                "prob_width": _prob_width(prob_raw),
                "prob_color": _prob_color(prob_raw),
                "image_url": IMAGE_BASE + pic if pic else "",
                "rank": idx + 1,
                "rank_bg": rank_bg,
                "rank_fg": rank_fg,
            }
        )
    return result


def _render_html(zj: str, zl: str, items: list[dict]) -> str:
    """Jinja2 渲染：数据 → HTML 片段。"""
    return render_template("nrc_eggs_details.html", zj=zj, zl=zl, items=items)


def _load_css() -> str:
    return load_css("nrc_eggs_details.css")


def _summary_text(zj: str, zl: str, items: list[dict]) -> str:
    """纯文本摘要，图片渲染失败时的降级输出。"""
    lines = [f"洛克王国孵蛋查询 · 直径:{zj} 重量:{zl}"]
    if not items:
        lines.append("未找到匹配的精灵蛋数据")
    lines.extend(
        f"  {item['rank']}. [{item['danzu_display']}] {item['name']} - 概率: {item['prob_display']}%"
        for item in items
    )
    return "\n".join(lines)


@tool(response_format="content_and_artifact")
async def get_nrc_eggs_details(zj: str, zl: str) -> tuple[str, UniMessage | None]:
    """查询洛克王国精灵蛋孵化结果。

    根据精灵蛋的直径（zj）和重量（zl）查询可能孵化的精灵信息。
    用户给到直径和重量的数值后调用此工具。

    Args:
        zj: 精灵蛋直径（单位：厘米）
        zl: 精灵蛋重量（单位：千克）

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 孵蛋结果截图)
    """
    raw_data = await fetch_eggs_data(zj=zj, zl=zl)
    if raw_data is None:
        return "获取孵蛋数据失败，请稍后重试", None

    if not raw_data:
        return f"直径 {zj}、重量 {zl} 的精灵蛋未找到匹配的孵化结果", None

    items = _build_items(raw_data)

    try:
        html = _render_html(zj=zj, zl=zl, items=items)
        css = _load_css()
        image = await html_to_image(html, css=css, width=480)
        summary = _summary_text(zj=zj, zl=zl, items=items)
        return summary, UniMessage.image(raw=image)
    except Exception as e:
        logger.error(f"孵蛋查询渲染失败: {e}")
        return _summary_text(zj=zj, zl=zl, items=items), None
