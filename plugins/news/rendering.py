"""Render archived payloads; rendering never changes editorial content."""
from pathlib import Path
from jinja2 import Environment,FileSystemLoader
from utils.markdown_render import html_to_image
HERE=Path(__file__).resolve().parent
def render_html(report):
 payload=report["payload"]; evidence={x["article_id"]:x for x in report["evidence"]}
 def item(s):
  names=[]
  for ref in s["evidence"]:
   a=evidence.get(ref["article_id"])
   if a and a["source"] not in names:names.append(a["source"])
  return {**s,"source_text":"、".join(names)}
 return Environment(loader=FileSystemLoader(str(HERE/"templates")),autoescape=True).get_template("daily_news.html").render(current_time="",period="新闻简报",report_time="",top_stories=[item(x) for x in payload["top_stories"]],worth_reading=[item(x) for x in payload["worth_reading"]])
async def render_image(report,timeout=30):
 import asyncio
 async with asyncio.timeout(timeout):
  return await html_to_image(render_html(report),css=(HERE/"templates"/"daily_news.css").read_text(encoding="utf-8"))
def render_text(report):
 lines=["Frontier 新闻简报"]
 for i,s in enumerate(report["payload"]["top_stories"]+report["payload"]["worth_reading"],1):
  lines.append(f"{i}. {s['title']}\n{s['summary']}")
 return "\n\n".join(lines)
