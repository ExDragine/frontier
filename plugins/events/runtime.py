"""Lifecycle and administrator access for the durable Milky request inbox."""

import asyncio

from nonebot import get_bot, get_bots, get_driver, logger, on_command, on_request
from nonebot.adapters.milky import Bot
from nonebot.adapters.milky.event import (
    FriendRequestEvent,
    GroupInvitationEvent,
    GroupInvitedJoinRequestEvent,
    GroupJoinRequestEvent,
    MessageEvent,
    RequestEvent,
)
from nonebot.adapters.milky.message import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from utils.configs import EnvConfig
from utils.database.platform_events import PlatformEventStore
from utils.event_orchestration import EventOrchestrator
from utils.platform_event import normalize_request

store = PlatformEventStore()
orchestrator = EventOrchestrator(store, lambda: EnvConfig.settings.events, lambda bot_id: get_bot(bot_id))
tasks: list[asyncio.Task] = []
ready = asyncio.Event()


async def supported(event: RequestEvent):
    return isinstance(event, (FriendRequestEvent, GroupJoinRequestEvent, GroupInvitedJoinRequestEvent, GroupInvitationEvent))


requests = on_request(rule=supported, priority=10, block=False)


@requests.handle()
async def receive(event: RequestEvent):
    await ready.wait()
    await orchestrator.ingest(normalize_request(event))


async def worker():
    while True:
        try:
            cfg = EnvConfig.settings.events
            bots = [key for key, bot in get_bots().items() if isinstance(bot, Bot)]
            row = await store.claim(bots, cfg.timeout_seconds + 150) if cfg.enabled else None
            if row:
                await orchestrator.process(row)
            else:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise
        except Exception as error:  # noqa: BLE001 - keep inbox alive without logging event bodies
            logger.error("Event inbox worker failed: {}", type(error).__name__)
            await asyncio.sleep(5)


async def maintenance():
    while True:
        try:
            await store.recover()
            await store.cleanup(EnvConfig.settings.events.retention_days)
            bots = [key for key, bot in get_bots().items() if isinstance(bot, Bot)]
            for row in await store.unknown(bots):
                try:
                    async with asyncio.timeout(10):
                        await orchestrator.reconcile(row)
                except TimeoutError:
                    pass
                await store.mark_checked(row["key"])
        except asyncio.CancelledError:
            raise
        except Exception as error:  # noqa: BLE001 - maintenance cannot interrupt event delivery
            logger.error("Event inbox maintenance failed: {}", type(error).__name__)
        await asyncio.sleep(60)


@get_driver().on_startup
async def startup():
    await store.initialize()
    await store.recover()
    ready.set()
    tasks.extend(asyncio.create_task(worker(), name=f"milky-event-{index}") for index in range(EnvConfig.settings.events.workers))
    tasks.append(asyncio.create_task(maintenance(), name="milky-event-maintenance"))


@get_driver().on_shutdown
async def shutdown():
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    tasks.clear()
    ready.clear()


command = on_command("events", permission=SUPERUSER, priority=1, block=True)
_COMMAND_ARG = CommandArg()


@command.handle()
async def inspect_events(event: MessageEvent, args: Message = _COMMAND_ARG):
    # Application comments are never echoed. Administration stays in private chat.
    if not event.is_private:
        await command.finish("请在私聊中管理事件。")
    await ready.wait()
    parts = args.extract_plain_text().split()
    if len(parts) == 2 and parts[0] == "retry":
        changed = await store.requeue(parts[1])
        await command.finish("已按当前策略重新排队。" if changed else "不能重新排队：事件不存在、过期或已尝试执行。")
    rows = await store.recent()
    if parts == ["reconcile"]:
        for row in rows:
            if row["status"] == "unknown":
                try:
                    async with asyncio.timeout(15):
                        await orchestrator.reconcile(row)
                except TimeoutError:
                    pass
        rows = await store.recent()
    lines = [f"{row['key']}\nbot={row['bot_id']} {row['status']} / {row['proposal'] or '-'} / {row['detail'] or '-'}" for row in rows]
    await command.finish("\n".join(lines) or "暂无事件。")
