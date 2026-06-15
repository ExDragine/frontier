"""洛克王国精灵蛋组查询工具。

根据精灵名称查询蛋组信息，判断两只精灵能否孵蛋，或查找同蛋组的配偶精灵。
API 数据 → Jinja2 模板渲染 HTML → Playwright 截图 → QQ 发送。
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from langchain_core.tools import tool
from nonebot import logger

from utils.alconna import UniMessage
from utils.http_client import get_http_client
from utils.markdown_render import html_to_image

API1_URL = "https://ap.xiaopidd.com/api.AppletXCX/getXcxjltujianListByName"
API2_URL = "https://ap.xiaopidd.com/api.AppletXCX/getXcxjltujianListByDanzu"

API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

DANZU_GROUPS = {
    1: "巨灵组", 2: "两栖组", 3: "昆虫组", 4: "天空组",
    5: "动物组", 6: "妖精组", 7: "植物组", 8: "拟人组",
    9: "软体组", 10: "大地组", 11: "魔力组", 12: "海洋组",
    13: "龙组", 14: "机械组",
}

DANZU_COLORS = {
    1: "#607D8B", 2: "#2196F3", 3: "#8BC34A", 4: "#00BCD4",
    5: "#FF9800", 6: "#E91E63", 7: "#4CAF50", 8: "#9C27B0",
    9: "#FF5722", 10: "#795548", 11: "#3F51B5", 12: "#03A9F4",
    13: "#F44336", 14: "#607D8B",
}

httpx_client = get_http_client("nrc_eggs_groups")


async def _fetch_pet_by_name(name: str) -> dict | None:
    """通过名称查询单个精灵信息，返回 API 返回的第一条记录。"""
    try:
        resp = await httpx_client.get(
            API1_URL, params={"name": name}, headers=API_HEADERS
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("code") == 0:
            inner = payload.get("data", {})
            items = inner.get("data", []) if isinstance(inner, dict) else []
            if isinstance(items, list) and len(items) > 0:
                return items[0]
        return None
    except Exception as e:
        logger.error(f"精灵名称查询失败 [{name}]: {e}")
        return None


async def _fetch_pets_by_danzu(danzu: str) -> list[dict]:
    """通过蛋组编号查询该蛋组下所有精灵。"""
    try:
        resp = await httpx_client.get(
            API2_URL, params={"danzu": danzu}, headers=API_HEADERS
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("code") == 0:
            inner = payload.get("data", {})
            items = inner.get("data", []) if isinstance(inner, dict) else []
            return items if isinstance(items, list) else []
        return []
    except Exception as e:
        logger.error(f"蛋组查询失败 [danzu={danzu}]: {e}")
        return []


def _parse_danzu_ids(danzu_raw) -> set[int]:
    """解析蛋组编号字符串为整数集合，支持逗号分隔的多蛋组。"""
    if not danzu_raw:
        return set()
    raw = str(danzu_raw)
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def _parse_danzu_names(danzu_raw) -> str:
    """蛋组编号 → 中文名称，多个用斜杠连接。"""
    ids = _parse_danzu_ids(danzu_raw)
    names = [DANZU_GROUPS.get(i, f"组{i}") for i in sorted(ids)]
    return " / ".join(names) if names else "未知"


def _get_danzu_color(danzu_raw) -> str:
    """获取第一个蛋组对应的颜色标识。"""
    ids = sorted(_parse_danzu_ids(danzu_raw))
    return DANZU_COLORS.get(ids[0], "#9E9E9E") if ids else "#9E9E9E"


def _check_compatible(danzu1: str, danzu2: str) -> bool:
    """判断两个蛋组集合是否有交集。"""
    return bool(_parse_danzu_ids(danzu1) & _parse_danzu_ids(danzu2))


def _find_common_groups(danzu1: str, danzu2: str) -> list[int]:
    """找出两个精灵共有的蛋组编号。"""
    ids1 = _parse_danzu_ids(danzu1)
    ids2 = _parse_danzu_ids(danzu2)
    return sorted(ids1 & ids2)


def _split_name(name: str) -> tuple[str, str]:
    """将精灵名称拆分为正式名称和括号备注。"""
    for left, right in (("（", "）"), ("(", ")")):
        idx = name.find(left)
        if idx != -1 and name.endswith(right):
            return name[:idx], name[idx:]
    return name, ""


def _build_pet_card(pet: dict) -> dict:
    """将 API 返回的精灵数据转为模板所需字段。"""
    pic_file = pet.get("pic_file", {}) or {}
    path = pic_file.get("path", "") if isinstance(pic_file, dict) else ""
    name_main, name_note = _split_name(pet.get("name", "?"))
    return {
        "name": pet.get("name", "?"),
        "name_main": name_main,
        "name_note": name_note,
        "image_url": path or "",
        "danzu_display": _parse_danzu_names(pet.get("danzu", "")),
        "danzu_color": _get_danzu_color(pet.get("danzu", "")),
        "isfudan": pet.get("isfudan", 2),
        "can_breed": pet.get("isfudan") == 1,
    }


def _render_html(mode: str, **context) -> str:
    """Jinja2 渲染：数据 → HTML 片段。"""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("nrc_eggs_groups.html")
    return template.render(mode=mode, **context)


def _load_css() -> str:
    return (TEMPLATES_DIR / "nrc_eggs_groups.css").read_text(encoding="utf-8")


# ── Tool ──────────────────────────────────────────────────────────────────


@tool(response_format="content_and_artifact")
async def get_nrc_eggs_groups(action: str, name1: str, name2: str = "") -> tuple[str, UniMessage | None]:
    """查询洛克王国精灵蛋组信息，判断孵蛋兼容性或查找同蛋组配偶。

    支持两种模式：
    1. compare 模式 — 比较两只精灵能否孵蛋（如：恶魔叮和加油蟹能不能孵蛋）
    2. find_matches 模式 — 查找可与该精灵孵蛋的所有可当配偶孵蛋的精灵

    Args:
        action: "compare" 或 "find_matches"
        name1: 精灵名称（compare 时为第一只，find_matches 时为查询目标）
        name2: 第二只精灵名称（仅 compare 模式需要）

    Returns:
        tuple[str, UniMessage | None]: (文字摘要, 蛋组查询结果截图)
    """
    if action == "compare":
        if not name2:
            return "比较模式需要提供两只精灵的名称，请补充第二只精灵名称", None

        pet1 = await _fetch_pet_by_name(name1)
        pet2 = await _fetch_pet_by_name(name2)

        if pet1 is None:
            return f"未找到精灵「{name1}」，请检查名称是否正确", None
        if pet2 is None:
            return f"未找到精灵「{name2}」，请检查名称是否正确", None

        breedable1 = pet1.get("isfudan") == 1
        breedable2 = pet2.get("isfudan") == 1

        card1 = _build_pet_card(pet1)
        card2 = _build_pet_card(pet2)

        # 判断结果类型
        if not breedable1 and not breedable2:
            result_type = "cannot_breed"
            cannot_breed_pets = [
                {"name": name1, "name_main": card1["name_main"], "name_note": card1["name_note"]},
                {"name": name2, "name_main": card2["name_main"], "name_note": card2["name_note"]},
            ]
            result_text = f"「{name1}」和「{name2}」均不能孵蛋！\n传说团本精灵、战令精灵等特殊精灵无法繁殖后代。"
        elif not breedable1:
            result_type = "cannot_breed"
            cannot_breed_pets = [
                {"name": name1, "name_main": card1["name_main"], "name_note": card1["name_note"]},
            ]
            result_text = f"「{name1}」不能孵蛋！\n传说团本精灵、战令精灵等特殊精灵无法繁殖后代。"
        elif not breedable2:
            result_type = "cannot_breed"
            cannot_breed_pets = [
                {"name": name2, "name_main": card2["name_main"], "name_note": card2["name_note"]},
            ]
            result_text = f"「{name2}」不能孵蛋！\n传说团本精灵、战令精灵等特殊精灵无法繁殖后代。"
        elif _check_compatible(pet1.get("danzu", ""), pet2.get("danzu", "")):
            result_type = "success"
            cannot_breed_pets = []
            result_text = f"{name1}和{name2}可以在一起孵蛋！"
        else:
            result_type = "danzu_mismatch"
            cannot_breed_pets = []
            result_text = f"{name1}和{name2}不能在一起孵蛋，因为蛋组不同。"

        context = {
            "pet1": card1,
            "pet2": card2,
            "result_type": result_type,
            "cannot_breed_pets": cannot_breed_pets,
        }

        try:
            html = _render_html("compare", **context)
            css = _load_css()
            image = await html_to_image(html, css=css, width=480)
            return result_text, UniMessage.image(raw=image)
        except Exception as e:
            logger.error(f"蛋组对比渲染失败: {e}")
            return result_text, None

    elif action == "find_matches":
        pet = await _fetch_pet_by_name(name1)
        if pet is None:
            return f"未找到精灵「{name1}」，请检查名称是否正确", None

        danzu_raw = pet.get("danzu", "")
        danzu_ids = _parse_danzu_ids(danzu_raw)

        if not danzu_ids:
            return f"精灵「{name1}」没有蛋组信息", None

        seen_names = {pet.get("name", "")}
        all_matches: list[dict] = []
        for dz_id in sorted(danzu_ids):
            pets = await _fetch_pets_by_danzu(str(dz_id))
            for p in pets:
                pname = p.get("name", "")
                if pname not in seen_names:
                    seen_names.add(pname)
                    all_matches.append(p)

        # 排序：可孵蛋的在前，同按名称排列
        all_matches.sort(key=lambda x: (0 if x.get("isfudan") == 1 else 1, x.get("name", "")))

        current_pet = _build_pet_card(pet)
        match_cards = [_build_pet_card(p) for p in all_matches[:60]]

        can_breed_count = sum(1 for m in all_matches if m.get("isfudan") == 1)
        cannot_breed_count = len(all_matches) - can_breed_count

        result_text = (
            f"「{name1}」蛋组：{current_pet['danzu_display']}，"
            f"共找到 {len(all_matches)} 只可当配偶孵蛋的精灵（{can_breed_count} 只可孵蛋，{cannot_breed_count} 只不可孵蛋）"
        )

        context = {
            "current_pet": current_pet,
            "matches": match_cards,
            "total_count": len(all_matches),
        }

        try:
            html = _render_html("find_matches", **context)
            css = _load_css()
            image = await html_to_image(html, css=css, width=480)
            return result_text, UniMessage.image(raw=image)
        except Exception as e:
            logger.error(f"蛋组配偶查询渲染失败: {e}")
            return result_text, None

    else:
        return f"不支持的操作类型：{action}，请使用 compare（比较两只精灵）或 find_matches（查找可当配偶孵蛋的精灵）", None
