import html
import logging
import re
import secrets
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

from utils import browser_runtime
from utils.markdown_rich import render_rich_markdown_blocks

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CACHE_DIR = PROJECT_ROOT / "cache"

_REMOTE_URL_RE = re.compile(r"^(?:https?|wss?)://", re.IGNORECASE)
# 量取页面实际高度；markdown/html 两个渲染入口共用。
_PAGE_HEIGHT_JS = """
    Math.max(
        document.body.scrollHeight,
        document.body.offsetHeight,
        document.documentElement.clientHeight,
        document.documentElement.scrollHeight,
        document.documentElement.offsetHeight
    )
"""


async def _get_browser():
    """返回共享浏览器实例（延迟初始化，探活失败时自动重启）。"""
    return await browser_runtime.get_browser()


def _on_console(msg):
    try:
        loc = msg.location
        logger.debug("[playwright console][%s] %s -- %s", msg.type, msg.text, loc)
    except Exception:
        logger.debug("[playwright console][%s] %s", msg.type, msg.text)


def _on_page_error(exc):
    logger.warning("[playwright pageerror] %s", exc)


def _attach_page_logging(page) -> None:
    page.on("console", _on_console)
    page.on("pageerror", _on_page_error)


async def _abort_route(route) -> None:
    await route.abort()


async def _resize_page_to_content(page, width: int | None) -> None:
    """按页面实际内容高度重设视口。"""
    if not width:
        return
    height = await page.evaluate(_PAGE_HEIGHT_JS)
    await page.set_viewport_size({"width": width, "height": max(int(height), 100)})


async def _capture_target(
    page,
    *,
    selector: str | None,
    wait_for_target: bool,
    fallback_full_page: bool,
) -> bytes | None:
    """截取目标元素；元素不存在时按调用方约定回退整页或返回 None。"""
    target = None
    if selector:
        target = await page.wait_for_selector(selector) if wait_for_target else await page.query_selector(selector)
    if target is not None:
        return await target.screenshot(type="png")
    if fallback_full_page:
        return await page.screenshot(full_page=True, type="png")
    return None


async def _close_page(page) -> None:
    if page is None:
        return
    close_page = getattr(page, "close", None)
    if close_page is not None:
        await close_page()


def _remove_temp_file(path: Path) -> None:
    try:
        path.unlink()
    except Exception as e:
        logger.warning("Failed to delete temp file: %s", e)


async def markdown_to_text(markdown_text):
    md_html = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"]).render(markdown_text)
    document = BeautifulSoup(md_html, "html.parser")
    for link in document.find_all("a", href=True):
        label = link.get_text()
        url = str(link["href"])
        link.replace_with(label if label == url else f"{label}（{url}）")
    return document.get_text()


def _markdown_asset_paths() -> tuple[Path, Path]:
    asset_dir = TEMPLATES_DIR / "markdown_assets"
    asset_style_path = asset_dir / "markdown-render.css"
    asset_script_path = asset_dir / "markdown-render.js"
    for asset_path in (asset_style_path, asset_script_path):
        if not asset_path.is_file():
            raise FileNotFoundError("Markdown renderer assets are missing; run `npm run build --prefix renderer`")
    return asset_style_path, asset_script_path


async def _render_png(
    full_html: str,
    *,
    cache_dir: Path | None = None,
    selector: str | None = None,
    width: int | None = None,
    viewport_height: int = 600,
    wait_ms: int = 500,
    resize_to_content: bool = True,
    block_remote: bool = False,
    wait_for_target: bool = False,
    fallback_full_page: bool = True,
    page_setup: Callable[[Any], None] | None = None,
    after_load: Callable[[Any], Awaitable[None]] | None = None,
) -> bytes | None:
    """三个渲染入口共用的私有内核：临时文件 → 开页 → 截图 → 清理。

    调用方只负责拼出自己的 HTML，以及在下面这些可观察差异上做选择：

    - ``selector`` / ``wait_for_target`` / ``fallback_full_page``：截哪个元素，找不到时是否回退整页。
    - ``width`` / ``viewport_height`` / ``resize_to_content``：初始视口，以及是否按内容高度重设视口。
    - ``wait_ms``：``networkidle`` 之后的额外等待（markdown/html 为 500ms，Jinja 模板为 3000ms）。
    - ``block_remote`` / ``page_setup`` / ``after_load``：是否拦截远端请求、挂页面日志、等待渲染器就绪。
    """
    temp_dir = cache_dir or CACHE_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_html_path = temp_dir / f"{secrets.token_hex(16)}.html"
    temp_html_path.write_text(full_html, encoding="utf-8")

    page_kwargs = {"viewport": {"width": width, "height": viewport_height}} if width else {}
    browser = await _get_browser()
    page = None
    try:
        # 每次渲染使用独立 page，避免竞态
        page = await browser.new_page(**page_kwargs)
        if page_setup is not None:
            page_setup(page)
        if block_remote:
            route = getattr(page, "route", None)
            if route is not None:
                await route(_REMOTE_URL_RE, _abort_route)

        await page.goto(temp_html_path.resolve().as_uri())
        await page.wait_for_load_state("networkidle")
        if after_load is not None:
            await after_load(page)
        if wait_ms:
            await page.wait_for_timeout(wait_ms)
        if resize_to_content:
            await _resize_page_to_content(page, width)

        return await _capture_target(
            page,
            selector=selector,
            wait_for_target=wait_for_target,
            fallback_full_page=fallback_full_page,
        )
    finally:
        await _close_page(page)
        _remove_temp_file(temp_html_path)


async def _wait_for_renderer_ready(page) -> None:
    """等待本地 Markdown 渲染器完成（Mermaid/ECharts/KaTeX 等按需渲染）。"""
    try:
        await page.wait_for_selector(
            "html[data-frontier-ready='true']",
            state="attached",
            timeout=10_000,
        )
        render_errors = await page.evaluate("window.__FRONTIER_RENDER__?.errors ?? []")
    except Exception as e:
        raise RuntimeError("Markdown local renderer did not become ready") from e
    if render_errors:
        logger.warning("Markdown 部分内容已降级渲染: %s", render_errors)
    else:
        logger.debug("Markdown local rendering complete")


async def markdown_to_image(markdown_text, width=1000, css=None):
    """
    将 Markdown 文本渲染为图片

    参数:
        markdown_text: Markdown 文本内容
        width: 输出图片宽度
        css: 自定义 CSS 样式
    """
    md = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    html_content = md.render(markdown_text)

    def replace_mermaid(match):
        code_content = html.unescape(match.group(1))  # 反转义 HTML 实体
        return f'<div class="mermaid">{html.escape(code_content)}</div>'

    html_content = re.sub(
        r"<pre><code class=\"language-mermaid\">(.*?)</code></pre>",
        replace_mermaid,
        html_content,
        flags=re.DOTALL,
    )
    html_content = render_rich_markdown_blocks(html_content)

    if css is None:
        style_block = f'<link rel="stylesheet" href="{(TEMPLATES_DIR / "markdown_render.css").as_uri()}">'
    else:
        style_block = f"<style>{css}</style>"

    with (TEMPLATES_DIR / "markdown_render.html").open(encoding="utf-8") as f:
        template_html = f.read()

    asset_style_path, asset_script_path = _markdown_asset_paths()
    full_html = (
        template_html.replace("{style_block}", style_block)
        .replace("{asset_style_url}", asset_style_path.as_uri())
        .replace("{asset_script_url}", asset_script_path.as_uri())
        .replace("{html_content}", html_content)
    )

    return await _render_png(
        full_html,
        selector="#markdown-content",
        width=width,
        block_remote=True,
        wait_for_target=True,
        page_setup=_attach_page_logging,
        after_load=_wait_for_renderer_ready,
    )


async def html_to_image(html: str, css: str | None = None, width: int = 1000, selector: str = "#render-content"):
    """将 HTML 渲染为图片，复用持久化浏览器实例。"""
    style_block = f"<style>{css}</style>" if css else ""
    rendered_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {style_block}
</head>
<body>
    <div class="markdown-body" id="render-content">
        {html}
    </div>
</body>
</html>
"""
    return await _render_png(
        rendered_html,
        cache_dir=Path.cwd() / "cache",
        selector=selector,
        width=width,
    )


async def playwright_render(name: str, packed_args: dict):
    """使用 Playwright + Jinja2 模板渲染指定类型的内容为图片。"""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader("./templates/"), autoescape=True)

    match name:
        case "eq_usgs" | "eq_cenc":
            template = env.get_template("earthquake.html")
            depth = packed_args.get("depth")
            if isinstance(depth, str):
                pattern = re.compile(r"[\d.]+")
                result = pattern.search(depth)
                depth = float(result.group(0)) if result else 10.0
            elif depth is not None:
                depth = float(depth)
            else:
                depth = 10.0

            rendered_html = template.render(
                title=packed_args["title"],
                detail=packed_args["detail"],
                latitude=float(packed_args["latitude"]),
                longitude=float(packed_args["longitude"]),
                magnitude=float(packed_args["magnitude"]),
                depth=depth,
            )
        case _:
            return None

    return await _render_png(
        rendered_html,
        cache_dir=Path.cwd() / "cache",
        selector="id=card",
        wait_ms=3000,
        resize_to_content=False,
        fallback_full_page=False,
    )
