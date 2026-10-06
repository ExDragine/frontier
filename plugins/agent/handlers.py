# ruff: noqa: E402

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from langchain.messages import AIMessage
from nonebot import get_bot, get_driver, logger, on_message, on_notice
from nonebot.adapters.milky.event import GroupDisbandEvent, MessageEvent
from nonebot_plugin_apscheduler import scheduler
from pydantic import BaseModel

from utils.agent_orchestration import ConversationOrchestrator, TurnStatus
from utils.agent_protocol import (
    AgentRequest,
    AgentResponse,
    ConversationRef,
    DeliveryReceipt,
    DeliveryStatus,
    GateDecision,
    MessageRef,
)
from utils.agents import (
    FrontierCognitive,
    ProgressEvent,
    ProgressReporter,
    conversation_workspace_key,
    run_serialized,
)
from utils.agents.message_envelope import (
    build_agent_attachment_payload,
    serialize_agent_payload,
)
from utils.agents.message_envelope import content_for_persisted_images as _remove_attached_image_placeholders
from utils.agents.neutral_core import FrontierAgentCore
from utils.agents.runtime_gateway import FrontierAgentRuntime
from utils.agents.sessions import HistoryBoundary, SessionKey, TurnLease, session_manager
from utils.alconna import UniMessage
from utils.configs import EnvConfig
from utils.database import MessageDatabase
from utils.delivery import DeliveryResult
from utils.media import resolve_media
from utils.message import (
    download_media,
    message_check,
    message_extract,
    outgoing_message_content,  # noqa: F401  # re-exported: tests and callers read it from this module
    sanitize_outgoing_text,
    send_artifacts,
    send_messages,
)
from utils.signal_llm import signal_structured

from .adapters import (
    QqDelivery,
    QqHistoryStore,
    QqMessageAdapter,
    QqReplyPolicy,
    QqToolProvider,
)
from .attachments import cleanup_staged_message_files, extract_message_files, stage_message_files
from .gateway import message_gateway
from .message_normalizer import NORMALIZED_VERSION, normalize_segments
from .reply_context import (
    build_reply_context,
    hydrate_recent_media_context,
    reply_seq_from_segments,
    requests_recent_media,
    segments_directly_mention_user,
    sender_names_from_milky_message,
)

messages_db = MessageDatabase()


async def _is_group_disband(event) -> bool:
    return isinstance(event, GroupDisbandEvent)


group_disband = on_notice(rule=_is_group_disband, priority=10, block=False)


@group_disband.handle()
async def handle_group_disband(event: GroupDisbandEvent):
    # A notice is not a user request. Preserve history and workspace for retrieval.
    logger.info("Milky 群已解散: group_id={} operator_id={}", event.data.group_id, event.data.operator_id)
f_cognitive = FrontierCognitive()
driver = get_driver()

common = on_message(priority=10)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_CLEANUP_JOB_ID = "frontier_daily_cache_cleanup"


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
    recent_images: list[bytes] = field(default_factory=list)
    attachments: list[dict[str, object]] = field(default_factory=list)
    current_attachments: list[dict[str, object]] = field(default_factory=list)
    recent_attachments: list[dict[str, object]] = field(default_factory=list)
    user_nickname: str | None = None
    user_card: str | None = None
    reply_to: dict[str, object] | None = None
    reply_seq: int | None = None
    direct_mention: bool = False
    message_id: int | None = None


def _agent_workspace_key(user_id: str, group_id: int | None) -> str:
    return conversation_workspace_key(user_id, group_id)


def _qq_reply_ref(context: AgentRequestContext, conversation: ConversationRef) -> MessageRef | None:
    """Build an opaque reply reference without exposing the legacy payload."""

    message_id = None
    if isinstance(context.reply_to, dict):
        message_id = context.reply_to.get("message_id")
    if message_id is None:
        message_id = context.reply_seq
    if message_id is None:
        return None
    return MessageRef(platform="qq", conversation=conversation, message_id=str(message_id))


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
    tasks = [asyncio.ensure_future(coroutine) for coroutine in coroutines]
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except BaseException:
        # A completed files task can outlive cancellation of the other downloads.
        # Settle every task, including any in-flight disk write, before cleanup.
        for task in tasks:
            task.cancel()
        settled = await asyncio.gather(*tasks, return_exceptions=True)
        cleanup_staged_message_files(settled[1] if isinstance(settled[1], list) else [])
        raise
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


def _allows_silent_reply(context: AgentRequestContext) -> bool:
    """Only opportunistic, non-addressed group turns may end silently."""
    if context.group_id is None or context.direct_mention:
        return False
    is_tome = getattr(context.event, "is_tome", None)
    return not bool(is_tome()) if callable(is_tome) else True


def _remove_structured_reply_marker(text: str, reply_seq: int | None) -> str:
    """Drop the legacy text marker once reply identity is carried structurally."""
    if reply_seq is None or not text:
        return text
    marker = f"[回复消息:{reply_seq}]"
    lines = text.splitlines()
    if lines and lines[0].strip() == marker:
        return "\n".join(lines[1:]).strip()
    return text


class _GroupProgressIntent(BaseModel):
    intent: Literal["web", "memory", "work"]


_GROUP_PROGRESS_MESSAGES = {
    "web": "我先查一下相关资料，核对后告诉你。",
    "memory": "我回看一下前面的信息，整理后回复你。",
    "work": "我先处理一下，马上给你结果。",
}


def _quick_group_progress_message(event: ProgressEvent) -> str | None:
    """Classify obvious tool events without adding another model round trip."""
    detail = event.detail or {}
    tool_name = str(detail.get("tool_name") or "").lower()
    message = event.message.lower()
    if any(keyword in f"{tool_name} {message}" for keyword in ("web", "search", "news", "exa", "tavily")):
        return _GROUP_PROGRESS_MESSAGES["web"]
    if any(keyword in f"{tool_name} {message}" for keyword in ("memory", "history", "conversation", "recall")):
        return _GROUP_PROGRESS_MESSAGES["memory"]
    return None


async def _group_progress_message(event: ProgressEvent) -> str | None:
    """Use one cheap Signal call to turn the first progress event into a status."""

    try:
        quick_message = _quick_group_progress_message(event)
        if quick_message:
            return quick_message
        result = await asyncio.wait_for(
            signal_structured(
                """判断 Agent 当前正在做哪类工作，只返回 JSON。web 表示查询网页、新闻或外部资料；
memory 表示回忆聊天记录、读取记忆或上下文；work 表示计算、调用业务工具、生成媒体或其他处理。""",
                f"事件类型：{event.type}\n当前动作：{event.message}",
                _GroupProgressIntent,
                temperature=0,
            ),
            timeout=2.5,
        )
    except Exception as exc:
        logger.debug("群聊进度 Signal 失败: {}", type(exc).__name__)
        return None
    return _GROUP_PROGRESS_MESSAGES.get(result.intent)


def _chat_progress_reporter(group_id: int | None) -> ProgressReporter:  # noqa: C901
    """构造会话级进度消费者；群聊只发一次 Signal 状态，私聊保留有限提示。"""
    spoken_messages: set[str] = set()
    spoken_count = 0
    max_spoken_messages = 2
    group_signal_started = False
    group_signal_sent = False
    group_signal_lock = asyncio.Lock()
    group_signal_task: asyncio.Task | None = None

    async def send_group_status(event: ProgressEvent) -> None:
        nonlocal group_signal_sent
        try:
            message = await asyncio.wait_for(_group_progress_message(event), timeout=0.35)
        except TimeoutError:
            message = _GROUP_PROGRESS_MESSAGES["work"]
        if not message:
            return
        async with group_signal_lock:
            if group_signal_sent:
                return
            group_signal_sent = True
            try:
                await UniMessage.text(message).send()
            except Exception as exc:
                group_signal_sent = False
                logger.debug("群聊进度状态发送失败: {}", type(exc).__name__)

    async def reporter(event: ProgressEvent) -> None:  # noqa: C901
        nonlocal spoken_count

        if group_id is not None:
            nonlocal group_signal_started, group_signal_task
            if event.type == "done":
                if group_signal_task is not None and not group_signal_task.done():
                    group_signal_task.cancel()
                return
            if group_signal_sent:
                return
            if event.type == "thinking":
                if not group_signal_started:
                    group_signal_started = True
                    # Give the model a short window to reveal a more useful
                    # tool-call event before falling back to generic wording.
                    async def delayed_status() -> None:
                        await asyncio.sleep(0.08)
                        await send_group_status(event)

                    group_signal_task = asyncio.create_task(
                        delayed_status(), name="frontier-group-progress-signal"
                    )
                return
            if event.type in {"tool_call_start", "tool_call", "subagent_start"}:
                if group_signal_task is not None and not group_signal_task.done():
                    group_signal_task.cancel()
                group_signal_started = True
                group_signal_task = asyncio.create_task(
                    send_group_status(event), name="frontier-group-progress-signal"
                )
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


async def _settle_session(lease: TurnLease | None, **kwargs) -> None:
    if lease is None or lease.finished:
        return
    try:
        await session_manager.finish(lease, **kwargs)
    except Exception as exc:
        # Transport success must never be retried because cache maintenance failed.
        logger.warning("会话状态结算失败: {}", type(exc).__name__)


def _qq_neutral_eligible(context: AgentRequestContext, _session_turn: TurnLease | None = None) -> bool:
    """Return whether the normalized QQ event contains an Agent turn.

    Media, files, quotes, and session leases are all represented by the
    neutral message contract.  The old canary-only restrictions are gone; an
    unresolved quote is still represented by its opaque message reference so
    the Agent can decide how to handle it.
    """

    return bool(context.text.strip() or context.reply_seq is not None or context.direct_mention)


class _QqNeutralCore:
    """Sanitize the neutral response before the QQ delivery port sends it."""

    def __init__(self, core: FrontierAgentCore) -> None:
        self._core = core

    async def run(self, request: AgentRequest, *, tools=(), progress_reporter=None) -> AgentResponse:
        if progress_reporter is None:
            response = await self._core.run(request, tools=tools)
        else:
            response = await self._core.run(request, tools=tools, progress_reporter=progress_reporter)
        sanitized = await sanitize_outgoing_text(response.text)
        sanitized_text = sanitized or ""
        if sanitized_text == response.text:
            return response
        return AgentResponse(
            text=sanitized_text,
            artifacts=response.artifacts,
            status=response.status,
            should_reply=response.should_reply,
            run_id=response.run_id,
            usage=response.usage,
        )


class _QqNeutralDelivery(QqDelivery):
    """Reject empty turns before they reach the QQ delivery port."""

    async def send(self, target: ConversationRef, response: AgentResponse) -> DeliveryReceipt:
        if not response.text.strip() and not response.artifacts:
            return DeliveryReceipt(DeliveryStatus.FAILED, errors=("empty_response",))
        return await super().send(target, response)


async def _send_qq_neutral_artifacts(_target: ConversationRef, artifacts) -> DeliveryResult:
    """Convert neutral media to QQ messages at the platform boundary."""

    messages = []
    for artifact in artifacts:
        source = {}
        if getattr(artifact, "data", None):
            source["raw"] = artifact.data
        elif getattr(artifact, "url", None):
            source["url"] = artifact.url
        elif getattr(artifact, "path", None):
            source["path"] = artifact.path
        else:
            return DeliveryResult(attempted=1, errors=("neutral_artifact",))
        media_kwargs = {"mimetype": artifact.mime_type} if getattr(artifact, "mime_type", None) else {}
        name = getattr(artifact, "name", None)
        if artifact.kind == "image":
            messages.append(UniMessage.image(**source, **media_kwargs))
        elif artifact.kind == "audio":
            messages.append(UniMessage.audio(**source, **media_kwargs))
        elif artifact.kind == "video":
            messages.append(UniMessage.video(**source, **media_kwargs))
        elif artifact.kind == "file":
            kwargs = {**source, **media_kwargs}
            if name:
                kwargs["name"] = name
            messages.append(UniMessage.file(**kwargs))
        else:
            return DeliveryResult(attempted=1, errors=("neutral_artifact",))
    return await send_artifacts(messages)


async def _qq_reply_id_for_context(context: AgentRequestContext) -> int | None:
    """Reuse the delayed-group reply heuristic for neutral sends."""

    if context.group_id is None or time.time() * 1000 - context.msg_time < 10_000:
        return None
    count_intervening = getattr(messages_db, "count_intervening_group_messages", None)
    if not callable(count_intervening):
        return None
    intervening_messages = await count_intervening(
        group_id=context.group_id,
        bot_user_id=int(context.event.self_id),
        user_id=int(context.user_id),
        after_time=context.msg_time,
        after_message_id=context.message_id,
    )
    return context.event_id if intervening_messages >= 5 else None


async def _send_qq_neutral_notice(context: AgentRequestContext, text: str) -> bool:
    """Send one bounded neutral-path failure notice without rerunning the Agent."""

    try:
        reply_id = await _qq_reply_id_for_context(context)
        delivery = await send_messages(
            context.group_id,
            reply_id,
            {"messages": [AIMessage(content=text)]},
        )
    except Exception as exc:
        logger.warning("QQ 中立路径错误提示发送失败: {}", type(exc).__name__)
        return False
    return delivery.sent > 0


async def _settle_qq_neutral_session(lease: TurnLease | None, outcome) -> None:
    """Settle a session lease after the neutral orchestrator owns delivery."""

    if lease is None:
        return
    if outcome.status == TurnStatus.SILENT:
        await _settle_session(lease, silent=True)
        return
    receipt = outcome.receipt
    if receipt is None or receipt.status != DeliveryStatus.DELIVERED:
        return
    message_id = None
    if receipt.message_refs:
        try:
            # QqDelivery emits artifact receipts before the final text
            # receipt. The text message is the session history boundary.
            message_id = int(receipt.message_refs[-1].message_id)
        except (TypeError, ValueError):
            message_id = None
    await _settle_session(
        lease,
        delivered=True,
        delivered_at=int(time.time() * 1000),
        message_id=message_id,
        content=outcome.response.text if outcome.response is not None else "",
    )


async def _run_qq_neutral(
    context: AgentRequestContext,
    history_messages: list[dict[str, Any]],
    session_turn: TurnLease | None = None,
) -> tuple[bool, bool]:
    """Run one QQ turn through the platform-neutral application boundary.

    The tuple is ``(handled, result)`` for compatibility with the staged
    caller.  The final path never retries the legacy Agent after the neutral
    boundary has been entered.
    """

    adapter = QqMessageAdapter(getattr(context.event, "self_id", ""))
    conversation = adapter.conversation(group_id=context.group_id, user_id=context.user_id)
    message = adapter.text_message(
        message_id=context.event_id,
        group_id=context.group_id,
        user_id=context.user_id,
        user_name=context.user_name,
        text=context.text or ("[用户叫了你一声]" if context.direct_mention else ""),
        created_at=datetime.fromtimestamp(context.msg_time / 1000, tz=UTC),
        role=_group_member_role(context.event),
        mentions_agent=context.direct_mention,
        images=context.images,
        audio=context.audio,
        videos=context.videos,
        attachments=context.current_attachments or context.attachments,
        recent_images=context.recent_images,
        recent_attachments=context.recent_attachments,
        reply_to=_qq_reply_ref(context, conversation),
        quoted_payload=context.reply_to,
        quoted_images=context.quoted_images,
    )

    async def load_history(_query):
        # The gateway has already prepared the bounded, pre-current history.
        # Reusing that snapshot avoids a second database query and preserves
        # the existing before-time semantics.
        return history_messages

    async def allow_gateway_result(_message, _history):
        return GateDecision(True, reason="legacy_gateway_passed")

    async def send_text(_target: ConversationRef, text: str):
        reply_id = await _qq_reply_id_for_context(context)
        return await send_messages(
            context.group_id,
            reply_id,
            {"messages": [AIMessage(content=text)]},
        )

    outcome = await ConversationOrchestrator(
        _QqNeutralCore(FrontierAgentCore(FrontierAgentRuntime(cognitive=f_cognitive)))
    ).handle(
        message,
        policy=QqReplyPolicy(allow_gateway_result),
        history=QqHistoryStore(database=messages_db, loader=load_history),
        delivery=_QqNeutralDelivery(text_sender=send_text, artifact_sender=_send_qq_neutral_artifacts),
        tools=QqToolProvider(),
        workspace_key=_agent_workspace_key(context.user_id, context.group_id),
        capabilities=frozenset({"platform:qq", "qq:tools"}),
        execution_profile=EnvConfig.AGENT_CAPABILITY,
        allow_silent_reply=_allows_silent_reply(context),
        session_turn=session_turn,
        progress_reporter=_chat_progress_reporter(context.group_id),
    )
    if outcome.status in {TurnStatus.DELIVERED, TurnStatus.HISTORY_APPEND_FAILED}:
        await _settle_qq_neutral_session(session_turn, outcome)
        return True, outcome.receipt is not None and outcome.receipt.status == DeliveryStatus.DELIVERED
    if outcome.status == TurnStatus.SILENT:
        await _settle_qq_neutral_session(session_turn, outcome)
        return True, False
    if outcome.status == TurnStatus.GATED:
        await _settle_session(session_turn, silent=True)
        return True, outcome.status == TurnStatus.DELIVERED
    if outcome.status in {TurnStatus.HISTORY_FAILED, TurnStatus.GATE_FAILED}:
        # History and gate are already prepared by the QQ entry point.  If a
        # port still fails here, report it once instead of retrying the legacy
        # Agent and risking duplicate side effects.
        logger.warning("QQ 中立路径前置阶段失败: {}", outcome.error or outcome.status)
        return True, await _send_qq_neutral_notice(context, "本轮上下文准备失败，请稍后重试。")
    if outcome.status == TurnStatus.AGENT_FAILED:
        # The legacy runtime normally exposes a fixed user-facing error
        # message.  Deliver it once after the neutral call fails; rerunning the
        # old graph could duplicate a tool side effect.
        notice = (
            outcome.response.text.strip()
            if outcome.response is not None and outcome.response.text.strip()
            else "本轮处理失败，请稍后重试。"
        )
        return True, await _send_qq_neutral_notice(context, notice)
    # A transport failure is already the failed user-facing operation.  Do
    # not issue a second message through the same failing channel; the queue
    # caller records the failure and the next inbound turn can retry normally.
    logger.warning("QQ 中立路径投递失败: {}", outcome.error or outcome.status)
    return True, False


async def _process_agent_request(
    context: AgentRequestContext,
    history_messages: list[dict[str, Any]] | None = None,
) -> bool:
    lease = None
    bot_id = getattr(context.event, "self_id", None)
    use_session_history = EnvConfig.SESSIONS.enabled and context.message_id is not None and bot_id is not None
    if use_session_history:
        async def begin():
            return session_manager.begin(
                SessionKey(str(bot_id), str(context.user_id), context.group_id),
                HistoryBoundary(cast(int, context.message_id), context.msg_time),
                EnvConfig.SESSIONS, EnvConfig.REVISION,
            )
        try:
            lease = await run_serialized(f"workspace:{_agent_workspace_key(context.user_id, context.group_id)}", begin)
        except Exception as exc:
            # No graph/tool has started: a cache maintenance failure can safely
            # fall back to the original execution with the same scoped history.
            session_manager.metrics["initialization_fallback"] += 1
            logger.warning("会话缓存初始化失败，使用历史上下文: {}", type(exc).__name__)
    try:
        if use_session_history:
            started = time.monotonic()
            history_messages = await messages_db.prepare_session_history(
                bot_user_id=int(bot_id), user_id=int(context.user_id), group_id=context.group_id,
                before_time=context.msg_time, before_message_id=context.message_id,
                query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
                after_message_id=lease.entry.history_cursor if lease is not None and lease.hot else None,
            )
            if lease is not None:
                lease.rebuild_seconds = time.monotonic() - started
        return await _execute_agent_request(context, history_messages, lease)
    finally:
        # Covers cancellation, tool/model failures, early returns and sender errors.
        await _settle_session(lease)


async def _execute_agent_request(
    context: AgentRequestContext,
    history_messages: list[dict[str, Any]] | None = None,
    session_turn: TurnLease | None = None,
) -> bool:
    """Execute every QQ turn through the neutral application boundary.

    The legacy implementation remains available as an explicit compatibility
    helper for isolated integrations, but the production QQ handler no longer
    selects it based on a canary flag or a media/session subset.
    """

    if not _qq_neutral_eligible(context):
        logger.info("忽略没有文本、引用或直接提及的 QQ 消息: event_id={}", context.event_id)
        await _settle_session(session_turn, silent=True)
        return False
    handled, result = await _run_qq_neutral(
        context,
        list(history_messages or []),
        session_turn=session_turn,
    )
    if handled:
        return result
    # The neutral runner owns the request once called.  This branch is kept
    # defensive for injected test doubles and must never rerun the legacy
    # graph after a model/tool call.
    return False


async def _process_queued_agent_request(context: AgentRequestContext, history_messages: list[dict[str, Any]]) -> None:
    started = False

    async def process() -> bool:
        nonlocal started
        started = True
        return await _process_agent_request(context, history_messages)

    try:
        # Delivery includes history persistence; cognitive has a separate workspace
        # execution lock shared with scheduled tasks and other entry points.
        delivery_key = f"delivery:{_agent_workspace_key(context.user_id, context.group_id)}"
        await run_serialized(
            delivery_key,
            process(),
            timeout=EnvConfig.AGENT_JOB_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        logger.warning("会话回复超时: group_id={} user_id={} started={}", context.group_id, context.user_id, started)
        notice = "本轮处理超时，请稍后重试。" if started else "等待处理超时，本轮请求尚未开始，请稍后重试。"
        try:
            async with asyncio.timeout(15):
                delivery = await send_messages(
                    context.group_id, context.event_id, {"messages": [AIMessage(content=notice)]}
                )
                if delivery.errors:
                    logger.warning("会话超时提示未送达: {}", delivery.errors)
        except Exception as exc:
            logger.warning("会话超时提示发送失败: {}", type(exc).__name__)


async def _run_agent_turn(
    *,
    bot: Any,
    context: AgentRequestContext,
    history_messages: list[dict[str, Any]],
    previous_reply_payload: dict[str, object] | None,
    fetched_reply_payload: dict[str, object] | None,
    original_text: str,
) -> None:
    finalize_message_context = getattr(messages_db, "finalize_message_context", None)
    if callable(finalize_message_context) and context.reply_to != previous_reply_payload:
        try:
            await finalize_message_context(
                time=context.msg_time,
                **({"message_id": context.message_id} if context.message_id is not None else {}),
                reply_context_json=(serialize_agent_payload(context.reply_to) if context.reply_to else None),
            )
        except Exception as exc:
            logger.warning("消息上下文定稿失败（不影响回复）: {}: {}", type(exc).__name__, exc)

    quoted_content = str((fetched_reply_payload or {}).get("content", ""))
    risk_check = (
        await message_check(
            f"{context.text}\n{quoted_content}".strip(),
            context.quoted_images + context.recent_images + context.images,
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
            logger.warning("发送群消息处理反应失败: {}: {}", type(exc).__name__, exc)

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
        await _process_queued_agent_request(context, history_messages)
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
                    "移除群消息处理反应失败 用户{} 群{}: {}",
                    context.user_id,
                    context.group_id,
                    exc,
                )


@driver.on_shutdown
async def on_shutdown():
    await session_manager.close()
    from tools.ens_professional import clear_ens_cache as clear_ens_professional_cache

    clear_ens_professional_cache()
    from utils.browser_capture import close_browser
    from utils.http_client import aclose_all

    await close_browser()
    await aclose_all()


@driver.on_startup
async def on_startup():
    session_manager.start()
    if EnvConfig.IMAGE_AUTO_CLEANUP:
        try:
            cleaned_attachments = await messages_db.cleanup_expired_attachments()
            if cleaned_attachments:
                logger.info("已清理过期消息附件: {}", cleaned_attachments)
        except Exception as exc:
            logger.warning("消息附件维护失败: {}: {}", type(exc).__name__, exc)

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
                logger.info("每日清理过期消息附件: {}", cleaned_attachments)
        except Exception as exc:
            logger.warning("每日消息附件清理失败: {}: {}", type(exc).__name__, exc)


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
            workspace_key=_agent_workspace_key(user_id, group_id),
            memory_dir=_agent_memory_dir(user_id, group_id),
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
    inserted = await messages_db.insert(
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
    if inserted is not None and not inserted.inserted:
        logger.info("忽略已处理的平台消息: group_id={} message_seq={}", group_id, event_id)
        await common.finish()
    message_id = inserted.message_id if inserted is not None else None
    message_identity = {"message_id": message_id} if message_id is not None else {}
    if normalized_message.derived_messages:
        await messages_db.replace_derived_messages(
            **({"parent_message_id": message_id} if message_id is not None else {}),
            parent_msg_time=msg_time,
            parent_msg_id=event_id,
            user_id=int(user_id),
            group_id=group_id,
            role="user" if user_id != str(event.self_id) else "assistant",
            derived_messages=normalized_message.derived_messages,
            normalized_version=NORMALIZED_VERSION,
        )

    gateway_messages = await messages_db.prepare_message(
        int(user_id),
        group_id,
        query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS,
        before_time=msg_time,
    )

    if not await message_gateway(event, gateway_messages):
        await common.finish()

    # ── Phase 3: 网关通过后才下载当前消息及引用消息中的媒体 ──
    media_task = download_media(image_downloaders, audio_downloaders, video_downloaders)
    files_task = stage_message_files(
        bot,
        file_items,
        memory_dir=_agent_memory_dir(user_id, group_id),
        workspace_key=_agent_workspace_key(user_id, group_id),
        message_time=msg_time,
        **message_identity,
        user_id=user_id,
        group_id=group_id,
    )
    if reply_seq:
        quote_task = build_reply_context(
            bot,
            event,
            reply_seq,
            group_id,
            messages_db,
            workspace_key=_agent_workspace_key(user_id, group_id),
            memory_dir=_agent_memory_dir(user_id, group_id),
        )
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

    recent_images: list[bytes] = []
    recent_attachments: list[dict[str, object]] = []
    should_hydrate_recent = (
        reply_seq is None
        and not images
        and not audio
        and not videos
        and not file_items
        and requests_recent_media(current_text)
    )
    if should_hydrate_recent:
        try:
            recent_images, recent_attachments, _recent_media_found = await hydrate_recent_media_context(
                bot,
                event,
                user_id=int(user_id),
                group_id=group_id,
                before_time=msg_time,
                messages_db=messages_db,
                workspace_key=_agent_workspace_key(user_id, group_id),
                memory_dir=_agent_memory_dir(user_id, group_id),
            )
        except Exception as exc:
            logger.warning("按需恢复近期媒体失败（不影响回复）: {}: {}", type(exc).__name__, exc)

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
                **message_identity,
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
                **message_identity,
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
                    **message_identity,
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
        staged_file for staged_file in staged_files if Path(staged_file.local_path) not in indexed_staged_paths
    ]

    try:
        current_attachment_refs = [
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
        current_attachment_refs.extend(
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
        known_attachment_paths = {str(attachment.get("path", "")) for attachment in current_attachment_refs}
        attachment_refs = [
            *current_attachment_refs,
            *(
                attachment
                for attachment in recent_attachments
                if str(attachment.get("path", "")) not in known_attachment_paths
            ),
        ]
        if recent_attachments:
            agent_text = f"{agent_text}\n[以上附件来自用户刚才发送的历史消息]".strip()
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
            recent_images=recent_images,
            images=images,
            audio=audio,
            videos=videos,
            attachments=attachment_refs,
            current_attachments=current_attachment_refs,
            recent_attachments=recent_attachments,
            # Persist and reuse the post-download snapshot so quoted media
            # semantics stay identical when this event becomes history.
            reply_to=resolved_reply_payload,
            reply_seq=reply_seq,
            direct_mention=direct_mention,
            message_id=message_id,
        )
        await _run_agent_turn(
            bot=bot,
            context=context,
            history_messages=gateway_messages,
            previous_reply_payload=reply_payload,
            fetched_reply_payload=agent_reply_payload,
            original_text=text,
        )
    finally:
        cleanup_staged_message_files(unindexed_staged_files)
