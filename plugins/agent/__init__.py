# ruff: noqa: E402

import asyncio
import base64
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain.messages import AIMessage
from nonebot import get_bot, get_driver, logger, on_message, require
from nonebot.adapters.milky.event import MessageEvent

require("nonebot_plugin_alconna")

from utils.agents import FrontierCognitive, ProgressEvent, _agent_thread_id, run_serialized
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.database import MessageDatabase, build_message_metadata
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
from utils.staged_artifacts import cleanup_expired_staged_artifacts

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
    if context.quoted_images:
        current_content.append({"type": "text", "text": "以下图片来自上面的引用消息："})
        current_content.extend(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"},
            }
            for image in context.quoted_images
        )
    if context.images:
        current_content.append({"type": "text", "text": "以下图片来自当前消息："})
        current_content.extend(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"},
            }
            for image in context.images
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
    plaintext = context.event.get_plaintext().strip()
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
        except Exception as exc:
            logger.warning("清理过期消息附件失败: %s: %s", type(exc).__name__, exc)
    try:
        cleaned_artifacts = cleanup_expired_staged_artifacts()
        if cleaned_artifacts:
            logger.info("已清理过期 staged artifacts: %s", cleaned_artifacts)
    except Exception as exc:
        logger.warning("清理过期 staged artifacts 失败: %s: %s", type(exc).__name__, exc)


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
    if not current_text and not quote_text:
        if not event.is_tome():
            await common.finish()
        else:
            current_text = ""

    msg_time = int(time.time() * 1000)
    staged_files = await stage_message_files(
        bot,
        file_items,
        memory_dir=_agent_memory_dir(user_id, group_id),
        workspace_key=_agent_workspace_key(user_id, group_id),
        user_id=user_id,
        group_id=group_id,
    )
    if staged_file_text := format_staged_message_files(staged_files):
        current_text = f"{current_text}\n{staged_file_text}".strip()
    text = f"{current_text}{quote_text}".strip()

    # ── Phase 2: 存储消息文本/文件路径 + 快速网关检查 ──
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
    if reply_seq:
        quote_task = build_reply_context(bot, event, reply_seq, group_id, messages_db)
        (images, _audio, videos), (agent_quote_text, quoted_images) = await asyncio.gather(media_task, quote_task)
    else:
        images, _audio, videos = await media_task
        agent_quote_text, quoted_images = "", []

    agent_text = _remove_attached_image_placeholders(current_text, len(images))

    if images and EnvConfig.IMAGE_ENABLED:
        try:
            await messages_db.insert_images(msg_time=msg_time, user_id=int(user_id), group_id=group_id, images=images)
        except Exception as e:
            logger.warning(f"⚠️ 图片保存失败（不影响主流程）: {e}")

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
        videos=videos,
        quoted_text=agent_quote_text,
    )
    thread_id = _agent_thread_id(user_id, group_id)
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
