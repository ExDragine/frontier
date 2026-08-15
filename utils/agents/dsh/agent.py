"""Frontier-shaped result adapter for DeepSeek Harness."""

from __future__ import annotations

import time

from langchain.messages import AIMessage
from nonebot import logger

from utils.agents.progress import ProgressEvent, ProgressReporter, emit_progress

from .service import DshAgentService, DshConfigurationError, DshUnavailableError, dsh_service


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
            if not response:
                response = "DSH 已结束，但没有生成文本回复。"
            finish_reason = getattr(result, "finish_reason", None)
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
