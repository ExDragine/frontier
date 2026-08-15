"""Frontier-shaped result adapter for DeepSeek Harness."""

from __future__ import annotations

import time

from langchain.messages import AIMessage
from nonebot import logger

from utils.agents.progress import ProgressEvent, ProgressReporter, emit_progress

from .service import DshAgentService, DshConfigurationError, DshUnavailableError, dsh_service

DSH_EMPTY_RESPONSE_RECOVERY_PROMPT = (
    "The previous turn completed without a user-visible final response. "
    "Do not repeat any actions and do not call tools. Reply now with a concise final summary "
    "of the outcome, including any errors or incomplete work."
)


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
