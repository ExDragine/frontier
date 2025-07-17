import html
import os
import re

from markdown_it import MarkdownIt
from playwright.async_api import async_playwright

browser = None
page = None


async def init_playwright():
    global browser, page
    if browser is None:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 800, "height": 600})


def preprocess_math(text):
    """预处理数学公式，确保LaTeX语法正确"""
    # 处理常见的LaTeX转义问题
    text = text.replace("\\lambda", "\\lambda")
    text = text.replace("\\Lambda", "\\Lambda")
    text = text.replace("\\partial", "\\partial")
    text = text.replace("\\frac", "\\frac")
    text = text.replace("\\sqrt", "\\sqrt")
    text = text.replace("\\quad", "\\quad")
    text = text.replace("\\qquad", "\\qquad")
    text = text.replace("\\Rightarrow", "\\Rightarrow")
    text = text.replace("\\neq", "\\neq")
    text = text.replace("\\nabla", "\\nabla")
    text = text.replace("\\ldots", "\\ldots")

    return text


def process_math_in_markdown(text):
    """处理Markdown中的数学公式，将其转换为HTML"""

    # 先处理块级数学公式 $$...$$
    def replace_display_math(match):
        math_content = match.group(1).strip()
        return f'<div class="math-display">$${math_content}$$</div>'

    # 处理块级公式
    text = re.sub(r"\$\$\s*\n?(.*?)\n?\s*\$\$", replace_display_math, text, flags=re.DOTALL)

    # 处理行内数学公式 $...$
    def replace_inline_math(match):
        math_content = match.group(1).strip()
        return f'<span class="math-inline">${math_content}$</span>'

    # 处理行内公式（避免与块级公式冲突）
    text = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)", replace_inline_math, text)

    return text


async def markdown_to_image(markdown_text, width=1280, css=None):
    """
    将 Markdown 文本渲染为图片

    参数:
        markdown_text: Markdown 文本内容
        width: 输出图片宽度
        css: 自定义 CSS 样式
    """
    # 预处理数学公式
    markdown_text = preprocess_math(markdown_text)

    # 处理数学公式
    markdown_text = process_math_in_markdown(markdown_text)

    # 使用 markdown-it-py 将 Markdown 转换为 HTML（不使用数学插件）
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])

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

    full_html = template_html.format(style_block=style_block, html_content=html_content)

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
    """后处理HTML中的数学公式标记"""
    # 确保数学公式被正确标记
    # 处理行内数学公式
    html_content = re.sub(r'<span class="math inline">\$([^$]+)\$</span>', r"$\1$", html_content)

    # 处理块级数学公式
    html_content = re.sub(r'<div class="math display">\$\$([^$]+)\$\$</div>', r"$$\1$$", html_content)

    return html_content
