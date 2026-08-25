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

from utils.agents import (
    FrontierCognitive,
    ProgressEvent,
    ProgressReporter,
    agent_thread_id,
    conversation_workspace_key,
    run_serialized,
)
from utils.agents.acp import acp_service
from utils.agents.conversation_memory import (
    ConversationHistoryRequest,
    ConversationMemoryService,
    ConversationScope,
)
from utils.agents.message_envelope import (
    build_agent_attachment_payload,
    build_agent_message_payload,
    serialize_agent_payload,
)
from utils.agents.message_envelope import content_for_persisted_images as _remove_attached_image_placeholders
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.media import resolve_media, standard_media_block
from utils.message import (
    cleanup_staged_message_files,
    download_media,
    extract_message_files,
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
from utils.reply_context import (
    build_reply_context,
    reply_seq_from_segments,
    segments_directly_mention_user,
    sender_names_from_milky_message,
)

messages_db = MessageDatabase()
conversation_memory_service = ConversationMemoryService(messages_db)
f_cognitive = FrontierCognitive()
driver = get_driver()

common = on_message(priority=10)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_CLEANUP_JOB_ID = "frontier_daily_cache_cleanup"


async def _schedule_conversation_compaction(
    user_id: int | str,
    group_id: int | None,
    *,
    raw_budget: int | None = None,
) -> None:
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
            raw_budget=raw_budget,
        )
    except Exception as exc:
        logger.warning("会话压缩调度失败（不影响回复）: %s: %s", type(exc).__name__, exc)


@dataclass(slots=True)
class AgentRequestContext:
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
    audio: list[bytes] = field(default_factory=list)
    attachments: list[dict[str, object]] = field(default_factory=list)
    user_nickname: str | None = None
    user_card: str | None = None
    reply_to: dict[str, object] | None = None
    direct_mention: bool = False


def _agent_workspace_key(user_id: str, group_id: int | None) -> str:
    return conversation_workspace_key(user_id, group_id)


def _agent_memory_dir(user_id: str, group_id: int | None) -> Path:
    working_dir = Path(getattr(f_cognitive, "working_dir", os.path.join(os.getcwd(), "cache", "sandbox")))
    return working_dir / "memory" / _agent_workspace_key(user_id, group_id)


async def _collect_incoming_assets(
    media_coro,
    files_coro,
    quote_coro=None,
):
    coroutines = [media_coro, files_coro]
    if quote_coro is not None:
        coroutines.append(quote_coro)
    results = await asyncio.gather(*coroutines, return_exceptions=True)
    staged_files = results[1] if isinstance(results[1], list) else []
    if phase_error := next((result for result in results if isinstance(result, BaseException)), None):
        cleanup_staged_message_files(staged_files)
        raise phase_error
    quote_result = results[2] if quote_coro is not None else (None, [])
    return results[0], staged_files, quote_result


def _group_member_role(event: MessageEvent) -> str | None:
    member = getattr(getattr(event, "data", None), "group_member", None)
    role = getattr(member, "role", None)
    if role in (None, ""):
        return None
    return str(role)


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
    combined_text = context.text.strip()
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
                    content=combined_text,
                    attachments=context.attachments,
                    reply_to=context.reply_to,
                    bot_user_id=getattr(context.event, "self_id", None),
                    directly_mentions_bot=context.direct_mention,
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
    messages.append(
        {
            "role": "user",
            "content": current_content[0]["text"] if len(current_content) == 1 else current_content,
        }
    )
    capability = EnvConfig.AGENT_CAPABILITY

    result = await f_cognitive.chat_agent(
        messages,
        context.user_id,
        context.user_name,
        capability,
        group_id=context.group_id,
        image_inputs=context.quoted_images + context.images,
        audio_inputs=context.audio,
        video_inputs=context.videos,
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
            sender_user_id=int(context.event.self_id),
            group_id=context.group_id,
            user_name="Assistant",
            role="assistant",
            content=outgoing_message_content(response["messages"][-1]),
            bot_user_id=int(context.event.self_id),
        )
        await send_messages(context.group_id, context.event_id, response)
        await _schedule_conversation_compaction(
            context.user_id,
            context.group_id,
            raw_budget=result.get("history_raw_budget"),
        )
    else:
        await UniMessage.text(response["messages"]).send()
    return True


async def _run_agent_turn(
    *,
    bot: Any,
    context: AgentRequestContext,
    history_messages: list[dict],
    previous_reply_payload: dict[str, object] | None,
    fetched_reply_payload: dict[str, object] | None,
    original_text: str,
) -> None:
    finalize_message_context = getattr(messages_db, "finalize_message_context", None)
    if callable(finalize_message_context) and context.reply_to != previous_reply_payload:
        try:
            await finalize_message_context(
                time=context.msg_time,
                reply_context_json=(
                    serialize_agent_payload(context.reply_to) if context.reply_to else None
                ),
            )
        except Exception as exc:
            logger.warning("消息上下文定稿失败（不影响回复）: %s: %s", type(exc).__name__, exc)

    quoted_content = str((fetched_reply_payload or {}).get("content", ""))
    risk_check = (
        await message_check(
            f"{context.text}\n{quoted_content}".strip(),
            context.quoted_images + context.images,
        )
        if EnvConfig.CONTENT_CHECK_ENABLED
        else "Safe"
    )
    reaction = {"Safe": "32", "Controversial": "212", "Unsafe": "26"}.get(risk_check)
    reaction_added = False
    if context.group_id is not None and reaction is not None:
        try:
            await bot.send_group_message_reaction(
                group_id=context.group_id,
                message_seq=context.event_id,
                reaction=reaction,
                is_add=True,
            )
            reaction_added = True
        except Exception as exc:
            logger.warning("发送群消息处理反应失败: %s: %s", type(exc).__name__, exc)

    from utils.ens_gate import _ens_caller_allowed, _ens_prefix

    cleaned = original_text.strip().lstrip("/")
    is_ens_msg = cleaned[:3].lower() == "vep" or cleaned[:2].lower() == "ve"
    _ens_caller_allowed.set(is_ens_msg)
    if cleaned[:3].lower() == "vep":
        _ens_prefix.set("vep")
    elif cleaned[:2].lower() == "ve":
        _ens_prefix.set("ve")
    else:
        _ens_prefix.set("")

    try:
        thread_id = agent_thread_id(context.user_id, context.group_id)
        await run_serialized(
            str(thread_id),
            _process_agent_request(context, history_messages),
        )
    finally:
        if context.group_id is not None and reaction_added:
            try:
                await bot.send_group_message_reaction(
                    group_id=context.group_id,
                    message_seq=context.event_id,
                    reaction=reaction,
                    is_add=False,
                )
            except Exception as exc:
                logger.warning(
                    "移除群消息处理反应失败 用户%s 群%s: %s",
                    context.user_id,
                    context.group_id,
                    exc,
                )


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
    direct_mention = segments_directly_mention_user(event.data.segments, event.self_id)

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
        sender_user_id=int(user_id),
        group_id=group_id,
        user_name=user_name,
        user_nickname=user_nickname,
        user_card=user_card,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
        bot_user_id=int(event.self_id),
        directly_mentions_bot=direct_mention,
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
        message_time=msg_time,
        user_id=user_id,
        group_id=group_id,
    )
    if reply_seq:
        quote_task = build_reply_context(bot, event, reply_seq, group_id, messages_db)
        (images, audio, videos), staged_files, (agent_reply_payload, quoted_images) = await _collect_incoming_assets(
            media_task,
            files_task,
            quote_task,
        )
    else:
        (images, audio, videos), staged_files, _quote_result = await _collect_incoming_assets(
            media_task,
            files_task,
        )
        agent_reply_payload, quoted_images = None, []
    resolved_reply_payload = agent_reply_payload or reply_payload

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

    persisted_image_count = sum(
        1 for attachment in persisted_attachments if getattr(attachment, "kind", None) == "image"
    )
    agent_text = _remove_attached_image_placeholders(current_text, persisted_image_count).strip()

    indexed_staged_paths: set[Path] = set()
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
            else:
                indexed_staged_paths.add(Path(staged_file.local_path))
    unindexed_staged_files = [
        staged_file
        for staged_file in staged_files
        if Path(staged_file.local_path) not in indexed_staged_paths
    ]

    try:
        attachment_refs = [
            dict(
                build_agent_attachment_payload(
                    kind=attachment.kind,
                    mime_type=attachment.mime_type,
                    file_name=attachment.file_name,
                    path=attachment.virtual_path,
                )
            )
            for attachment in persisted_attachments
        ]
        attachment_refs.extend(
            dict(
                build_agent_attachment_payload(
                    kind="file",
                    mime_type=staged_file.mime_type,
                    file_name=staged_file.file_name,
                    path=staged_file.virtual_path,
                )
            )
            # The path remains readable for this turn even when indexing failed.
            for staged_file in staged_files
        )
        context = AgentRequestContext(
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
            attachments=attachment_refs,
            # Persist and reuse the post-download snapshot so quoted media
            # semantics stay identical when this event becomes history.
            reply_to=resolved_reply_payload,
            direct_mention=direct_mention,
        )
        await _run_agent_turn(
            bot=bot,
            context=context,
            history_messages=messages,
            previous_reply_payload=reply_payload,
            fetched_reply_payload=agent_reply_payload,
            original_text=text,
        )
    finally:
        cleanup_staged_message_files(unindexed_staged_files)
