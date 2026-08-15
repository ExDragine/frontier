"""Frontier-shaped result adapter for DeepSeek Harness."""

from __future__ import annotations

import re
import time
from typing import Any

from langchain.messages import AIMessage
from nonebot import logger

from utils.agents.progress import ProgressEvent, ProgressReporter, emit_progress

from .service import DshAgentService, DshConfigurationError, DshUnavailableError, dsh_service

DSH_EMPTY_RESPONSE_RECOVERY_PROMPT = (
    "The previous turn completed without a user-visible final response. "
    "Do not repeat any actions and do not call tools. Reply now with a concise final summary "
    "of the outcome, including any errors or incomplete work."
)

_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[-_ ]?key|access[-_ ]?token)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)


def _safe_error_text(value: Any, *, limit: int = 300) -> str:
    text = " ".join(str(value or "").split())
    for pattern in _SECRET_PATTERNS:
        replacement = r"\1[REDACTED]" if pattern.groups else "[REDACTED]"
        text = pattern.sub(replacement, text)
    if len(text) > limit:
        return f"{text[: limit - 1]}…"
    return text


def _dsh_error_summary(result: Any) -> str | None:
    """Extract the public LLM failure fields from the last error turn."""
    for event in reversed(getattr(result, "events", ()) or ()):
        if not isinstance(event, dict) or event.get("type") != "turn/end":
            continue
        data = event.get("data")
        reason = data.get("reason") if isinstance(data, dict) else None
        if not isinstance(reason, dict) or reason.get("kind") != "error":
            continue
        failure = reason.get("error")
        if not isinstance(failure, dict):
            return None

        message = _safe_error_text(failure.get("message"))
        metadata: list[str] = []
        code = _safe_error_text(failure.get("code"), limit=80)
        if code:
            metadata.append(f"code={code}")
        status = failure.get("status")
        if isinstance(status, int):
            metadata.append(f"HTTP {status}")
        retry_after_ms = failure.get("providerRetryAfterMs")
        if isinstance(retry_after_ms, int) and retry_after_ms >= 0:
            metadata.append(f"建议 {retry_after_ms / 1000:g}s 后重试")

        suffix = f"（{', '.join(metadata)}）" if metadata else ""
        if message:
            return f"上游模型调用失败：{message}{suffix}"
        if suffix:
            return f"上游模型调用失败{suffix}"
        return None
    return None


class DshAgent:
    def __init__(self, service: DshAgentService | None = None) -> None:
        self.service = service or dsh_service

    async def chat_agent(
        self,
        prompt: str,
        *,
        workspace_key: str,
        session_id: str,
        progress_reporter: ProgressReporter | None = None,
    ) -> dict:
        start_time = time.monotonic()
        try:
            result = await self.service.run(
                prompt,
                workspace_key=workspace_key,
                session_id=session_id,
                progress_reporter=progress_reporter,
            )
            response = str(getattr(result, "final_response", "") or "").strip()
            finish_reason = getattr(result, "finish_reason", None)
            if not response and finish_reason == "completed":
                logger.warning(
                    "DSH completed without assistant message; retrying final summary "
                    "(events=%s, notifications=%s)",
                    len(getattr(result, "events", ()) or ()),
                    len(getattr(result, "notifications", ()) or ()),
                )
                await emit_progress(
                    progress_reporter,
                    ProgressEvent(type="thinking", message="DSH 正在整理最终回复…"),
                )
                result = await self.service.run(
                    DSH_EMPTY_RESPONSE_RECOVERY_PROMPT,
                    workspace_key=workspace_key,
                    session_id=session_id,
                    progress_reporter=progress_reporter,
                )
                response = str(getattr(result, "final_response", "") or "").strip()
                finish_reason = getattr(result, "finish_reason", None)
            if not response:
                reason = str(finish_reason or "unknown")
                if reason == "error":
                    detail = _dsh_error_summary(result)
                    if detail:
                        raise DshUnavailableError(detail)
                raise DshUnavailableError(f"运行结束但没有生成文本回复（finish_reason={reason}）")
            await emit_progress(
                progress_reporter,
                ProgressEvent(type="done", message="DSH 已完成", detail={"finish_reason": finish_reason}),
            )
            return {
                "response": {"messages": [AIMessage(content=response)]},
                "total_time": time.monotonic() - start_time,
                "uni_messages": [],
            }
        except (DshUnavailableError, DshConfigurationError) as exc:
            logger.warning("DSH 实验 Agent 不可用: %s", exc)
            message = f"🧪 DSH 实验 Agent 暂不可用：{exc}"
            error = str(exc)
        except TimeoutError as exc:
            logger.warning("DSH 实验 Agent 超时: %s", exc)
            message = "🧪 DSH 执行超时，运行时已关闭；下次调用会自动重建。"
            error = str(exc)
        except Exception as exc:
            logger.exception("DSH 实验 Agent 执行失败: %s", type(exc).__name__)
            message = "🧪 DSH 实验 Agent 执行失败，请稍后重试。"
            error = str(exc)

        await emit_progress(
            progress_reporter,
            ProgressEvent(type="done", message="DSH 执行失败", detail={"success": False}),
        )
        return {
            "response": {"messages": [AIMessage(content=message)]},
            "total_time": time.monotonic() - start_time,
            "uni_messages": [],
            "error": error,
        }
