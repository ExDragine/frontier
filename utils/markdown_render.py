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
        await page.close()
        try:
            os.remove(temp_html_path)
        except Exception as e:
            logger.warning("Failed to delete temp file: %s", e)
