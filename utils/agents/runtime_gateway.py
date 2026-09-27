"""Protocol-neutral entry point for running Frontier's built-in Deep Agent."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol

from utils.agent_protocol import ConversationRef, Participant, normalize_workspace_key
from utils.agents.progress import ProgressReporter
from utils.media import MediaKind, detect_mime_type, resolve_media, standard_media_block

if TYPE_CHECKING:
    from .execution import AgentResult
    from .sessions import TurnLease


@dataclass(frozen=True, slots=True)
class AgentRuntimeMedia:
    kind: MediaKind
    data: bytes
    mime_type: str


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
        return ""
    if isinstance(content, list):
        return "\n".join(part for item in content if (part := _message_text(item)))
    return str(content or "")


def _runtime_artifacts(messages: list[object]) -> tuple[AgentRuntimeMedia, ...]:
    artifacts: list[AgentRuntimeMedia] = []
    for message in messages:
        segments = list(message) if isinstance(message, Iterable) else [message]
        for segment in segments:
            kind = str(getattr(segment, "type", getattr(segment, "kind", "")) or "")
            if kind not in {"image", "audio", "video", "file"}:
                continue
            raw = getattr(segment, "raw", getattr(segment, "data", None))
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
            artifacts=_runtime_artifacts(result.get("uni_messages", []))
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
