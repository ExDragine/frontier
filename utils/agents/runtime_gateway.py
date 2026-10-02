"""Protocol-neutral entry point for running Frontier's built-in Deep Agent."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol

from utils.agent_protocol import AgentArtifact, ConversationRef, Participant, normalize_workspace_key
from utils.agents.progress import ProgressReporter
from utils.media import (
    MediaKind,
    detect_mime_type,
    inline_media_bytes,
    media_block_kind,
    resolve_media,
    standard_media_block,
)

if TYPE_CHECKING:
    from .execution import AgentResult
    from .sessions import TurnLease


@dataclass(frozen=True, slots=True)
class AgentRuntimeMedia:
    kind: MediaKind
    data: bytes
    mime_type: str
    name: str | None = None
    url: str | None = None
    path: str | None = None


@dataclass(frozen=True, slots=True)
class AgentRuntimeRequest:
    session_id: str = ""
    prompt: str = ""
    images: tuple[AgentRuntimeMedia, ...] = ()
    audio: tuple[AgentRuntimeMedia, ...] = ()
    messages: tuple[dict[str, Any], ...] = ()
    user_id: str | None = None
    user_name: str = "ACP client"
    group_id: int | None = None
    group_member_role: str | None = None
    capability: str | None = None
    access_profile: Literal["frontier", "acp"] = "acp"
    enable_acp_subagents: bool = False
    allow_silent_reply: bool = False
    image_inputs: tuple[bytes, ...] = ()
    audio_inputs: tuple[bytes, ...] = ()
    video_inputs: tuple[bytes, ...] = ()
    session_turn: TurnLease | None = None
    # Neutral identity fields are optional while QQ callers migrate.  The
    # legacy fields above remain the compatibility surface for existing ACP,
    # scheduled-task and QQ entry points.
    conversation: ConversationRef | None = None
    principal: Participant | None = None
    capabilities: frozenset[str] = frozenset()
    workspace_key: str | None = None
    # Platform-provided tools are supplemental to the built-in capability
    # snapshot.  Keeping them on the runtime request lets a new adapter inject
    # its own operations without importing the global registry.
    tool_overrides: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentRuntimeResult:
    text: str
    artifacts: tuple[AgentRuntimeMedia, ...] = ()
    error: str | None = None
    status: str = "success"
    run_id: str | None = None
    usage: dict[str, Any] | None = None


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
        if "content" in content:
            return _message_text(content["content"])
        return ""
    if isinstance(content, list):
        return "\n".join(part for item in content if (part := _message_text(item)))
    return str(content or "")


def _runtime_artifact_kind(value: object) -> MediaKind | None:
    kind = str(value or "").lower()
    if kind == "voice":
        kind = "audio"
    return kind if kind in {"image", "audio", "video", "file"} else None


def _runtime_value(value: object, *names: str) -> object:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return None
    for name in names:
        item = getattr(value, name, None)
        if item is not None:
            return item
    return None


def _iter_runtime_artifact_segments(value: object):
    if isinstance(value, (AgentArtifact, Mapping)):
        yield value
        return
    if isinstance(value, (str, bytes, bytearray)):
        return
    if isinstance(value, Iterable):
        for item in value:
            yield from _iter_runtime_artifact_segments(item)
        return
    yield value


def _runtime_artifact(value: object) -> AgentRuntimeMedia | None:
    if isinstance(value, AgentArtifact):
        kind = _runtime_artifact_kind(value.kind)
        if kind is None:
            return None
        return AgentRuntimeMedia(
            kind=kind, data=value.data, mime_type=value.mime_type,
            name=value.name, url=value.url, path=value.path,
        )
    kind = media_block_kind(value) if isinstance(value, Mapping) else None
    if kind is None:
        kind = _runtime_artifact_kind(_runtime_value(value, "kind", "type"))
    if kind is None:
        return None
    inline = inline_media_bytes(value) if isinstance(value, Mapping) else None
    raw = inline[0] if inline and inline[0] else None
    declared_mime = (inline[1] if inline else None) or _runtime_value(value, "mime_type", "mimetype")
    if raw is None:
        raw_value = _runtime_value(value, "raw", "data")
        raw = bytes(raw_value) if isinstance(raw_value, (bytes, bytearray)) and raw_value else None
    url_value = _runtime_value(value, "url")
    path_value = _runtime_value(value, "path")
    url = str(url_value) if isinstance(url_value, str) and url_value and not url_value.startswith("data:") else None
    path = str(path_value) if isinstance(path_value, str) and path_value else None
    name_value = _runtime_value(value, "name", "filename")
    name = str(name_value) if isinstance(name_value, str) and name_value else None
    if raw is None and not url and not path:
        return None
    return AgentRuntimeMedia(
        kind=kind,
        data=raw or b"",
        mime_type=detect_mime_type(
            raw or b"",
            kind=kind,
            declared_mime=str(declared_mime) if declared_mime else None,
            file_name=name,
        ),
        name=name,
        url=url,
        path=path,
    )


def _runtime_artifacts(messages: object) -> tuple[AgentRuntimeMedia, ...]:
    artifacts: list[AgentRuntimeMedia] = []
    for segment in _iter_runtime_artifact_segments(messages):
        if artifact := _runtime_artifact(segment):
            artifacts.append(artifact)
    return tuple(artifacts)


def _qq_group_id(conversation: ConversationRef | None) -> int | None:
    """Translate a QQ group identity for the legacy cognitive boundary."""

    if conversation is None or conversation.platform != "qq" or conversation.kind != "group":
        return None
    try:
        return int(conversation.conversation_id)
    except (TypeError, ValueError):
        return None


def _conversation_workspace_key(conversation: ConversationRef | None) -> str | None:
    """Derive an isolated key when a new adapter omits an explicit key."""

    if conversation is None:
        return None
    # Serialize fields as a structured value so delimiters in opaque IDs
    # cannot make two different conversations share a workspace.
    identity = json.dumps(
        [
            conversation.platform,
            conversation.account_id,
            conversation.tenant_id,
            conversation.kind,
            conversation.parent_id,
            conversation.conversation_id,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return normalize_workspace_key(f"conversation:{identity}")


def _legacy_identity(request: AgentRuntimeRequest) -> tuple[str, str, int | None, str | None]:
    """Build the old cognitive identity without leaking it into new adapters."""

    principal = request.principal
    user_id = request.user_id or (principal.id if principal is not None else None)
    if user_id is None:
        user_id = f"acp-{request.session_id or request.workspace_key or 'request'}"
    user_name = request.user_name
    if principal is not None and user_name == "ACP client":
        user_name = principal.display_name
    group_id = request.group_id if request.group_id is not None else _qq_group_id(request.conversation)
    group_member_role = request.group_member_role or (principal.role if principal is not None else None)
    return str(user_id), user_name, group_id, group_member_role


class FrontierAgentRuntime:
    """Adapt ``FrontierCognitive`` to a transport-independent request contract."""

    def __init__(self, cognitive=None) -> None:
        self._cognitive = cognitive

    def _get_cognitive(self):
        if self._cognitive is None:
            from utils.agents.cognitive import FrontierCognitive

            self._cognitive = FrontierCognitive()
        return self._cognitive

    async def run(
        self,
        request: AgentRuntimeRequest,
        *,
        progress_reporter: ProgressReporter | None = None,
    ) -> AgentResult:
        from utils.configs import EnvConfig

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
        user_id, user_name, group_id, group_member_role = _legacy_identity(request)
        workspace_key = (
            normalize_workspace_key(request.workspace_key)
            if request.workspace_key
            else _conversation_workspace_key(request.conversation)
        )
        compatibility_kwargs: dict[str, Any] = {}
        if request.conversation is not None:
            compatibility_kwargs["conversation"] = request.conversation
        if request.principal is not None:
            compatibility_kwargs["principal"] = request.principal
        if request.capabilities:
            compatibility_kwargs["capabilities"] = request.capabilities
        if request.tool_overrides:
            compatibility_kwargs["tool_overrides"] = request.tool_overrides
        if workspace_key:
            compatibility_kwargs["workspace_key_override"] = workspace_key

        return await self._get_cognitive().chat_agent(
            list(request.messages) or [{"role": "user", "content": content}],
            user_id=user_id,
            user_name=user_name,
            capability=request.capability if request.capability is not None else EnvConfig.AGENT_CAPABILITY,
            group_id=group_id,
            group_member_role=group_member_role,
            image_inputs=[*request.image_inputs, *(item.data for item in request.images)],
            audio_inputs=[*request.audio_inputs, *(item.data for item in request.audio)],
            video_inputs=list(request.video_inputs),
            thread_id_override=request.session_id or workspace_key or None,
            progress_reporter=progress_reporter,
            user_text=request.prompt,
            access_profile=request.access_profile,
            enable_acp_subagents=request.enable_acp_subagents,
            allow_silent_reply=request.allow_silent_reply,
            **compatibility_kwargs,
            **({"session_turn": request.session_turn} if request.session_turn is not None else {}),
        )

    async def prompt(
        self,
        request: AgentRuntimeRequest,
        *,
        progress_reporter: ProgressReporter | None = None,
    ) -> AgentRuntimeResult:
        result = await self.run(request, progress_reporter=progress_reporter)
        response = result.get("response", {}) if isinstance(result, dict) else {}
        response_messages = response.get("messages", []) if isinstance(response, dict) else []
        final_message = response_messages[-1] if response_messages else ""
        return AgentRuntimeResult(
            text=_message_text(final_message).strip(),
            artifacts=_runtime_artifacts(result.get("artifacts", result.get("uni_messages", [])))
            if isinstance(result, dict)
            else (),
            error=str(result["error"]) if isinstance(result, dict) and result.get("error") else None,
            status=result.get("status", "failed" if result.get("error") else "success"),
            run_id=result.get("run_id"),
            usage=result.get("usage"),
        )


__all__ = [
    "AgentRuntime",
    "AgentRuntimeMedia",
    "AgentRuntimeRequest",
    "AgentRuntimeResult",
    "FrontierAgentRuntime",
]
