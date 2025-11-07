import html
import os
import re

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from mdit_py_plugins.texmath import texmath_plugin  # 使用 mdit-py-plugins 提供的 math 插件
from playwright.async_api import async_playwright

browser = None
page = None


async def init_playwright():
    global browser, page
    if browser is None:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1000, "height": 600})

        # 收集并打印浏览器端 console 日志，便于调试 KaTeX/Prism/Mermaid 等前端渲染问题
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


# NOTE: 已移除旧的数学预处理逻辑，统一使用 mdit-py-plugins 的 math_plugin 来处理


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
    # 使用 mdit-py-plugins 的 math 插件处理数学公式（假设已安装）
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"]).use(texmath_plugin)
    html_content = md.render(markdown_text)

    # 处理 Mermaid 图表代码块，将其转换为可由 Mermaid.js 渲染的 <div class="mermaid"> 元素
    def replace_mermaid(match):
        code_content = html.unescape(match.group(1))  # 反转义 HTML 实体
        return f'<div class="mermaid">{code_content}</div>'

    html_content = re.sub(
        r"<pre><code class=\"language-mermaid\">(.*?)</code></pre>",
        replace_mermaid,
        html_content,
        flags=re.DOTALL,
    )

    # 选择样式：如未指定自定义css，则引用外部css文件（用绝对路径，确保本地加载）
    if css is None:
        css_abs_path = os.path.abspath("./resources/markdown_render.css")
        style_block = f'<link rel="stylesheet" href="file://{css_abs_path}">'  # 绝对路径
    else:
        style_block = f"<style>{css}</style>"

    # 读取 HTML 模板
    template_path = "./resources/markdown_render.html"
    with open(template_path, encoding="utf-8") as f:
        template_html = f.read()

    # Use simple replace instead of str.format to avoid issues with
    # literal `{` `}` in the HTML/JS template (which would be interpreted
    # by str.format and cause ValueError: unexpected '{' in field name).
    full_html = template_html.replace("{style_block}", style_block).replace("{html_content}", html_content)

    # 创建临时 HTML 文件
    temp_html_path = "./cache/temp_markdown.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # 使用 Playwright 将 HTML 渲染为图片
    await init_playwright()
    if page:
        await page.goto("about:blank")  # 清空页面
        await page.set_viewport_size({"width": width, "height": 600})
        await page.goto(f"file://{os.path.abspath(temp_html_path)}")

        # 等待页面加载完成
        await page.wait_for_load_state("networkidle")

        # 等待 KaTeX 渲染完成
        try:
            # 等待KaTeX库加载
            await page.wait_for_function("typeof renderMathInElement !== 'undefined'", timeout=1000)
            # 等待一段时间让渲染完成
            await page.wait_for_timeout(1000)
            print("✅ KaTeX 渲染完成")
        except Exception as e:
            print(f"⚠️ KaTeX 渲染可能有问题，继续截图: {e}")
            await page.wait_for_timeout(1000)

        # 等待 Mermaid 渲染完成
        try:
            await page.wait_for_function(
                "typeof mermaid !== 'undefined' && document.querySelectorAll('svg').length > 0", timeout=1000
            )
            await page.wait_for_timeout(500)
            print("✅ Mermaid 渲染完成")
        except Exception as e:
            print(f"⚠️ Mermaid 渲染可能有问题，继续截图: {e}")
            await page.wait_for_timeout(500)

        # 等待代码高亮（Prism 或其它在模板中设置的标志）渲染完成
        try:
            await page.wait_for_function("window.codeHighlightComplete === true", timeout=1000)
            await page.wait_for_timeout(200)
            print("✅ 代码高亮（Prism）完成")
        except Exception as e:
            # 若超时或页面未设置标志，继续截图但记录警告
            print(f"⚠️ 代码高亮可能未完成或未启用: {e}")
            await page.wait_for_timeout(200)

        # 获取内容高度以设置适当的截图高度
        height = await page.evaluate("""
            Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            )
        """)

        # 调整页面大小以适应内容
        await page.set_viewport_size({"width": width, "height": max(int(height), 100)})

        # 再次等待一下确保布局稳定
        await page.wait_for_timeout(500)
        # 选取id为markdown-content的元素并截图
        target_element = await page.wait_for_selector("#markdown-content")
        if target_element:
            # 截图
            img = await target_element.screenshot(type="png")
        else:
            img = await page.screenshot(full_page=True, type="png")

        # 删除临时文件
        try:
            os.remove(temp_html_path)
        except Exception as e:
            print(f"⚠️ 删除临时文件失败: {e}")

        return img
    else:
        return None


def post_process_math_html(html_content):
    """后处理HTML中的数学公式标记

    保留占位函数以便未来对插件生成的 HTML 做小修正（目前直接返回）。
    """
    return html_content
