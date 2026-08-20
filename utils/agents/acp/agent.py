"""Frontier-shaped result adapter for ACP agents."""

from __future__ import annotations

import re
import time
from typing import Any

from langchain.messages import AIMessage
from nonebot import logger

from utils.agents.progress import ProgressEvent, ProgressReporter, emit_progress

from .service import (
    AcpAgentService,
    AcpConfigurationError,
    AcpInputMedia,
    AcpUnavailableError,
    acp_service,
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
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _uni_messages(artifacts: tuple[Any, ...]) -> list[Any]:
    if not artifacts:
        return []
    from utils.alconna import UniMessage

    messages = []
    for artifact in artifacts:
        if artifact.kind == "image":
            messages.append(UniMessage.image(raw=artifact.data))
        elif artifact.kind == "audio":
            messages.append(UniMessage.audio(raw=artifact.data))
    return messages


class AcpAgent:
    def __init__(self, service: AcpAgentService | None = None) -> None:
        self.service = service or acp_service

    async def chat_agent(
        self,
        prompt: str,
        *,
        workspace_key: str,
        agent_name: str | None = None,
        media: tuple[AcpInputMedia, ...] = (),
        progress_reporter: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        start_time = time.monotonic()
        try:
            result = await self.service.run(
                prompt,
                workspace_key=workspace_key,
                agent_name=agent_name,
                media=media,
                progress_reporter=progress_reporter,
            )
            response = result.final_response.strip()
            if not response and not result.artifacts:
                raise AcpUnavailableError(
                    f"运行结束但没有生成可发送内容（stop_reason={result.stop_reason}）"
                )
            await emit_progress(
                progress_reporter,
                ProgressEvent(type="done", message="ACP Agent 已完成", detail={"stop_reason": result.stop_reason}),
            )
            return {
                "response": {"messages": [AIMessage(content=response)]},
                "total_time": time.monotonic() - start_time,
                "uni_messages": _uni_messages(result.artifacts),
            }
        except (AcpUnavailableError, AcpConfigurationError) as exc:
            logger.warning("ACP Agent 不可用: %s", type(exc).__name__)
            error = _safe_error_text(exc)
            message = f"🔌 ACP Agent 暂不可用：{error}"
        except TimeoutError as exc:
            logger.warning("ACP Agent 超时")
            error = _safe_error_text(exc)
            message = "🔌 ACP Agent 执行超时，连接已关闭；下次调用会自动重建。"
        except Exception as exc:
            logger.exception("ACP Agent 执行失败: %s", type(exc).__name__)
            error = _safe_error_text(exc)
            message = "🔌 ACP Agent 执行失败，请稍后重试。"

        await emit_progress(
            progress_reporter,
            ProgressEvent(type="done", message="ACP Agent 执行失败", detail={"success": False}),
        )
        return {
            "response": {"messages": [AIMessage(content=message)]},
            "total_time": time.monotonic() - start_time,
            "uni_messages": [],
            "error": error,
        }
