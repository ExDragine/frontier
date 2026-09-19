"""Render archived payloads without changing editorial content."""

import asyncio
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from utils.markdown_render import html_to_image

HERE = Path(__file__).resolve().parent


def render_html(report):
    payload = report["payload"]
    evidence = {item["article_id"]: item for item in report["evidence"]}

    def template_item(story):
        names = []
        for reference in story["evidence"]:
            article = evidence.get(reference["article_id"])
            if article and article["source"] not in names:
                names.append(article["source"])
        return {**story, "source_text": "、".join(names)}

    template = Environment(
        loader=FileSystemLoader(str(HERE / "templates")), autoescape=True
    ).get_template("daily_news.html")
    return template.render(
        current_time="", period="新闻简报", report_time="",
        top_stories=[template_item(item) for item in payload["top_stories"]],
        worth_reading=[template_item(item) for item in payload["worth_reading"]],
    )


async def render_image(report, timeout=30):
    css = (HERE / "templates" / "daily_news.css").read_text(encoding="utf-8")
    async with asyncio.timeout(timeout):
        return await html_to_image(render_html(report), css=css)


def render_text(report):
    lines = ["Frontier 新闻简报"]
    stories = report["payload"]["top_stories"] + report["payload"]["worth_reading"]
    for index, story in enumerate(stories, 1):
        lines.append(f"{index}. {story['title']}\n{story['summary']}")
    return "\n\n".join(lines)
