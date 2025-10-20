import os
import re
import secrets

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt
from playwright.async_api import async_playwright


async def markdown_to_text(markdown_text):
    html = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"]).render(markdown_text)
    plain_text = BeautifulSoup(html, "html.parser").get_text()
    return plain_text


async def markdown_to_image(markdown_text):
    html = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"]).render(markdown_text)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        image = await page.screenshot()
        await browser.close()
        return image


async def playwright_render(name: str, packed_args: dict):
    trigger_mark = secrets.token_hex(16)
    cache_file = f"{os.getcwd()}/cache/{trigger_mark}.html"
    # 设置模板加载路径
    env = Environment(loader=FileSystemLoader("./templates/"), autoescape=True)

    # 加载模板

    match name:
        case "eq_usgs":
            template = env.get_template("eew.html")
            depth = packed_args.get("depth")
            if isinstance(depth, str):
                pattern = re.compile(r"[\d.]+")
                result = pattern.search(depth)
                if result:
                    depth = result.group(0)
                else:
                    depth = 10.0
            else:
                depth = depth

            # 渲染模板
            rendered_html = template.render(
                title=packed_args["title"],
                detail=packed_args["detail"],
                latitude=float(packed_args["latitude"]),
                longitude=float(packed_args["longitude"]),
                magnitude=float(packed_args["magnitude"]),
                depth=float(packed_args["depth"]),
            )
        case _:
            return None

    # 输出或保存渲染结果
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{cache_file}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)
        bytes_picture = None
        element_handle = await page.query_selector("id=card")
        if element_handle is not None:
            bytes_picture = await element_handle.screenshot()
        await browser.close()
        os.remove(cache_file)
        if bytes_picture:
            return bytes_picture
