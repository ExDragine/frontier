# ruff: noqa: E402

import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain.messages import AIMessage
from nonebot import get_bot, get_driver, logger, on_message, require
from nonebot.adapters.milky.event import MessageEvent

require("nonebot_plugin_alconna")

from utils.agents import FrontierCognitive, ProgressEvent, agent_thread_id, run_serialized
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.database import MessageDatabase, build_message_metadata
from utils.media import resolve_media, standard_media_block
from utils.message import (
    _get_wake_words,
    download_media,
    extract_message_files,
    format_staged_message_files,
    message_check,
    message_extract,
    message_gateway,
    outgoing_message_content,
    sanitize_outgoing_text,
    send_artifacts,
    send_messages,
    stage_message_files,
)
from utils.message_normalizer import NORMALIZED_VERSION, normalize_segments
from utils.reply_context import build_reply_context, reply_seq_from_segments

messages_db = MessageDatabase()
f_cognitive = FrontierCognitive()
driver = get_driver()

common = on_message(priority=10)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class AgentRequestContext:
    bot: Any
    event: MessageEvent
    user_id: str
    user_name: str
    event_id: int
    group_id: int | None
    msg_time: int
    text: str
    quoted_images: list[bytes]
    images: list[bytes]
    videos: list[bytes]
    quoted_text: str = ""
    audio: list[bytes] = field(default_factory=list)


def _agent_workspace_key(user_id: str, group_id: int | None) -> str:
    return str(group_id) if group_id is not None else str(user_id)


def _agent_memory_dir(user_id: str, group_id: int | None) -> Path:
    working_dir = Path(getattr(f_cognitive, "working_dir", os.path.join(os.getcwd(), "cache", "sandbox")))
    return working_dir / "memory" / _agent_workspace_key(user_id, group_id)


def _group_member_role(event: MessageEvent) -> str | None:
    member = getattr(getattr(event, "data", None), "group_member", None)
    role = getattr(member, "role", None)
    if role in (None, ""):
        return None
    return str(role)


def _remove_attached_image_placeholders(text: str, attached_images: int) -> str:
    """移除已作为视觉内容附加的当前消息图片占位行。"""
    if attached_images <= 0 or not text:
        return text

    remaining = attached_images
    lines: list[str] = []
    for line in text.splitlines():
        marker = line.strip()
        is_image_marker = marker == "[图片]" or (marker.startswith("[图片:") and marker.endswith("]"))
        if remaining and is_image_marker:
            remaining -= 1
            continue
        lines.append(line)
    return "\n".join(lines).strip()


async def _private_chat_reporter(event: ProgressEvent) -> None:
    """私聊场景的进度事件消费者 —— 向用户发送当前 Agent 正在做什么。"""
    match event.type:
        case "thinking" | "subagent_start" | "tool_call":
            await UniMessage.text(event.message).send()


async def _process_agent_request(context: AgentRequestContext, history_messages: list[dict] | None = None) -> bool:  # noqa: C901
    messages = list(history_messages or [])
    combined_text = f"{context.text}{context.quoted_text}".strip()
    remaining_bytes = EnvConfig.MAX_INLINE_MEDIA_BYTES
    remaining_images = EnvConfig.MAX_INLINE_IMAGES

    def take_inline(items: list[bytes], kind: str) -> tuple[list[bytes], int]:
        nonlocal remaining_bytes, remaining_images
        selected: list[bytes] = []
        for item in items:
            if kind == "image" and remaining_images <= 0:
                continue
            if len(item) > remaining_bytes:
                continue
            selected.append(item)
            remaining_bytes -= len(item)
            if kind == "image":
                remaining_images -= 1
        return selected, len(items) - len(selected)

    inline_quoted_images, omitted_quoted_images = take_inline(context.quoted_images, "image")
    inline_images, omitted_images = take_inline(context.images, "image")
    inline_audio, omitted_audio = take_inline(context.audio, "audio")
    inline_videos, omitted_videos = take_inline(context.videos, "video")
    current_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": str(
                {
                    "metadata": build_message_metadata(
                        timestamp_ms=context.msg_time,
                        user_id=context.user_id,
                        group_id=context.group_id,
                        user_name=context.user_name,
                    ),
                    "is_current": True,
                    "content": combined_text,
                }
            ),
        }
    ]
    if inline_quoted_images:
        current_content.append({"type": "text", "text": "以下图片来自上面的引用消息："})
        current_content.extend(standard_media_block(resolve_media(image, "image")) for image in inline_quoted_images)
    if inline_images:
        current_content.append({"type": "text", "text": "以下图片来自当前消息："})
        current_content.extend(standard_media_block(resolve_media(image, "image")) for image in inline_images)
    if inline_audio:
        current_content.append({"type": "text", "text": "以下语音来自当前消息："})
        current_content.extend(standard_media_block(resolve_media(audio, "audio")) for audio in inline_audio)
    if inline_videos:
        current_content.append({"type": "text", "text": "以下视频来自当前消息："})
        current_content.extend(standard_media_block(resolve_media(video, "video")) for video in inline_videos)
    omitted_labels = [
        f"引用图片 {omitted_quoted_images} 张" if omitted_quoted_images else "",
        f"当前图片 {omitted_images} 张" if omitted_images else "",
        f"语音 {omitted_audio} 条" if omitted_audio else "",
        f"视频 {omitted_videos} 条" if omitted_videos else "",
    ]
    omitted_labels = [label for label in omitted_labels if label]
    if omitted_labels:
        current_content.append(
            {
                "type": "text",
                "text": f"[以下媒体因上下文预算未直接内联：{'、'.join(omitted_labels)}；可使用上方工作区路径读取]",
            }
        )
    messages += [
        {
            "role": "user",
            "content": "以上是对话历史，仅用于理解上下文。",
        },
        {
            "role": "user",
            "content": current_content,
        },
    ]
    capability = EnvConfig.AGENT_CAPABILITY

    # 提取当前消息触发的唤醒词
    get_plaintext = getattr(context.event, "get_plaintext", None)
    plaintext = str(get_plaintext() if callable(get_plaintext) else context.text).strip()
    triggered_wake = ""
    if context.group_id:
        wake_words = _get_wake_words(context.group_id)
        for w in wake_words:
            if plaintext.startswith(w):
                triggered_wake = w
                break

    result = await f_cognitive.chat_agent(
        messages,
        context.user_id,
        context.user_name,
        capability,
        group_id=context.group_id,
        image_inputs=context.quoted_images + context.images,
        audio_inputs=context.audio,
        video_inputs=context.videos,
        wake_word=triggered_wake or None,
        group_member_role=_group_member_role(context.event),
        progress_reporter=_private_chat_reporter if context.group_id is None else None,
        user_text=context.text,
    )

    if not isinstance(result, dict) or "response" not in result:
        await UniMessage.text(f"{EnvConfig.BOT_NAME}飞升了，暂时不可用").send()
        return True

    response = result["response"]
    if not response:
        await UniMessage.text(f"{EnvConfig.BOT_NAME}飞升了，暂时不可用").send()
        return True

    if result.get("error"):
        logger.warning("Agent returned error response: %s", result["error"])

    artifacts: list[UniMessage] | None = result.get("uni_messages", [])
    if artifacts:
        logger.info(f"📤 发送 {len(artifacts)} 个媒体工件")
        await send_artifacts(artifacts)

    if response["messages"] and isinstance(response["messages"], list):
        response_content = outgoing_message_content(response["messages"][-1])
        sanitized_response = await sanitize_outgoing_text(response_content)
        if sanitized_response != response_content:
            response["messages"][-1] = AIMessage(content=sanitized_response)
        await messages_db.insert(
            time=int(time.time() * 1000),
            msg_id=None,
            user_id=int(context.event.self_id),
            group_id=context.group_id,
            user_name="Assistant",
            role="assistant",
            content=outgoing_message_content(response["messages"][-1]),
        )
        await send_messages(context.group_id, context.event_id, response)
    else:
        await UniMessage.text(response["messages"]).send()
    return True


@driver.on_shutdown
async def on_shutdown():
    from tools.ens_professional import clear_ens_cache as clear_ens_professional_cache

    clear_ens_professional_cache()
    from utils.browser_capture import close_browser
    from utils.http_client import aclose_all

    await close_browser()
    await aclose_all()


@driver.on_startup
async def on_startup():
    if EnvConfig.IMAGE_AUTO_CLEANUP:
        try:
            cleaned_attachments = await messages_db.cleanup_expired_attachments()
            if cleaned_attachments:
                logger.info("已清理过期消息附件: %s", cleaned_attachments)
            repair_legacy_media = getattr(messages_db, "repair_legacy_media_attachments", None)
            if repair_legacy_media is not None:
                verified, corrected = await repair_legacy_media()
                if verified:
                    logger.info("已校验历史媒体附件: %s，修正: %s", verified, corrected)
        except Exception as exc:
            logger.warning("消息附件维护失败: %s: %s", type(exc).__name__, exc)


@common.handle()
async def handle_common(event: MessageEvent):  # noqa: C901
    if EnvConfig.AGENT_MODULE_ENABLED is False:
        await common.finish(f"{EnvConfig.BOT_NAME}飞升了,暂时不可用")

    try:
        bot = get_bot()
    except ValueError:
        bot = getattr(event, "bot", None)
        if bot is None:
            await common.finish()
    user_id = event.get_user_id()
    user_name = event.data.sender.nickname
    event_id = event.data.message_seq
    group_id = event.data.group.group_id if event.data.group else None

    # ── Phase 1: 快速提取文本（不下载媒体）──
    text, image_downloaders, audio_downloaders, video_downloaders = await message_extract(event.data.segments)
    file_items = extract_message_files(event.data.segments)
    normalized_message = await normalize_segments(bot, event.data.segments)
    if normalized_message.content:
        text = normalized_message.content
    current_text = text

    reply_seq = reply_seq_from_segments(event.data.segments)
    quote_text = ""
    if reply_seq:
        quote_text, _ = await build_reply_context(
            bot,
            event,
            reply_seq,
            group_id,
            messages_db,
            load_images=False,
        )
    if video_downloaders and "[视频" not in current_text:
        current_text = f"{current_text}\n{' '.join('[视频]' for _ in video_downloaders)}".strip()
    if audio_downloaders and "[语音" not in current_text:
        current_text = f"{current_text}\n{' '.join('[语音]' for _ in audio_downloaders)}".strip()
    if not current_text and not quote_text:
        if not event.is_tome():
            await common.finish()
        else:
            current_text = ""

    msg_time = int(time.time() * 1000)
    text = f"{current_text}{quote_text}".strip()

    # ── Phase 2: 存储消息文本与结构化元数据 + 快速网关检查 ──
    await messages_db.insert(
        time=msg_time,
        msg_id=event_id,
        user_id=int(user_id),
        group_id=group_id,
        user_name=user_name,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
        raw_segments_json=normalized_message.raw_segments_json,
        normalized_version=normalized_message.normalized_version,
        normalized_status=normalized_message.status,
    )
    if normalized_message.derived_messages:
        await messages_db.replace_derived_messages(
            parent_msg_time=msg_time,
            parent_msg_id=event_id,
            user_id=int(user_id),
            group_id=group_id,
            role="user" if user_id != str(event.self_id) else "assistant",
            derived_messages=normalized_message.derived_messages,
            normalized_version=NORMALIZED_VERSION,
        )

    messages = await messages_db.prepare_message(
        int(user_id),
        group_id,
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
        before_time=msg_time,
    )

    if not await message_gateway(event, messages):
        await common.finish()

    # ── Phase 3: 网关通过后才下载当前消息及引用消息中的媒体 ──
    media_task = download_media(image_downloaders, audio_downloaders, video_downloaders)
    files_task = stage_message_files(
        bot,
        file_items,
        memory_dir=_agent_memory_dir(user_id, group_id),
        workspace_key=_agent_workspace_key(user_id, group_id),
        user_id=user_id,
        group_id=group_id,
    )
    if reply_seq:
        quote_task = build_reply_context(bot, event, reply_seq, group_id, messages_db)
        (images, audio, videos), staged_files, (agent_quote_text, quoted_images) = await asyncio.gather(
            media_task,
            files_task,
            quote_task,
        )
    else:
        (images, audio, videos), staged_files = await asyncio.gather(media_task, files_task)
        agent_quote_text, quoted_images = "", []

    agent_text = _remove_attached_image_placeholders(current_text, len(images))
    if staged_file_text := format_staged_message_files(staged_files):
        agent_text = f"{agent_text}\n{staged_file_text}".strip()

    persisted_media = []
    if EnvConfig.IMAGE_ENABLED:
        persisted_media.extend(resolve_media(image, "image") for image in images)
    persisted_media.extend(resolve_media(item, "audio") for item in audio)
    persisted_media.extend(resolve_media(item, "video") for item in videos)
    persisted_attachments = []
    if persisted_media and hasattr(messages_db, "insert_media"):
        try:
            persisted_attachments = await messages_db.insert_media(
                msg_time=msg_time,
                msg_id=event_id,
                user_id=int(user_id),
                group_id=group_id,
                media=persisted_media,
            )
        except Exception as e:
            logger.warning(f"⚠️ 媒体保存失败（不影响主流程）: {e}")
    elif images and EnvConfig.IMAGE_ENABLED and hasattr(messages_db, "insert_images"):
        try:
            await messages_db.insert_images(
                msg_time=msg_time,
                user_id=int(user_id),
                group_id=group_id,
                images=images,
            )
        except Exception as e:
            logger.warning(f"⚠️ 图片保存失败（不影响主流程）: {e}")

    if staged_files and hasattr(messages_db, "insert_attachment"):
        expires_at = int(time.time() * 1000) + EnvConfig.MEDIA_TTL_DAYS * 86400 * 1000
        for staged_file in staged_files:
            try:
                await messages_db.insert_attachment(
                    msg_time=msg_time,
                    msg_id=event_id,
                    user_id=int(user_id),
                    group_id=group_id,
                    kind="file",
                    physical_path=str(staged_file.local_path),
                    virtual_path=staged_file.virtual_path,
                    file_name=staged_file.file_name,
                    mime_type=staged_file.mime_type,
                    file_size=staged_file.file_size,
                    sha256=staged_file.sha256,
                    expires_at=expires_at,
                )
            except Exception as e:
                logger.warning(f"⚠️ 文件附件索引失败（不影响主流程）: {e}")

    if persisted_attachments:
        paths = "\n".join(
            f"[{attachment.kind}已保存到工作区 {attachment.virtual_path}]" for attachment in persisted_attachments
        )
        agent_text = f"{agent_text}\n{paths}".strip()

    # ── Phase 4: 内容安全 + Agent 处理 ──
    if EnvConfig.CONTENT_CHECK_ENABLED:
        risk_check = await message_check(f"{agent_text}{agent_quote_text}".strip(), quoted_images + images)
    else:
        risk_check = "Safe"
    match risk_check:
        case "Safe":
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="32", is_add=True
                )
        case "Controversial":
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="212", is_add=True
                )
        case "Unsafe":
            if group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id, reaction="26", is_add=True
                )

    context = AgentRequestContext(
        bot=bot,
        event=event,
        user_id=user_id,
        user_name=user_name,
        event_id=event_id,
        group_id=group_id,
        msg_time=msg_time,
        text=agent_text,
        quoted_images=quoted_images,
        images=images,
        audio=audio,
        videos=videos,
        quoted_text=agent_quote_text,
    )
    thread_id = agent_thread_id(user_id, group_id)
    from utils.ens_gate import _ens_caller_allowed, _ens_prefix

    cleaned = text.strip().lstrip("/")
    is_ens_msg = cleaned[:3].lower() == "vep" or cleaned[:2].lower() == "ve"
    _ens_caller_allowed.set(is_ens_msg)
    if cleaned[:3].lower() == "vep":
        _ens_prefix.set("vep")
    elif cleaned[:2].lower() == "ve":
        _ens_prefix.set("ve")
    else:
        _ens_prefix.set("")
    await run_serialized(str(thread_id), _process_agent_request(context, messages))
    if group_id:
        try:
            await bot.send_group_message_reaction(group_id=group_id, message_seq=event_id, reaction="32", is_add=False)
        except Exception as e:
            logger.warning(f"❌ 发送群消息反应失败 用户{user_id} 群{group_id}: {e}")
