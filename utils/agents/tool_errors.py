"""Shared tool error policy for the main graph and read-only subagents."""

import logging
from functools import wraps

from langchain.agents.middleware import ToolErrorMiddleware
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain.agents.middleware.tool_call_limit import ToolCallLimitExceededError
from langchain_core.tools import ToolException
from langgraph.errors import GraphBubbleUp

from .session_errors import CheckpointCapacityExceeded, SessionInterruptedError

logger = logging.getLogger(__name__)
BUDGET_ERRORS = (ModelCallLimitExceededError, ToolCallLimitExceededError)
CONTROL_ERRORS = (*BUDGET_ERRORS, CheckpointCapacityExceeded, SessionInterruptedError)


class ToolExecutionUncertainError(RuntimeError):
    """A potentially mutating tool failed; do not invite the model to repeat it."""


def read_only_error_message(exc: Exception) -> str:
    # Match rate-limit hints without copying arbitrary service payloads into prompts.
    text = str(exc).lower()
    if any(marker in text for marker in ("429", "rate limit", "too many requests", "usage limit", "quota")):
        return "查询服务已限流。停止继续搜索或切换后端，使用已有证据完成回复，并说明资料可能不完整。"
    if isinstance(exc, PermissionError):
        return "工具访问被拒绝。不得绕过权限或重复尝试该操作。"
    if isinstance(exc, (ValueError, FileNotFoundError)):
        return "查询参数无效或目标不存在。请检查参数或使用其他已有证据，不要编造结果。"
    return "查询工具暂时不可用。请基于已有证据继续，并说明未能完成的查询。"


def tool_error_middleware(*, read_only_tools=(), all_read_only: bool = False) -> ToolErrorMiddleware:
    names = {tool if isinstance(tool, str) else tool.name for tool in read_only_tools}

    def on_error(exc, request):
        if isinstance(exc, (*CONTROL_ERRORS, ToolExecutionUncertainError)):
            return None
        name = request.tool_call["name"]
        logger.warning("Tool failed name=%s error_type=%s", name, type(exc).__name__)
        if all_read_only or name in names:
            return read_only_error_message(exc)
        # Unknown tools are not assumed safe to repeat, even after ValueError:
        # an implementation can raise after a successful external write.
        raise ToolExecutionUncertainError(name) from None

    return ToolErrorMiddleware(on_error=on_error)


def _guard_ptc_sync(function):
    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (*CONTROL_ERRORS, ToolExecutionUncertainError, GraphBubbleUp):
            raise
        except Exception as exc:
            raise ToolException(read_only_error_message(exc)) from None
    return call


def _guard_ptc_async(function):
    @wraps(function)
    async def call(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except (*CONTROL_ERRORS, ToolExecutionUncertainError, GraphBubbleUp):
            raise
        except Exception as exc:
            raise ToolException(read_only_error_message(exc)) from None
    return call


def prepare_ptc_tools(tools):
    """QuickJS invokes tool.arun directly, outside graph middleware hooks."""
    prepared = []
    for tool in tools:
        updates = {}
        if callable(getattr(tool, "func", None)):
            updates["func"] = _guard_ptc_sync(tool.func)
        if callable(getattr(tool, "coroutine", None)):
            updates["coroutine"] = _guard_ptc_async(tool.coroutine)
        prepared.append(tool.model_copy(update=updates) if updates else tool)
    return prepared
