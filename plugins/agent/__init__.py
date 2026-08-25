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
require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

from utils.agents import FrontierCognitive, ProgressEvent, ProgressReporter, agent_thread_id, run_serialized
from utils.agents.acp import acp_service
from utils.agents.conversation_memory import (
    ConversationHistoryRequest,
    ConversationMemoryService,
    ConversationScope,
)
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.database import (
    MessageDatabase,
    build_agent_message_payload,
    serialize_agent_payload,
)
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
from utils.reply_context import build_reply_context, reply_seq_from_segments, sender_names_from_milky_message

messages_db = MessageDatabase()
conversation_memory_service = ConversationMemoryService(messages_db)
f_cognitive = FrontierCognitive()
driver = get_driver()

common = on_message(priority=10)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_CLEANUP_JOB_ID = "frontier_daily_cache_cleanup"
EMPTY_CURRENT_MESSAGE_PROMPT = "[用户叫了你一声]"


async def _schedule_conversation_compaction(user_id: int | str, group_id: int | None) -> None:
    required_methods = (
        "latest_conversation_summary",
        "context_token_total",
        "select_context_page",
        "prepare_message_records",
        "append_conversation_summary",
    )
    if not all(hasattr(messages_db, name) for name in required_methods):
        return
    conversation_memory_service.database = messages_db
    try:
        await conversation_memory_service.maybe_schedule(
            scheduler,
            user_id=user_id,
            group_id=group_id,
        )
    except Exception as exc:
        logger.warning("会话压缩调度失败（不影响回复）: %s: %s", type(exc).__name__, exc)


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
    user_nickname: str | None = None
    user_card: str | None = None
    reply_to: dict[str, object] | None = None


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


def _remove_structured_reply_marker(text: str, reply_seq: int | None) -> str:
    """Drop the legacy text marker once reply identity is carried structurally."""
    if reply_seq is None or not text:
        return text
    marker = f"[回复消息:{reply_seq}]"
    lines = text.splitlines()
    if lines and lines[0].strip() == marker:
        return "\n".join(lines[1:]).strip()
    return text


def _chat_progress_reporter(group_id: int | None) -> ProgressReporter:
    """构造会话级进度消费者；群聊静默，私聊保留有限进度提示。"""
    spoken_messages: set[str] = set()
    spoken_count = 0
    max_spoken_messages = 2

    async def reporter(event: ProgressEvent) -> None:
        nonlocal spoken_count

        # 群聊只发送最终回复和媒体工件，避免中间推理叙述刷屏或泄露。
        if group_id is not None:
            return

        if event.type == "assistant_preamble":
            content = event.message.strip()
            if not content or content in spoken_messages or spoken_count >= max_spoken_messages:
                return

            sanitized = await sanitize_outgoing_text(content)
            # 风险审核改写后的拦截提示不作为过程发言发送，最终回复仍会正常审核。
            if not sanitized or sanitized != content:
                return

            spoken_messages.add(content)
            spoken_count += 1
            await UniMessage.text(content).send()
            return

        if event.type in {"thinking", "subagent_start", "tool_call"}:
            await UniMessage.text(event.message).send()

    return reporter


async def _process_agent_request(context: AgentRequestContext, history_messages: list[dict] | None = None) -> bool:  # noqa: C901
    messages = list(history_messages or [])
    history_prefix_count = len(messages)
    combined_text = context.text.strip() or EMPTY_CURRENT_MESSAGE_PROMPT
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
    reply_to = context.reply_to
    if reply_to is None and context.quoted_text:
        # Compatibility for direct/internal callers that still pass the former
        # human-readable quote string.
        reply_to = {
            "schema": "frontier.qq_message_ref.v1",
            "message_id": None,
            "sender": None,
            "content": context.quoted_text.strip(),
        }
    current_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": serialize_agent_payload(
                build_agent_message_payload(
                    timestamp_ms=context.msg_time,
                    msg_id=context.event_id,
                    user_id=context.user_id,
                    group_id=context.group_id,
                    user_name=context.user_name,
                    user_nickname=context.user_nickname,
                    user_card=context.user_card,
                    role="user",
                    is_current=True,
                    content=combined_text,
                    reply_to=reply_to,
                )
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
    messages.append({"role": "user", "content": current_content})
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
        progress_reporter=_chat_progress_reporter(context.group_id),
        user_text=context.text,
        conversation_history=(
            ConversationHistoryRequest(
                database=messages_db,
                scope=ConversationScope.from_ids(context.user_id, context.group_id),
                before_time=context.msg_time,
                prefix_message_count=history_prefix_count,
            )
            if EnvConfig.CONVERSATION_MEMORY_ENABLED
            and all(
                hasattr(messages_db, name)
                for name in ("latest_conversation_summary", "select_context_page", "prepare_message_records")
            )
            else None
        ),
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
            # 私聊按对端 user_id 建立会话范围；群聊仍保留真实机器人发送者 ID。
            user_id=int(context.user_id) if context.group_id is None else int(context.event.self_id),
            group_id=context.group_id,
            user_name="Assistant",
            role="assistant",
            content=outgoing_message_content(response["messages"][-1]),
        )
        await _schedule_conversation_compaction(context.user_id, context.group_id)
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

    scheduler.add_job(
        run_daily_cache_cleanup,
        "cron",
        id=CACHE_CLEANUP_JOB_ID,
        hour=4,
        minute=0,
        timezone="Asia/Shanghai",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )


async def run_daily_cache_cleanup() -> None:
    """Run bounded cache maintenance once per day."""
    if EnvConfig.IMAGE_AUTO_CLEANUP:
        try:
            cleaned_attachments = await messages_db.cleanup_expired_attachments()
            if cleaned_attachments:
                logger.info("每日清理过期消息附件: %s", cleaned_attachments)
        except Exception as exc:
            logger.warning("每日消息附件清理失败: %s: %s", type(exc).__name__, exc)

    try:
        cleaned_scopes = await acp_service.cleanup_cache()
        if cleaned_scopes:
            logger.info("每日清理 ACP 缓存 scope: %s", cleaned_scopes)
    except Exception as exc:
        logger.warning("每日 ACP 缓存清理失败: %s: %s", type(exc).__name__, exc)


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
    user_name, user_nickname, user_card = sender_names_from_milky_message(event.data)
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
    reply_payload = None
    if reply_seq:
        reply_payload, _ = await build_reply_context(
            bot,
            event,
            reply_seq,
            group_id,
            messages_db,
            load_images=False,
        )
        if reply_payload:
            current_text = _remove_structured_reply_marker(current_text, reply_seq)
    if video_downloaders and "[视频" not in current_text:
        current_text = f"{current_text}\n{' '.join('[视频]' for _ in video_downloaders)}".strip()
    if audio_downloaders and "[语音" not in current_text:
        current_text = f"{current_text}\n{' '.join('[语音]' for _ in audio_downloaders)}".strip()
    if not current_text and not reply_payload:
        if not event.is_tome():
            await common.finish()
        else:
            current_text = ""

    msg_time = int(time.time() * 1000)
    text = current_text.strip()

    # ── Phase 2: 存储消息文本与结构化元数据 + 快速网关检查 ──
    await messages_db.insert(
        time=msg_time,
        msg_id=event_id,
        user_id=int(user_id),
        group_id=group_id,
        user_name=user_name,
        user_nickname=user_nickname,
        user_card=user_card,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
        reply_context_json=serialize_agent_payload(reply_payload) if reply_payload else None,
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
        await _schedule_conversation_compaction(user_id, group_id)
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
        (images, audio, videos), staged_files, (agent_reply_payload, quoted_images) = await asyncio.gather(
            media_task,
            files_task,
            quote_task,
        )
    else:
        (images, audio, videos), staged_files = await asyncio.gather(media_task, files_task)
        agent_reply_payload, quoted_images = None, []

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
    quoted_content = str((agent_reply_payload or {}).get("content", ""))
    if EnvConfig.CONTENT_CHECK_ENABLED:
        risk_check = await message_check(f"{agent_text}\n{quoted_content}".strip(), quoted_images + images)
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
        user_nickname=user_nickname,
        user_card=user_card,
        event_id=event_id,
        group_id=group_id,
        msg_time=msg_time,
        text=agent_text,
        quoted_images=quoted_images,
        images=images,
        audio=audio,
        videos=videos,
        reply_to=agent_reply_payload,
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
