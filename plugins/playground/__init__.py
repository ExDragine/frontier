# ruff: noqa: E402

import time

from nonebot import on_command, on_notice, require
from nonebot.adapters.milky.bot import Bot
from nonebot.adapters.milky.event import FriendNudgeEvent, GroupNudgeEvent, MessageEvent

require("nonebot_plugin_alconna")

from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.message import download_media, message_extract
from utils.paint_service import PaintRateLimiter, paint
from utils.video_service import generate_video

notice = on_notice(priority=0, block=True)
paint_entry = on_command("paint", priority=3, block=True, aliases={"画图", "绘图"})
video_entry = on_command("video", priority=3, block=True, aliases={"视频", "生成视频"})

paint_rate_limiter = PaintRateLimiter()
video_rate_limiter = PaintRateLimiter()

PAINT_PREFIXES = ("/paint", "paint", "/画图", "画图", "/绘图", "绘图")
VIDEO_PREFIXES = ("/video", "video", "/视频", "视频", "/生成视频", "生成视频")
MEDIA_ACCESS_DENIED = "没有权限使用媒体生成功能"


@notice.handle()
async def handle_notice(bot: Bot, event: FriendNudgeEvent | GroupNudgeEvent):
    if isinstance(event, FriendNudgeEvent):
        is_self_send = event.data.is_self_send
        is_self_receive = event.data.is_self_receive
        if not is_self_send and is_self_receive:
            await bot.send_friend_nudge(user_id=event.data.user_id)
    elif isinstance(event, GroupNudgeEvent):
        sender_id = event.data.sender_id
        receiver_id = event.data.receiver_id
        if sender_id != event.self_id and receiver_id == event.self_id:
            await bot.send_group_nudge(group_id=event.data.group_id, user_id=sender_id)


def _event_group_id(event: MessageEvent) -> int | None:
    return event.data.group.group_id if event.data.group else None


def _contains_id(values: list, target: int | str | None) -> bool:
    if target is None:
        return False
    target_text = str(target)
    return any(str(value) == target_text for value in values)


def _has_media_permission(event: MessageEvent) -> bool:
    user_id = event.get_user_id()
    group_id = _event_group_id(event)

    if _contains_id(EnvConfig.PAINT_BLACKLIST_PERSON_LIST, user_id):
        return False
    if _contains_id(EnvConfig.PAINT_BLACKLIST_GROUP_LIST, group_id):
        return False
    if not EnvConfig.PAINT_WHITELIST_MODE:
        return True
    return _contains_id(EnvConfig.PAINT_WHITELIST_PERSON_LIST, user_id) or _contains_id(
        EnvConfig.PAINT_WHITELIST_GROUP_LIST, group_id
    )


def _strip_command_prefix(text: str, prefixes: tuple[str, ...]) -> str:
    stripped = text.strip()
    for prefix in sorted(prefixes, key=len, reverse=True):
        if stripped.lower().startswith(prefix.lower()):
            return stripped[len(prefix) :].strip()
    return stripped


@paint_entry.handle()
async def handle_paint_entry(event: MessageEvent):
    if EnvConfig.PAINT_MODULE_ENABLED is False:
        await UniMessage.text("绘画功能未启用").send()
        return
    if not _has_media_permission(event):
        await UniMessage.text(MEDIA_ACCESS_DENIED).send()
        return

    text, image_items, audio_items, video_items = await message_extract(event.data.segments)
    prompt = _strip_command_prefix(text, PAINT_PREFIXES)
    if not prompt:
        await UniMessage.text("用法: /paint <提示词>，可附带图片进行编辑").send()
        return

    rate_limit = paint_rate_limiter.check(
        event.get_user_id(),
        now=time.time(),
        max_requests=EnvConfig.PAINT_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.PAINT_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        await UniMessage.text(f"画得太快了，{rate_limit.retry_after_seconds} 秒后再试吧").send()
        return

    images, _audio, _videos = await download_media(image_items, audio_items, video_items)
    image = await paint(prompt, images)
    if not image:
        await UniMessage.text("图片生成失败").send()
        return
    await UniMessage.image(raw=image).send()


@video_entry.handle()
async def handle_video_entry(event: MessageEvent):
    if EnvConfig.VIDEO_MODULE_ENABLED is False:
        await UniMessage.text("视频功能没开").send()
        return
    if not _has_media_permission(event):
        await UniMessage.text(MEDIA_ACCESS_DENIED).send()
        return

    text, image_items, audio_items, video_items = await message_extract(event.data.segments)
    prompt = _strip_command_prefix(text, VIDEO_PREFIXES)
    if not prompt:
        await UniMessage.text("用法: /video <提示词>，可附带图片或视频作为输入").send()
        return

    rate_limit = video_rate_limiter.check(
        event.get_user_id(),
        now=time.time(),
        max_requests=EnvConfig.VIDEO_RATE_LIMIT_MAX_REQUESTS,
        window_seconds=EnvConfig.VIDEO_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not rate_limit.allowed:
        await UniMessage.text(f"视频生成得太快了，{rate_limit.retry_after_seconds} 秒后再试吧").send()
        return

    images, _audio, videos = await download_media(image_items, audio_items, video_items)
    if videos:
        generated = await generate_video(prompt, video=videos[-1])
    elif images:
        generated = await generate_video(prompt, image=images[-1])
    else:
        generated = await generate_video(prompt)

    if generated is None:
        await UniMessage.text("视频生成失败了").send()
        return
    if raw := getattr(generated, "raw", None):
        await UniMessage.video(raw=raw).send()
        return
    if url := getattr(generated, "url", None):
        await UniMessage.video(url=url).send()
        return
    await UniMessage.text("视频生成失败了").send()
