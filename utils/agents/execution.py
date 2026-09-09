"""Transport-independent Agent lifetime, deadlines, and outcome contract."""

import asyncio
import inspect
import json
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
from .session_errors import CheckpointCapacityExceeded, SessionInterruptedError
from .tool_errors import BUDGET_ERRORS, ToolExecutionUncertainError
from .usage import collect_run_usage, usage_registry

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
    usage: NotRequired[dict[str, Any]]


def agent_error_message(exc: Exception) -> str:  # noqa: C901
    """User-facing summaries must not contain provider response payloads."""
    if isinstance(exc, CheckpointCapacityExceeded):
        return "本次会话状态达到容量上限，已停止执行。此前操作可能已生效，请先核实结果。"
    if isinstance(exc, SessionInterruptedError):
        return "本次任务已中断，未继续执行后续操作。"
    if isinstance(exc, BUDGET_ERRORS):
        return "本次任务已达到调用上限，已停止继续执行。请缩小任务范围后再试。"
    if isinstance(exc, ToolExecutionUncertainError):
        return "工具执行遇到异常，已停止后续操作。此前操作可能已经生效，请先核实执行结果。"
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
        with collect_run_usage() as collector:
            result: AgentResult | None = None
            outcome = "cancelled"
            error_code = None
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
                outcome = result["status"]
                error_code = result.get("error_code")
                return result
            except asyncio.CancelledError:
                logger.info("Agent cancelled run_id=%s scope=%s", run_id, scope)
                # The transport owns cancellation reporting; never delay cancellation on I/O.
                raise
            except Exception as exc:
                status = "timeout" if isinstance(exc, (ModelTimeoutError, TimeoutError)) else "failed"
                logger.exception("Agent failed run_id=%s scope=%s error_type=%s", run_id, scope, type(exc).__name__)
                outcome = status
                error_code = (
                    "checkpoint_capacity_exceeded" if isinstance(exc, CheckpointCapacityExceeded)
                    else "session_interrupted" if isinstance(exc, SessionInterruptedError)
                    else "budget_exceeded" if isinstance(exc, BUDGET_ERRORS)
                    else "tool_execution_uncertain" if isinstance(exc, ToolExecutionUncertainError)
                    else type(exc).__name__ if isinstance(exc, ModelError) else status
                )
                await _emit_failure_progress(reporter, ProgressEvent(type="done", message=agent_error_message(exc), detail={
                    "success": False, "status": status, "run_id": run_id,
                }))
                result = {
                    "response": {"messages": [AIMessage(agent_error_message(exc))]},
                    "total_time": time.monotonic() - started,
                    "uni_messages": [],
                    "should_reply": True,
                    "status": status,
                    "run_id": run_id,
                    "error": type(exc).__name__,
                    "error_code": error_code,
                }
                return result
            finally:
                usage = collector.snapshot()
                if result is not None:
                    result["usage"] = usage
                usage_registry.record(
                    run_id=run_id, status=outcome, error_code=error_code,
                    duration=time.monotonic() - started, usage=usage,
                )
                logger.info("Agent usage run_id=%s status=%s usage=%s", run_id, outcome, json.dumps(usage))
                current_run_id.reset(token)

    return wrapped
