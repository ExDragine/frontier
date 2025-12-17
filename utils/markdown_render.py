import html
import os
import re

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from playwright.async_api import async_playwright

browser = None
page = None


async def init_playwright():
    global browser, page
    if browser is None:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1000, "height": 600})

        def _on_console(msg):
            try:
                loc = msg.location
                print(f"[playwright console][{msg.type}] {msg.text} -- {loc}")
            except Exception:
                print(f"[playwright console][{msg.type}] {msg.text}")

        page.on("console", _on_console)

        def _on_page_error(exc):
            print(f"[playwright pageerror] {exc}")

        page.on("pageerror", _on_page_error)


async def markdown_to_text(markdown_text):
    md_html = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"]).render(markdown_text)
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
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
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
    temp_html_path = "./caches/temp_markdown.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    await init_playwright()
    if page:
        await page.goto("about:blank")  # 清空页面
        await page.set_viewport_size({"width": width, "height": 600})
        await page.goto(f"file://{os.path.abspath(temp_html_path)}")

        await page.wait_for_load_state("networkidle")

        try:
            await page.wait_for_function("typeof renderMathInElement !== 'undefined'", timeout=1000)
            await page.wait_for_timeout(1000)
            print("✅ KaTeX 渲染完成")
        except Exception as e:
            print(f"⚠️ KaTeX 渲染可能有问题，继续截图: {e}")
            await page.wait_for_timeout(1000)

        try:
            await page.wait_for_function(
                "typeof mermaid !== 'undefined' && document.querySelectorAll('svg').length > 0", timeout=1000
            )
            await page.wait_for_timeout(500)
            print("✅ Mermaid 渲染完成")
        except Exception as e:
            print(f"⚠️ Mermaid 渲染可能有问题，继续截图: {e}")
            await page.wait_for_timeout(500)

        try:
            await page.wait_for_function("window.codeHighlightComplete === true", timeout=1000)
            await page.wait_for_timeout(200)
            print("✅ 代码高亮（Prism）完成")
        except Exception as e:
            # 若超时或页面未设置标志，继续截图但记录警告
            print(f"⚠️ 代码高亮可能未完成或未启用: {e}")
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
            # 截图
            img = await target_element.screenshot(type="png")
        else:
            img = await page.screenshot(full_page=True, type="png")

        try:
            os.remove(temp_html_path)
        except Exception as e:
            print(f"⚠️ 删除临时文件失败: {e}")

        return img
    else:
        return None
