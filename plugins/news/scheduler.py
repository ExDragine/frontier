"""Clockwork adapter for the standalone news plugin."""

import datetime as dt
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from nonebot import logger

from utils.configs import EnvConfig
from utils.http_client import get_http_client

from .config import load_news_config
from .delivery import deliver
from .editor import NewsEditor
from .rendering import render_image
from .repository import NewsRepository
from .schemas import Edition
from .service import NewsService
from .sources import configured_sources


def edition_for(now, cfg, namespace="published"):
    local = now.astimezone(ZoneInfo(cfg.timezone))
    slots = [
        local.replace(hour=9, minute=0, second=0, microsecond=0),
        local.replace(hour=21, minute=0, second=0, microsecond=0),
    ]
    valid = [slot for slot in slots if slot <= local]
    if valid:
        slot = max(valid)
    else:
        slot = (local - dt.timedelta(days=1)).replace(
            hour=21, minute=0, second=0, microsecond=0
        )
    return Edition(cfg.board, slot, window_hours=cfg.window_hours, namespace=namespace)


def context():
    cfg = load_news_config()
    if not cfg.model:
        cfg = cfg.model_copy(
            update={"model": EnvConfig.DAILY_NEWS_MODEL, "provider": EnvConfig.DAILY_NEWS_MODEL_PROVIDER}
        )
    repo = NewsRepository(Path(os.getenv("FRONTIER_NEWS_DB", "news.db")))
    client = get_http_client("news-search", timeout=cfg.source_timeout)
    service = NewsService(repo, configured_sources(client, cfg), NewsEditor(cfg), cfg)
    return cfg, repo, service


async def generate(namespace="published", now=None):
    cfg, repo, service = context()
    await repo.initialize()
    if not cfg.enabled:
        raise RuntimeError("news plugin disabled")
    edition = edition_for(now or dt.datetime.now(dt.UTC), cfg, namespace)
    report = await service.generate_report(edition)
    if report.get("image") is None:
        try:
            image = await render_image(report, cfg.render_timeout)
            await repo.set_image(report["id"], image)
            report = await repo.get(report["id"])
        except Exception as exc:
            logger.warning(f"新闻图片渲染失败，将使用文本降级投递: {type(exc).__name__}")
    return cfg, repo, report


async def daily_news(job_id="daily_news", **_kwargs):
    from plugins.clockwork import task_manager
    from plugins.clockwork.task_models import TaskRunResult

    cfg, repo, report = await generate()
    groups = await task_manager.get_task_groups(job_id)
    sent = await deliver(repo, report, groups, cfg)
    states = await repo.deliveries(report["id"])
    state_text = ",".join(f"{item['target']}:{item['state']}" for item in states)
    return TaskRunResult(
        groups_sent=sent,
        messages_sent=len(sent),
        output_summary=f"news {report['status']}; sent={len(sent)}/{len(groups)}; {state_text}",
    )
