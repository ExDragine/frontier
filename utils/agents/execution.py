"""Transport-independent Agent lifetime, deadlines, and outcome contract."""

import asyncio
import inspect
import logging
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Literal, NotRequired, TypedDict

from langchain.messages import AIMessage
from langchain_core.exceptions import (
    ContextOverflowError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelError,
    ModelInvalidRequestError,
    ModelNotFoundError,
    ModelPermissionDeniedError,
    ModelRateLimitError,
    ModelTimeoutError,
)

from utils.configs import EnvConfig

from .progress import ProgressEvent, emit_progress
from .runtime import conversation_workspace_key, run_serialized

logger = logging.getLogger(__name__)
current_run_id: ContextVar[str | None] = ContextVar("agent_run_id", default=None)
AgentStatus = Literal["success", "failed", "silent", "timeout"]
_TERMINAL_PROGRESS_TIMEOUT_SECONDS = 1.0


class AgentResult(TypedDict):
    response: dict[str, Any]
    total_time: float
    uni_messages: list[Any]
    should_reply: bool
    status: AgentStatus
    run_id: str
    error: NotRequired[str]
    error_code: NotRequired[str]


def agent_error_message(exc: Exception) -> str:
    """User-facing summaries must not contain provider response payloads."""
    if isinstance(exc, ContextOverflowError):
        return "本次对话内容超出处理上限，请缩短消息或拆分任务后重试。"
    if isinstance(exc, (ModelTimeoutError, TimeoutError)):
        return "本次请求超时，请稍后重试。"
    if isinstance(exc, ModelRateLimitError):
        return "服务请求过于频繁，请稍后重试。"
    if isinstance(exc, ModelConnectionError):
        return "暂时无法连接服务，请稍后重试。"
    if isinstance(exc, (ModelAuthenticationError, ModelPermissionDeniedError, ModelNotFoundError)):
        return "服务配置或访问权限异常，请联系管理员检查。"
    if isinstance(exc, ModelInvalidRequestError):
        return "服务无法处理本次请求，请联系管理员检查请求参数。"
    return "💥 服务暂时不可用，请稍后重试。"


async def _emit_failure_progress(reporter, event: ProgressEvent) -> None:
    # The turn deadline has already expired; reporting must not extend it indefinitely.
    try:
        async with asyncio.timeout(_TERMINAL_PROGRESS_TIMEOUT_SECONDS):
            await emit_progress(reporter, event)
    except TimeoutError:
        logger.debug("Terminal progress notification timed out")


def managed_agent_turn(function):
    """Apply one lifetime boundary around construction, execution and extraction.

    Cancellation propagates to the caller. Failures never rerun the entire graph:
    doing so could repeat already-completed platform writes.
    """
    signature = inspect.signature(function)

    @wraps(function)
    async def wrapped(*args, **kwargs) -> AgentResult:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        values = bound.arguments
        reporter = values.get("progress_reporter")
        scope = conversation_workspace_key(values["user_id"], values.get("group_id"))
        run_id = uuid.uuid4().hex
        token = current_run_id.set(run_id)
        started = time.monotonic()
        try:
            result = await run_serialized(
                f"workspace:{scope}",
                lambda: function(*args, **kwargs),
                timeout=EnvConfig.AGENT_JOB_TIMEOUT_SECONDS,
            )
            result.update(
                status="failed" if result.get("error") else ("success" if result.get("should_reply", True) else "silent"),
                run_id=run_id,
                total_time=time.monotonic() - started,
            )
            return result
        except asyncio.CancelledError:
            logger.info("Agent cancelled run_id=%s scope=%s", run_id, scope)
            # The transport owns cancellation reporting; never delay cancellation on I/O.
            raise
        except Exception as exc:
            status = "timeout" if isinstance(exc, (ModelTimeoutError, TimeoutError)) else "failed"
            logger.exception("Agent failed run_id=%s scope=%s error_type=%s", run_id, scope, type(exc).__name__)
            await _emit_failure_progress(reporter, ProgressEvent(type="done", message=agent_error_message(exc), detail={
                "success": False, "status": status, "run_id": run_id,
            }))
            return {
                "response": {"messages": [AIMessage(agent_error_message(exc))]},
                "total_time": time.monotonic() - started,
                "uni_messages": [],
                "should_reply": True,
                "status": status,
                "run_id": run_id,
                "error": type(exc).__name__,
                "error_code": type(exc).__name__ if isinstance(exc, ModelError) else status,
            }
        finally:
            current_run_id.reset(token)

    return wrapped
