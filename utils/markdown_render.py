import html
import logging
import os
import re
import secrets
from asyncio import Lock

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

_browser = None
_browser_lock = Lock()


async def _get_browser():
    """返回持久化浏览器实例（延迟初始化，线程安全）。"""
    global _browser
    async with _browser_lock:
        if _browser is None:
            playwright = await async_playwright().start()
            _browser = await playwright.chromium.launch(headless=True)
            logger.info("Playwright 浏览器已初始化")
        return _browser


async def close_playwright():
    """清理全局浏览器实例（关闭时调用）。"""
    global _browser
    async with _browser_lock:
        if _browser:
            await _browser.close()
            _browser = None
            logger.info("Playwright 浏览器已关闭")


def _on_console(msg):
    try:
        loc = msg.location
        logger.debug("[playwright console][%s] %s -- %s", msg.type, msg.text, loc)
    except Exception:
        logger.debug("[playwright console][%s] %s", msg.type, msg.text)


def _on_page_error(exc):
    logger.warning("[playwright pageerror] %s", exc)


async def markdown_to_text(markdown_text):
    md_html = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"]).render(markdown_text)
    plain_text = BeautifulSoup(md_html, "html.parser").get_text()
    return plain_text


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
        return f'<div class="mermaid">{code_content}</div>'

    html_content = re.sub(
        r"<pre><code class=\"language-mermaid\">(.*?)</code></pre>",
        replace_mermaid,
        html_content,
        flags=re.DOTALL,
    )

    if css is None:
        css_abs_path = os.path.abspath("./templates/markdown_render.css")
        style_block = f'<link rel="stylesheet" href="file://{css_abs_path}">'  # 绝对路径
    else:
        style_block = f"<style>{css}</style>"

    template_path = "./templates/markdown_render.html"
    with open(template_path, encoding="utf-8") as f:
        template_html = f.read()

    full_html = template_html.replace("{style_block}", style_block).replace("{html_content}", html_content)
    temp_html_path = f"./cache/{secrets.token_hex(16)}.html"
    with open(temp_html_path, mode="w", encoding="utf-8") as f:
        f.write(full_html)

    browser = await _get_browser()
    # 每次渲染使用独立 page，避免竞态
    page = await browser.new_page(viewport={"width": width, "height": 600})
    page.on("console", _on_console)
    page.on("pageerror", _on_page_error)

    try:
        await page.goto(f"file://{os.path.abspath(temp_html_path)}")
        await page.wait_for_load_state("networkidle")

        try:
            await page.wait_for_function("typeof renderMathInElement !== 'undefined'", timeout=1000)
            await page.wait_for_timeout(1000)
            logger.debug("KaTeX rendering complete")
        except Exception as e:
            logger.warning("KaTeX may have issues, continuing screenshot: %s", e)
            await page.wait_for_timeout(1000)

        try:
            await page.wait_for_function(
                "typeof mermaid !== 'undefined' && document.querySelectorAll('svg').length > 0", timeout=1000
            )
            await page.wait_for_timeout(500)
            logger.debug("Mermaid rendering complete")
        except Exception as e:
            logger.warning("Mermaid may have issues, continuing screenshot: %s", e)
            await page.wait_for_timeout(500)

        try:
            await page.wait_for_function("window.codeHighlightComplete === true", timeout=1000)
            await page.wait_for_timeout(200)
            logger.debug("Prism highlighting complete")
        except Exception as e:
            logger.warning("Prism highlighting may have issues: %s", e)
            await page.wait_for_timeout(200)

        height = await page.evaluate("""
            Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            )
        """)

        await page.set_viewport_size({"width": width, "height": max(int(height), 100)})
        await page.wait_for_timeout(500)
        target_element = await page.wait_for_selector("#markdown-content")
        if target_element:
            img = await target_element.screenshot(type="png")
        else:
            img = await page.screenshot(full_page=True, type="png")

        return img
    finally:
        close_page = getattr(page, "close", None)
        if close_page is not None:
            await close_page()
        try:
            os.remove(temp_html_path)
        except Exception as e:
            logger.warning("Failed to delete temp file: %s", e)


async def html_to_image(html: str, css: str | None = None, width: int = 1000, selector: str = "#render-content"):
    """将 HTML 渲染为图片，复用持久化浏览器实例。"""
    import secrets

    trigger_mark = secrets.token_hex(16)
    cache_file = f"{os.getcwd()}/cache/{trigger_mark}.html"
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

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": width, "height": 600})
    try:
        await page.goto(f"file://{cache_file}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(500)
        height = await page.evaluate("""
            Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            )
        """)
        await page.set_viewport_size({"width": width, "height": max(int(height), 100)})
        target = await page.query_selector(selector)
        image = await target.screenshot(type="png") if target else await page.screenshot(full_page=True, type="png")
    finally:
        close_page = getattr(page, "close", None)
        if close_page is not None:
            await close_page()
    os.remove(cache_file)
    return image


async def playwright_render(name: str, packed_args: dict):
    """使用 Playwright + Jinja2 模板渲染指定类型的内容为图片。"""
    import re
    import secrets

    from jinja2 import Environment, FileSystemLoader

    trigger_mark = secrets.token_hex(16)
    cache_file = f"{os.getcwd()}/cache/{trigger_mark}.html"
    env = Environment(loader=FileSystemLoader("./templates/"), autoescape=True)

    match name:
        case "eq_usgs" | "eq_cenc":
            template = env.get_template("earthquake.html")
            depth = packed_args.get("depth")
            if isinstance(depth, str):
                pattern = re.compile(r"[\d.]+")
                result = pattern.search(depth)
                if result:
                    depth = float(result.group(0))
                else:
                    depth = 10.0
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

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(f"file://{cache_file}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)
        bytes_picture = None
        element_handle = await page.query_selector("id=card")
        if element_handle is not None:
            bytes_picture = await element_handle.screenshot()
    finally:
        close_page = getattr(page, "close", None)
        if close_page is not None:
            await close_page()
    os.remove(cache_file)
    if bytes_picture:
        return bytes_picture
