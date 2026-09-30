"""Operator commands for news inspection, preview, and explicit failed-delivery retry."""

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import UniMessage

from .delivery import deliver
from .rendering import render_text
from .scheduler import context, generate

news = on_command("news", permission=SUPERUSER, priority=5, block=True)


async def _reply(text: str):
    """Send through the UniMessage exporter; ``matcher.finish`` cannot convert UniMessage segments."""
    await UniMessage.text(text).send()


@news.handle()
async def handle_news(args=CommandArg()):  # noqa: B008
    parts = str(args).strip().split()
    action = parts[0] if parts else "latest"
    cfg, repo, _service = context()
    await repo.initialize()

    if action == "preview":
        _, _, report = await generate(namespace="preview")
        await _reply(render_text(report))
    elif action == "latest":
        report = await repo.latest(cfg.board)
        await _reply(render_text(report) if report else "暂无新闻简报")
    elif action == "status":
        report = await repo.latest(cfg.board)
        if not report:
            await _reply("暂无新闻简报")
        else:
            rows = await repo.deliveries(report["id"])
            states = ", ".join(f"{row['target']}={row['state']}" for row in rows)
            await _reply(f"{report['id']} {report['status']} / {states}")
    elif action == "retry":
        if len(parts) != 2 or not parts[1].isascii() or not parts[1].isdigit():
            await _reply("用法：/news retry <群号>")
        else:
            report = await repo.latest(cfg.board)
            if not report:
                await _reply("暂无新闻简报")
            else:
                target = parts[1]
                targets = await repo.retry_failed(report["id"], [target])
                sent = await deliver(repo, report, targets, cfg, stage=False)
                message = "已补发" if sent else "未补发：仅 failed 状态允许显式重试"
                await _reply(message)
    else:
        await _reply("用法：/news latest|status|preview|retry <群号>")
