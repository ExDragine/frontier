"""远行商人（NRC Merchant）实时商品查询工具。

API 数据 → Jinja2 模板渲染 HTML → Playwright 截图 → QQ 发送。
"""

import datetime as dt
import time
import zoneinfo
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client
from utils.markdown_render import html_to_image

API_URL = "https://roco-eggs.tsuki-world.com/api/merchant/current"
BACKUP_API_URL = "https://rocokingdomworld.org/api/merchant/live"
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
_TZ_SHANGHAI = zoneinfo.ZoneInfo("Asia/Shanghai")

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
    """获取远行商人当前货架数据（主 API）。失败返回 None。"""
    try:
        resp = await httpx_client.get(API_URL, headers=API_HEADERS)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"NRC 商人主 API 请求失败: {e}")
        return None


async def fetch_backup_merchant_data() -> dict | None:
    """获取远行商人当前货架数据（备用 API）。失败返回 None。"""
    try:
        resp = await httpx_client.get(BACKUP_API_URL, headers=API_HEADERS)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"NRC 商人备用 API 请求失败: {e}")
        return None


def _safe_int(value, default=0) -> int:
    """安全转换为整数，失败返回默认值。"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _adapt_backup_data(data: dict) -> dict:
    """将备用 API 返回数据转换为主 API 格式，复用现有渲染管道。"""
    # nextRefreshBeijing 字符串 → unix 时间戳
    next_refresh_str = data.get("nextRefreshBeijing", "")
    next_refresh_ts = int(time.time())
    if next_refresh_str:
        try:
            parsed = dt.datetime.strptime(next_refresh_str, "%Y-%m-%d %H:%M:%S")
            parsed = parsed.replace(tzinfo=_TZ_SHANGHAI)
            next_refresh_ts = int(parsed.timestamp())
        except (ValueError, OSError) as e:
            logger.warning(f"NRC 商人备用 API nextRefreshBeijing 解析失败: {e}")

    # startedAtBeijing 日期部分 → slot_date
    started_at = data.get("startedAtBeijing", "")
    slot_date = started_at[:10] if started_at else ""

    # rounds dict key 数量 → total_rounds
    rounds_dict = data.get("rounds", {})
    total_rounds = len(rounds_dict) if isinstance(rounds_dict, dict) and rounds_dict else 1

    # 适配 items：rarity 统一为 common，用 _rarity_label 储存 category 展示文字
    items = []
    for item in data.get("items", []):
        items.append({
            "name": item.get("name", ""),
            "price": _safe_int(item.get("price", 0)),
            "purchase_limit": _safe_int(item.get("limit", 0)),
            "image": item.get("image", ""),
            "rarity": "common",
            "_rarity_label": item.get("category", ""),
        })

    # fetchedAt ISO 8601 UTC → 北京时间可读字符串
    fetched_at = data.get("fetchedAt", "")
    updated_at = ""
    if fetched_at:
        try:
            # "2026-07-06T10:31:33.660Z" → "2026-07-06 18:31:33"
            dt_obj = dt.datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
            dt_bj = dt_obj.astimezone(_TZ_SHANGHAI)
            updated_at = dt_bj.strftime("%H:%M")
        except (ValueError, OSError) as e:
            logger.warning(f"NRC 商人备用 API fetchedAt 解析失败: {e}")
            updated_at = fetched_at

    return {
        "slot_date": slot_date,
        "round": data.get("round", 1),
        "total_rounds": total_rounds,
        "next_refresh_ts": next_refresh_ts,
        "updated_at": updated_at,
        "items": items,
    }


async def fetch_merchant_data_with_fallback() -> tuple[dict | None, str | None]:
    """获取远行商人货架数据，主 API 无效时自动切备用。

    Returns:
        (data_dict, source) — source 为 "primary" 或 "backup"；两个 API 都无效时返回 (None, None)。
    """
    data = await fetch_merchant_data()
    if data and data.get("items"):
        return data, "primary"

    logger.info("NRC 商人：主 API 数据无效，尝试备用 API")
    backup_data = await fetch_backup_merchant_data()
    if backup_data and backup_data.get("items"):
        adapted = _adapt_backup_data(backup_data)
        logger.info("NRC 商人：备用 API 数据适配成功")
        return adapted, "backup"

    logger.warning("NRC 商人：主、备 API 均无有效商品数据")
    return None, None


def _fmt_price(price: int) -> str:
    """价格格式化：纯数字，无格式。"""
    return str(price)


def _fmt_countdown(remain: int) -> str:
    """剩余秒数 → HH:MM:SS。"""
    if remain <= 0:
        return "00:00:00"
    return f"{remain // 3600:02d}:{(remain % 3600) // 60:02d}:{remain % 60:02d}"


def _build_items(items: list[dict]) -> list[dict]:
    """将 API 返回的 items 转为模板所需字段。

    备用 API 数据已在上层适配，携带 category 字段用于稀有度展示标签，
    rarity 统一为 "common" 以使用灰色样式。
    """
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
                "rarity_cn": item.get("_rarity_label") or _RARITY_CN.get(rarity, "普通"),
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
        rarity_label = item.get("_rarity_label") or _RARITY_CN.get(item.get("rarity", "common"), "普通")
        limit = item.get("purchase_limit", "?")
        lines.append(f"  [{rarity_label}] {name} - {price}（限购{limit}）")
    return "\n".join(lines)


@tool(response_format="content_and_artifact")
async def get_nrc_merchant_current() -> tuple[str, UniMessage | None]:
    """获取洛克王国远行商人（NRC Merchant）当前商品货架。

    触发关键词：远行商人、商人、NRC、今天商人卖什么、商人货架、商人商品

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 货架截图)
    """
    data, _source = await fetch_merchant_data_with_fallback()
    if data is None:
        return "当前远行商人无有效商品数据，请稍后再试", None

    try:
        html = _render_html(data)
        css = _load_css()
        image = await html_to_image(html, css=css, width=480)
        summary = _summary_text(data)
        return summary, UniMessage.image(raw=image)
    except Exception as e:
        logger.error(f"NRC 商人渲染失败: {e}")
        return _summary_text(data), None
