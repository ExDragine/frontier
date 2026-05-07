import re
import time

from nonebot import get_bot, on_command, require
from nonebot.adapters.milky.event import MessageEvent

from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.message import message_extract
from utils.paint_service import PaintRateLimiter, paint
from utils.paint_service import PaintRateLimitResult as PaintRateLimitResult
from utils.reply_context import build_reply_context, reply_seq_from_segments, strip_reply_marker
from utils.video_service import MediaReference, VideoGenerationResult, generate_video

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402

painter = on_command("画图", priority=3, block=True, aliases={"paint", "绘图", "画一张图", "帮我画一张图"})
videographer = on_command("video", priority=3, block=True, aliases={"视频"})
PAINT_COMMAND_PREFIXES = ("帮我画一张图", "画一张图", "画图", "绘图", "paint")
VIDEO_COMMAND_PREFIXES = ("video", "视频")
messages_db = MessageDatabase()


paint_rate_limiter = PaintRateLimiter()
video_rate_limiter = PaintRateLimiter()


@painter.handle()
async def handle_painter(event: MessageEvent):
    if EnvConfig.PAINT_MODULE_ENABLED is False:
        await painter.finish("么得画了，等升级哇!")
    text, images, *_ = await message_extract(event.data.segments)
    quoted_images: list[bytes] = []
    if reply_seq := reply_seq_from_segments(event.data.segments):
        group_id = event.data.group.group_id if event.data.group else None
        quote_text, quoted_images = await build_reply_context(get_bot(), event, reply_seq, group_id, messages_db)
        text = strip_reply_marker(text, reply_seq)
        if quote_text:
            text += quote_text
    prompt = strip_paint_prompt(text)
    reference_images = quoted_images + images
    if not prompt:
        tip = "你想怎么修改这张图？" if reference_images else "你想画点什么？"
        await UniMessage.text(tip).send()
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
    image = await paint(prompt, reference_images)
    if image:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.image(raw=image)).send()
    else:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.text("图被肥猫吃了，画不了嘞")).send()


@videographer.handle()
async def handle_video(event: MessageEvent):
    if EnvConfig.VIDEO_MODULE_ENABLED is False:
        await videographer.finish("视频功能没开")

    text, images, _audio, videos = await message_extract(event.data.segments)
    prompt = strip_video_prompt(text)
    if not prompt:
        await UniMessage.text("你想生成什么视频？").send()
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

    video_input = MediaReference(data=videos[-1], mime_type="video/mp4") if videos else None
    image_input = None if video_input else MediaReference(data=images[-1], mime_type="image/jpeg") if images else None

    generated_video = await generate_video(prompt, image=image_input, video=video_input)
    video_message = _video_result_message(generated_video)
    if video_message:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.text("视频生成OK了")).send()
        await video_message.send()
    else:
        await (UniMessage.reply(str(event.data.message_seq)) + UniMessage.text("视频生成失败了")).send()


def strip_paint_prompt(text: str) -> str:
    stripped = text.strip()
    for prefix in PAINT_COMMAND_PREFIXES:
        boundary = r"(?:\b|\s+|$)" if prefix.isascii() else ""
        pattern = rf"^/?{re.escape(prefix)}{boundary}"
        if re.match(pattern, stripped, flags=re.IGNORECASE):
            return re.sub(pattern, "", stripped, count=1, flags=re.IGNORECASE).strip()
    return stripped


def strip_video_prompt(text: str) -> str:
    stripped = text.strip()
    for prefix in VIDEO_COMMAND_PREFIXES:
        boundary = r"(?:\b|\s+|$)" if prefix.isascii() else ""
        pattern = rf"^/?{re.escape(prefix)}{boundary}"
        if re.match(pattern, stripped, flags=re.IGNORECASE):
            return re.sub(pattern, "", stripped, count=1, flags=re.IGNORECASE).strip()
    return stripped


def _video_result_message(video: VideoGenerationResult | None):
    if video is None:
        return None
    if video.raw:
        return UniMessage.video(raw=video.raw)
    if video.url:
        return UniMessage.video(url=video.url)
    return None
