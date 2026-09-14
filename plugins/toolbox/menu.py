"""Toolbox menu commands and supporting logic."""

from pathlib import Path

from nonebot import logger, on_command
from nonebot.adapters.milky.event import MessageEvent

from utils.alconna import UniMessage
from utils.markdown_render import html_to_image

vehelp_cmd = on_command("vehelp", priority=2, block=True, aliases={"专业模式", "vep菜单"})


_vep_menu_cache: bytes | None = None


_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


async def _get_vep_menu() -> bytes:
    """返回 vep 参数菜单截图（首次渲染后缓存）。"""
    global _vep_menu_cache
    if _vep_menu_cache is not None:
        return _vep_menu_cache
    html = (_TEMPLATES_DIR / "vep_menu.html").read_text(encoding="utf-8")
    css_path = _TEMPLATES_DIR / "vep_menu.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else None
    image = await html_to_image(html, css=css, width=480)
    _vep_menu_cache = image
    logger.info("vep 菜单已渲染并缓存")
    return image


@vehelp_cmd.handle()
async def handle_vehelp(event: MessageEvent):
    """返回 vep 专业模式参数菜单截图（首次渲染后缓存）。"""
    try:
        image = await _get_vep_menu()
        await UniMessage.text("ve专业模式参数菜单：").send()
        await UniMessage.image(raw=image).send()
    except Exception as e:
        logger.error(f"vehelp 菜单渲染失败: {e}")
        await UniMessage.text(f"菜单加载失败: {e}").send()

