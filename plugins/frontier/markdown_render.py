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


async def markdown_to_image(markdown_text, width=800, css=None):
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

    # 准备完整的 HTML 文档
    default_css = """
    body {
        background: #f4f6fb;
        min-height: 100vh;
        margin: 0;
        padding: 0;
    }
    .markdown-body {
        background: #fff;
        max-width: 820px;
        margin: 0 auto;
        border-radius: 0;
        box-shadow: none;
        padding: 40px 36px 32px 36px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'SimSun', Roboto, Helvetica, Arial, sans-serif;
        color: #23272f;
        font-size: 18px;
        line-height: 1.85;
        word-break: break-word;
        box-sizing: border-box;
    }
    @media (max-width: 600px) {
        .markdown-body {
            padding: 16px 2vw;
            margin: 0;
            border-radius: 0;
            box-shadow: none;
        }
    }
    h1, h2, h3, h4, h5, h6 { 
        margin-top: 2.2em; 
        margin-bottom: 1em; 
        font-weight: 700; 
        line-height: 1.25;
        color: #1a1a1a;
        letter-spacing: 0.01em;
    }
    h1 { font-size: 2.2em; border-bottom: 2px solid #eaecef; padding-bottom: .3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
    h3 { font-size: 1.2em; }
    h4 { font-size: 1em; }
    p { margin-bottom: 1.2em; }
    a { color: #2563eb; text-decoration: none; border-bottom: 1px dotted #b3d3f6; transition: color 0.2s; }
    a:hover { color: #174ea6; border-bottom: 1px solid #2563eb; }
    code {
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
        background: #f3f4f6;
        border-radius: 5px;
        font-size: 95%;
        padding: .18em .5em;
        color: #d6336c;
    }
    pre {
        background: #23272e;
        color: #f8f8f2;
        border-radius: 10px;
        overflow-x: auto;
        padding: 18px 16px;
        margin: 1.5em 0;
        font-size: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    pre code {
        background: none;
        color: inherit;
        padding: 0;
        border-radius: 0;
    }
    blockquote {
        border-left: 5px solid #b3d3f6;
        background: #f3f8fd;
        color: #555;
        padding: 0.8em 1.2em;
        margin: 1.5em 0;
        border-radius: 8px;
        font-style: italic;
    }
    table { 
        border-collapse: collapse; 
        margin: 1.5em 0;
        width: 100%;
        background: #fafbfc;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    th, td { 
        border: 1px solid #eaecef; 
        padding: 12px 18px; 
        text-align: left;
    }
    th {
        background: #f3f4f6;
        font-weight: 600;
    }
    img { max-width: 100%; height: auto; border-radius: 8px; }
    ul, ol {
        margin: 1.2em 0 1.2em 1.5em;
        padding-left: 1.2em;
    }
    li {
        margin: 6px 0;
    }
    hr {
        border: none;
        border-top: 1.5px solid #eaecef;
        margin: 2em 0;
    }
    /* 数学公式样式 */
    .katex { 
        font-size: 1.13em !important; 
    }
    .katex-display { 
        text-align: center !important; 
        margin: 1.8em 0 !important; 
        overflow-x: auto;
        overflow-y: hidden;
    }
    .katex-html {
        white-space: nowrap;
    }
    .math-display {
        text-align: center;
        margin: 1.8em 0;
        overflow-x: auto;
    }
    .math-inline {
        display: inline;
    }
    .math-inline, .math-display {
        font-family: 'KaTeX_Main', 'Times New Roman', serif;
    }
    /* 滚动条美化 */
    ::-webkit-scrollbar {
        width: 8px;
        background: #f3f4f6;
    }
    ::-webkit-scrollbar-thumb {
        background: #e0e0e0;
        border-radius: 4px;
    }
    """

    style_content = default_css if css is None else css

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown Rendered</title>
        <style>
            {style_content}
        </style>
        <!-- KaTeX 配置和加载 -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                renderMathInElement(document.body, {{
                    delimiters: [
                        {{left: '$$', right: '$$', display: true}},
                        {{left: '$', right: '$', display: false}},
                        {{left: '\\\\(', right: '\\\\)', display: false}},
                        {{left: '\\\\[', right: '\\\\]', display: true}}
                    ],
                    throwOnError: false,
                    errorColor: '#cc0000',
                    strict: false,
                    trust: true,
                    macros: {{
                        "\\\\RR": "\\\\mathbb{{R}}",
                        "\\\\NN": "\\\\mathbb{{N}}",
                        "\\\\ZZ": "\\\\mathbb{{Z}}",
                        "\\\\QQ": "\\\\mathbb{{Q}}",
                        "\\\\CC": "\\\\mathbb{{C}}"
                    }}
                }});
                
                // 标记渲染完成
                window.mathRenderComplete = true;
                console.log("KaTeX rendering completed");
            }});
        </script>
    </head>
    <body>
        <div class="markdown-body" id="markdown-content">
            {html_content}
        </div>
    </body>
    </html>
    """

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
            await page.wait_for_function("typeof renderMathInElement !== 'undefined'", timeout=10000)
            # 等待一段时间让渲染完成
            await page.wait_for_timeout(1000)
            print("✅ KaTeX 渲染完成")
        except Exception as e:
            print(f"⚠️ KaTeX 渲染可能有问题，继续截图: {e}")
            await page.wait_for_timeout(1000)

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
        except Exception:
            pass

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
