"""Per-target QQ delivery; failures need an explicit /news retry."""

import asyncio

from nonebot import get_bot
from nonebot_plugin_alconna import Target, UniMessage

from .rendering import render_text


async def deliver(repo, report, targets, cfg, *, stage=True):
    target_ids = {str(target) for target in targets}
    if stage:
        await repo.stage_deliveries(report["id"], list(target_ids))
    sent = []
    for row in await repo.deliveries(report["id"]):
        if row["target"] not in target_ids or row["state"] not in {"pending", "failed"}:
            continue
        try:
            message = (
                UniMessage().image(raw=report["image"])
                if report.get("image")
                else UniMessage.text(render_text(report))
            )
            bot = get_bot(cfg.bot_id) if cfg.bot_id else None
            async with asyncio.timeout(cfg.send_timeout):
                await message.send(target=Target.group(row["target"]), bot=bot)
        except Exception as exc:
            await repo.mark_delivery(report["id"], row["target"], "failed", error=type(exc).__name__)
        else:
            await repo.mark_delivery(report["id"], row["target"], "sent")
            sent.append(int(row["target"]))
    return sent
