"""NRC（洛克王国）工具与台风工具共享的常量、模板渲染与蛋组解析。

这些模块原先各自复制了同一份浏览器 UA、请求头、模板目录、蛋组表与解析函数；
这里收拢为唯一实现，各模块只保留自己的 API 端点、模板名和渲染上下文。

跨模块契约：``tools/NRCmerchant_current._load_css`` 仍以同名零参薄别名存在，
``plugins/clockwork/task_handlers.py`` 依赖该名字，不能删除或改签名。
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# 各站点共用的浏览器 UA（4 个 NRC 模块与 typhoon 原为 5 份逐字副本）。
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

API_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}

# 图片下载专用头，不设 Accept 避免 CDN 返回 406
IMG_HEADERS = {
    "User-Agent": USER_AGENT,
}

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

DANZU_GROUPS = {
    1: "巨灵组",
    2: "两栖组",
    3: "昆虫组",
    4: "天空组",
    5: "动物组",
    6: "妖精组",
    7: "植物组",
    8: "拟人组",
    9: "软体组",
    10: "大地组",
    11: "魔力组",
    12: "海洋组",
    13: "龙组",
    14: "机械组",
}

DANZU_COLORS = {
    1: "#607D8B",
    2: "#2196F3",
    3: "#8BC34A",
    4: "#00BCD4",
    5: "#FF9800",
    6: "#E91E63",
    7: "#4CAF50",
    8: "#9C27B0",
    9: "#FF5722",
    10: "#795548",
    11: "#3F51B5",
    12: "#03A9F4",
    13: "#F44336",
    14: "#607D8B",
}


def load_css(filename: str) -> str:
    """读取 templates/ 下的 CSS 文件。"""
    return (TEMPLATES_DIR / filename).read_text(encoding="utf-8")


def render_template(name: str, **context) -> str:
    """用 templates/ 下的 Jinja2 模板渲染 HTML 片段。"""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    return env.get_template(name).render(**context)


def parse_danzu_ids(danzu_raw) -> list[int]:
    """解析蛋组编号（可能逗号分隔）为整数列表，保持原始顺序、不去重。"""
    if not danzu_raw:
        return []
    return [int(x.strip()) for x in str(danzu_raw).split(",") if x.strip().isdigit()]


def parse_danzu_id_set(danzu_raw) -> set[int]:
    """解析蛋组编号为整数集合（去重），供蛋组兼容性判断使用。"""
    return set(parse_danzu_ids(danzu_raw))


def parse_danzu_names(danzu_raw, *, unique_sorted: bool = False) -> str:
    """蛋组编号 → 中文名称，多个用斜杠连接。

    ``unique_sorted=True`` 时先按编号升序去重（原 ``NRCeggs_groups`` 行为），
    否则保持输入顺序（原 ``NRCeggs_details`` 行为）。
    """
    ids = sorted(parse_danzu_id_set(danzu_raw)) if unique_sorted else parse_danzu_ids(danzu_raw)
    names = [DANZU_GROUPS.get(i, f"组{i}") for i in ids]
    return " / ".join(names) if names else "未知"


def get_danzu_color(danzu_raw, *, unique_sorted: bool = False) -> str:
    """返回第一个蛋组对应的颜色。

    ``unique_sorted=True`` 时先按编号升序去重（原 ``NRCeggs_groups`` 行为），
    否则取输入顺序上的第一个（原 ``NRCeggs_details`` 行为）。
    """
    ids = sorted(parse_danzu_id_set(danzu_raw)) if unique_sorted else parse_danzu_ids(danzu_raw)
    return DANZU_COLORS.get(ids[0], "#9E9E9E") if ids else "#9E9E9E"
