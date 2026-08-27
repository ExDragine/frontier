"""Protocol-neutral entry point for running Frontier's built-in Deep Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from utils.agents.progress import ProgressReporter
from utils.media import detect_mime_type, resolve_media, standard_media_block


@dataclass(frozen=True, slots=True)
class AgentRuntimeMedia:
    kind: Literal["image", "audio"]
    data: bytes
    mime_type: str


@dataclass(frozen=True, slots=True)
class AgentRuntimeRequest:
    session_id: str
    prompt: str
    images: tuple[AgentRuntimeMedia, ...] = ()
    audio: tuple[AgentRuntimeMedia, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentRuntimeResult:
    text: str
    artifacts: tuple[AgentRuntimeMedia, ...] = ()
    error: str | None = None


class AgentRuntime(Protocol):
    async def prompt(
        self,
        request: AgentRuntimeRequest,
        *,
        progress_reporter: ProgressReporter | None = None,
    ) -> AgentRuntimeResult: ...


def _message_text(value: object) -> str:
    content = getattr(value, "content", value)
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if content.get("type") in {"text", "output_text"} or "text" in content:
            return str(content.get("text", ""))
        return ""
    if isinstance(content, list):
        return "\n".join(part for item in content if (part := _message_text(item)))
    return str(content or "")


def _runtime_artifacts(messages: list[object]) -> tuple[AgentRuntimeMedia, ...]:
    artifacts: list[AgentRuntimeMedia] = []
    for message in messages:
        try:
            segments = list(message)  # type: ignore[arg-type]
        except TypeError:
            segments = [message]
        for segment in segments:
            kind = str(getattr(segment, "type", "") or "")
            if kind not in {"image", "audio"}:
                continue
            raw = getattr(segment, "raw", None)
            if not isinstance(raw, bytes | bytearray) or not raw:
                continue
            data = bytes(raw)
            declared_mime = getattr(segment, "mimetype", None)
            artifacts.append(
                AgentRuntimeMedia(
                    kind=kind,
                    data=data,
                    mime_type=detect_mime_type(
                        data,
                        kind=kind,
                        declared_mime=str(declared_mime) if declared_mime else None,
                    ),
                )
            )
    return tuple(artifacts)


class FrontierAgentRuntime:
    """Adapt ``FrontierCognitive`` to a transport-independent request contract."""

    def __init__(self, cognitive=None) -> None:
        self._cognitive = cognitive

    def _get_cognitive(self):
        if self._cognitive is None:
            from utils.agents.cognitive import FrontierCognitive

            self._cognitive = FrontierCognitive()
        return self._cognitive

    async def prompt(
        self,
        request: AgentRuntimeRequest,
        *,
        progress_reporter: ProgressReporter | None = None,
    ) -> AgentRuntimeResult:
        content: list[dict] = [{"type": "text", "text": request.prompt}]
        content.extend(
            (
                standard_media_block(
                    resolve_media(
                        item.data,
                        item.kind,
                        declared_mime=item.mime_type,
                    )
                )
            )
            for item in (*request.images, *request.audio)
        )
        result = await self._get_cognitive().chat_agent(
            [{"role": "user", "content": content}],
            user_id=f"acp-{request.session_id}",
            user_name="ACP client",
            group_id=None,
            image_inputs=[item.data for item in request.images],
            audio_inputs=[item.data for item in request.audio],
            video_inputs=[],
            thread_id_override=request.session_id,
            progress_reporter=progress_reporter,
            user_text=request.prompt,
            access_profile="acp",
            enable_acp_subagents=False,
        )
        response = result.get("response", {}) if isinstance(result, dict) else {}
        response_messages = response.get("messages", []) if isinstance(response, dict) else []
        final_message = response_messages[-1] if response_messages else ""
        return AgentRuntimeResult(
            text=_message_text(final_message).strip(),
            artifacts=_runtime_artifacts(result.get("uni_messages", []))
            if isinstance(result, dict)
            else (),
            error=str(result["error"]) if isinstance(result, dict) and result.get("error") else None,
        )


__all__ = [
    "AgentRuntime",
    "AgentRuntimeMedia",
    "AgentRuntimeRequest",
    "AgentRuntimeResult",
    "FrontierAgentRuntime",
]
