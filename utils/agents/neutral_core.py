"""Bridge the neutral Agent Core contract to Frontier's legacy runtime.

This module is the migration seam between ``utils.agent_protocol`` and the
existing ``FrontierAgentRuntime``.  It owns compatibility conversion only:
platform adapters still normalize native events before this boundary, and no
NoneBot, Milky, or other platform SDK types are imported here.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any

from utils.agent_protocol import (
    AgentArtifact,
    AgentRequest,
    AgentResponse,
    AudioPart,
    ChatMessage,
    FilePart,
    ImagePart,
    MentionPart,
    MessagePart,
    QuotePart,
    TextPart,
    VideoPart,
)
from utils.media import resolve_media, standard_media_block

from .runtime_gateway import (
    AgentRuntimeMedia,
    AgentRuntimeRequest,
    AgentRuntimeResult,
    FrontierAgentRuntime,
    _runtime_artifacts,
)


def _part_text(part: MessagePart) -> str:
    """Return a bounded plain-text representation for legacy prompts."""

    if isinstance(part, TextPart):
        return part.text
    if isinstance(part, MentionPart):
        return f"@{part.display_name or part.participant_id}"
    if isinstance(part, QuotePart):
        quoted = "".join(_part_text(item) for item in part.parts)
        return f"[引用: {quoted}]" if quoted else "[引用消息]"
    if isinstance(part, FilePart):
        label = f"[文件: {part.name}]" if part.name else "[文件]"
        return f"{label} ({part.url})" if part.url else label
    if isinstance(part, (ImagePart, AudioPart, VideoPart)):
        label = type(part).__name__.removesuffix("Part").lower()
        return f"[{label}]"
    return ""


def _parts_text(parts: Sequence[MessagePart]) -> str:
    return "".join(_part_text(part) for part in parts)


def _prompt_part_text(part: MessagePart) -> str:
    """Return only textual input for legacy intent/capture hooks.

    Media is already represented by the structured message blocks and the
    runtime media fields.  Keeping ``prompt`` textual avoids appending a
    second ``[image]``/``[audio]``/``[video]`` marker when the compatibility
    gateway forwards the neutral request.
    """

    if isinstance(part, (ImagePart, AudioPart, VideoPart)):
        return ""
    if isinstance(part, QuotePart):
        quoted = "".join(_prompt_part_text(item) for item in part.parts)
        return f"[引用: {quoted}]" if quoted else "[引用消息]"
    return _part_text(part)


def _prompt_text(parts: Sequence[MessagePart]) -> str:
    return "".join(_prompt_part_text(part) for part in parts)


def _part_block(part: MessagePart) -> object:
    """Translate one neutral part to a legacy model content block."""

    if isinstance(part, TextPart):
        return {"type": "text", "text": part.text}
    if isinstance(part, MentionPart):
        return {"type": "text", "text": _part_text(part)}
    if isinstance(part, QuotePart):
        text = _part_text(part)
        return {"type": "text", "text": text}
    if isinstance(part, FilePart):
        return {"type": "text", "text": _part_text(part)}
    if isinstance(part, (ImagePart, AudioPart, VideoPart)):
        if part.data:
            kind = "image" if isinstance(part, ImagePart) else "audio" if isinstance(part, AudioPart) else "video"
            media = resolve_media(part.data, kind, declared_mime=part.mime_type, file_name=part.name)
            return standard_media_block(media)
        if part.url:
            # The runtime intentionally does not fetch remote media at this
            # boundary.  Platform adapters can download it before normalizing
            # the message when the provider requires inline bytes.
            return {"type": "text", "text": _part_text(part) + f" ({part.url})"}
        return {"type": "text", "text": _part_text(part)}
    return {"type": "text", "text": _part_text(part)}


def _part_blocks(part: MessagePart) -> list[object]:
    """Return model content blocks, expanding media nested in a quote.

    A quote is a message container rather than a media payload itself.  Keep
    its readable text in one block and expose any already downloaded media as
    sibling blocks so providers that support multimodal input can still see
    the quoted bytes.
    """

    if not isinstance(part, QuotePart):
        return [_part_block(part)]

    blocks: list[object] = []
    text = _part_text(part)
    if text:
        blocks.append({"type": "text", "text": text})
    for child in part.parts:
        if isinstance(child, (ImagePart, AudioPart, VideoPart)) and (child.data or child.url):
            blocks.extend(_part_blocks(child))
    return blocks or [{"type": "text", "text": "[引用消息]"}]


def _content_blocks(parts: Sequence[MessagePart]) -> list[object]:
    blocks: list[object] = []
    for part in parts:
        blocks.extend(_part_blocks(part))
    return blocks


def _iter_parts(parts: Sequence[MessagePart]):
    """Yield top-level parts and parts nested in quotes."""

    for part in parts:
        yield part
        if isinstance(part, QuotePart):
            yield from _iter_parts(part.parts)


def _content_for_message(content: object) -> object:
    if isinstance(content, str):
        return content
    if isinstance(content, (tuple, list)):
        return _content_blocks(content)
    return str(content or "")


def _history_message(message: ChatMessage) -> dict[str, Any]:
    result: dict[str, Any] = {
        "role": message.role,
        "content": _content_for_message(message.content),
    }
    if message.message_id is not None:
        # The session middleware uses LangGraph-compatible ``id`` values to
        # identify the current boundary and avoid replaying hot history.
        result["id"] = message.message_id
    return result


def _current_content(request: AgentRequest) -> list[object]:
    return _content_blocks(request.current.parts)


def _current_message(request: AgentRequest) -> dict[str, Any]:
    message: dict[str, Any] = {
        "role": "user",
        "content": _current_content(request),
    }
    if request.session_turn is not None and (current_id := getattr(request.session_turn, "current_id", None)):
        message["id"] = current_id
    return message


def _current_media(request: AgentRequest) -> tuple[
    tuple[AgentRuntimeMedia, ...],
    tuple[AgentRuntimeMedia, ...],
    tuple[bytes, ...],
]:
    images: list[AgentRuntimeMedia] = []
    audio: list[AgentRuntimeMedia] = []
    videos: list[bytes] = []
    for part in _iter_parts(request.current.parts):
        if not isinstance(part, (ImagePart, AudioPart, VideoPart)) or not part.data:
            continue
        if isinstance(part, ImagePart):
            images.append(AgentRuntimeMedia("image", part.data, part.mime_type or "image/*"))
        elif isinstance(part, AudioPart):
            audio.append(AgentRuntimeMedia("audio", part.data, part.mime_type or "audio/*"))
        elif isinstance(part, VideoPart):
            videos.append(part.data)
    return tuple(images), tuple(audio), tuple(videos)


def _response_text(value: object) -> str:
    content = getattr(value, "content", None)
    if content is None and hasattr(value, "text"):
        content = value.text
    if content is None:
        content = value
    if isinstance(content, str):
        return content
    if isinstance(content, Mapping):
        value = content.get("text", content.get("content", ""))
        return _response_text(value)
    if isinstance(content, list):
        return "\n".join(text for item in content if (text := _response_text(item)))
    return str(content or "")


def _mapping_result(result: Mapping[str, Any]) -> AgentRuntimeResult:
    response = result.get("response")
    messages = response.get("messages", []) if isinstance(response, Mapping) else []
    text = _response_text(messages[-1]) if messages else str(result.get("text", ""))
    raw_artifacts = result.get("artifacts", result.get("uni_messages", ()))
    artifacts = list(_runtime_artifacts(raw_artifacts))
    status = str(result.get("status", "failed" if result.get("error") else "success"))
    if result.get("should_reply") is False and status == "success":
        status = "silent"
    return AgentRuntimeResult(
        text=text.strip(),
        artifacts=tuple(artifacts),
        error=str(result["error"]) if result.get("error") else None,
        status=status,
        run_id=str(result["run_id"]) if result.get("run_id") is not None else None,
        usage=result.get("usage"),
    )


async def _invoke_runtime(
    runtime: object,
    request: AgentRuntimeRequest,
    tools: Sequence[object],
) -> AgentRuntimeResult | Mapping[str, Any]:
    """Invoke either the normalized or legacy runtime shape.

    ``FrontierAgentRuntime.prompt`` is preferred because it already converts
    legacy graph output.  Small test doubles and older integrations may expose
    only ``run``; both are supported during the migration.
    """

    method = getattr(runtime, "prompt", None) or getattr(runtime, "run", None)
    if method is None:
        raise TypeError("runtime must provide prompt() or run()")
    kwargs: dict[str, object] = {}
    try:
        if "tools" in inspect.signature(method).parameters:
            kwargs["tools"] = tools
    except (TypeError, ValueError):
        pass
    return await method(request, **kwargs)


class FrontierAgentCore:
    """Implement the neutral ``AgentCore`` port using the existing runtime."""

    def __init__(self, runtime: object | None = None) -> None:
        self._runtime = runtime or FrontierAgentRuntime()

    async def run(
        self,
        request: AgentRequest,
        *,
        tools: Sequence[object] = (),
    ) -> AgentResponse:
        images, audio, videos = _current_media(request)
        messages = [_history_message(message) for message in request.history]
        messages.append(_current_message(request))
        sender = request.current.sender
        runtime_request = AgentRuntimeRequest(
            session_id=request.request_id,
            prompt=_prompt_text(request.current.parts),
            images=images,
            audio=audio,
            messages=tuple(messages),
            user_id=sender.id,
            user_name=sender.display_name,
            capability=request.execution_profile,
            access_profile="acp" if request.execution_profile == "acp" else "frontier",
            enable_acp_subagents=request.execution_profile != "acp",
            allow_silent_reply=request.allow_silent_reply,
            image_inputs=tuple(item.data for item in images),
            audio_inputs=tuple(item.data for item in audio),
            video_inputs=videos,
            session_turn=request.session_turn,
            conversation=request.current.conversation,
            principal=sender,
            capabilities=request.capabilities,
            workspace_key=request.workspace_key,
            tool_overrides=tuple(tools),
        )
        raw_result = await _invoke_runtime(self._runtime, runtime_request, tools)
        result = _mapping_result(raw_result) if isinstance(raw_result, Mapping) else raw_result
        if not isinstance(result, AgentRuntimeResult):
            raise TypeError("runtime must return AgentRuntimeResult or a legacy result mapping")
        artifacts = tuple(
            AgentArtifact(
                kind=item.kind,
                data=item.data,
                mime_type=item.mime_type,
                name=item.name,
                url=item.url,
                path=item.path,
            )
            for item in result.artifacts
        )
        return AgentResponse(
            text=result.text,
            artifacts=artifacts,
            status=result.status,
            # Keep failed status visible to the orchestrator.  Marking an
            # errored turn as ``should_reply=False`` would incorrectly turn it
            # into a silent/gated outcome before status handling runs.
            should_reply=result.status != "silent",
            run_id=result.run_id,
            usage=result.usage or {},
        )


__all__ = ["FrontierAgentCore"]
