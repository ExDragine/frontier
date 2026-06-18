"""远行商人（NRC Merchant）实时商品查询工具。

API 数据 → Jinja2 模板渲染 HTML → Playwright 截图 → QQ 发送。
"""

import time
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client
from utils.markdown_render import html_to_image

API_URL = "https://roco-eggs.tsuki-world.com/api/merchant/current"
IMAGE_BASE = "https://roco-eggs.tsuki-world.com"
API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://roco-eggs.tsuki-world.com/",
    "Accept": "application/json",
}

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

_RARITY_CN = {
    "legendary": "极品",
    "rare": "稀有",
    "common": "普通",
}

httpx_client = get_http_client("nrc_merchant")

# 提醒推送目标商品名称
ALERT_TARGET_ITEMS = {"国王球", "棱镜球", "炫彩精灵蛋", "祝福项坠", "首领血脉秘药"}


async def fetch_merchant_data() -> dict | None:
    """获取远行商人当前货架数据。失败返回 None。"""
    try:
        resp = await httpx_client.get(API_URL, headers=API_HEADERS)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"NRC 商人 API 请求失败: {e}")
        return None


def _fmt_price(price: int) -> str:
    """价格格式化：纯数字，无格式。"""
    return str(price)


def _fmt_countdown(remain: int) -> str:
    """剩余秒数 → HH:MM:SS。"""
    if remain <= 0:
        return "00:00:00"
    return f"{remain // 3600:02d}:{(remain % 3600) // 60:02d}:{remain % 60:02d}"


def _build_items(items: list[dict]) -> list[dict]:
    """将 API 返回的 items 转为模板所需字段。"""
    result = []
    for item in items:
        rarity = item.get("rarity", "common")
        img = item.get("image", "")
        result.append(
            {
                "name": item.get("name", ""),
                "image_full": IMAGE_BASE + img if (img and not img.startswith("http")) else img,
                "purchase_limit": item.get("purchase_limit", 0),
                "price_fmt": _fmt_price(item.get("price", 0)),
                "rarity": rarity,
                "rarity_cn": _RARITY_CN.get(rarity, "普通"),
            }
        )
    return result


def _render_html(data: dict) -> str:
    """Jinja2 渲染：API 数据 → HTML 片段。"""
    items = _build_items(data.get("items", []))
    now = int(time.time())
    countdown = _fmt_countdown(data.get("next_refresh_ts", now) - now)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("nrc_merchant.html")
    return template.render(
        slot_date=data.get("slot_date", ""),
        round=data.get("round", "?"),
        total_rounds=data.get("total_rounds", "?"),
        countdown=countdown,
        items=items,
        updated_at=data.get("updated_at", ""),
    )


def _load_css() -> str:
    return (TEMPLATES_DIR / "nrc_merchant.css").read_text(encoding="utf-8")


def _summary_text(data: dict) -> str:
    """纯文本摘要，图片渲染失败时的降级输出。"""
    items = data.get("items", [])
    lines = [
        f"远行商人 · {data.get('updated_at', '')} 更新",
        f"当前第{data.get('round', '?')}轮 / 共{data.get('total_rounds', '?')}轮",
    ]
    for item in items:
        name = item.get("name", "?")
        price = _fmt_price(item.get("price", 0))
        rarity = _RARITY_CN.get(item.get("rarity", "common"), "普通")
        limit = item.get("purchase_limit", "?")
        lines.append(f"  [{rarity}] {name} - {price}（限购{limit}）")
    return "\n".join(lines)


@tool(response_format="content_and_artifact")
async def get_nrc_merchant_current() -> tuple[str, UniMessage | None]:
    """获取洛克王国远行商人（NRC Merchant）当前商品货架。

    触发关键词：远行商人、商人、NRC、今天商人卖什么、商人货架、商人商品

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 货架截图)
    """
    data = await fetch_merchant_data()
    if data is None:
        return "获取远行商人数据失败", None

    if not data.get("items"):
        return "远行商人暂无商品数据", None

    try:
        html = _render_html(data)
        css = _load_css()
        image = await html_to_image(html, css=css, width=480)
        summary = _summary_text(data)
        return summary, UniMessage.image(raw=image)
    except Exception as e:
        logger.error(f"NRC 商人渲染失败: {e}")
        return _summary_text(data), None
