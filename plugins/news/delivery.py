"""Per-target QQ delivery with conservative handling of ambiguous timeouts."""

import asyncio
import time

from nonebot import get_bot
from nonebot_plugin_alconna import Target, UniMessage

from .rendering import render_text


async def deliver(repo, report, targets, cfg):
    target_ids = {str(target) for target in targets}
    await repo.stage_deliveries(report["id"], list(target_ids), time.time() + cfg.catchup_seconds)
    sent = []
    for row in await repo.deliveries(report["id"]):
        if row["target"] not in target_ids:
            continue
        token = await repo.claim_delivery(
            report["id"], row["target"], ttl=cfg.send_timeout + 10, max_attempts=cfg.max_delivery_attempts
        )
        if not token:
            continue
        try:
            message = UniMessage().image(raw=report["image"]) if report.get("image") else UniMessage.text(render_text(report))
            bot = get_bot(cfg.bot_id) if cfg.bot_id else None
            async with asyncio.timeout(cfg.send_timeout):
                result = await message.send(target=Target.group(row["target"]), bot=bot)
            receipt = str(getattr(result, "message_id", getattr(result, "message_seq", ""))) or None
            await repo.finish_delivery(report["id"], row["target"], token, "sent", receipt=receipt)
            sent.append(int(row["target"]))
        except TimeoutError:
            await asyncio.shield(
                repo.finish_delivery(report["id"], row["target"], token, "unknown", error="send_timeout")
            )
        except Exception as exc:
            await repo.finish_delivery(
                report["id"], row["target"], token, "failed",
                error=type(exc).__name__, retry_delay=cfg.retry_delay,
            )
    return sent
