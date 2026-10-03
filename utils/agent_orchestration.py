"""Platform-neutral application orchestration for one Agent turn.

This module is deliberately small and boring: adapters normalize a native
event before calling :class:`ConversationOrchestrator`, while Agent Core and
the three application ports remain unaware of NoneBot, Milky, or any other
platform SDK.  The existing QQ handlers can adopt this boundary incrementally
without changing their current request path.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import quote
from uuid import uuid4

from .agent_protocol import (
    AgentCore,
    AgentRequest,
    AgentResponse,
    ChatMessage,
    ConversationRef,
    DeliveryPort,
    DeliveryReceipt,
    DeliveryStatus,
    GateDecision,
    HistoryQuery,
    HistoryStore,
    InboundMessage,
    PlatformToolProvider,
    ReplyPolicy,
    StoredMessage,
    normalize_workspace_key,
)


class TurnStatus(StrEnum):
    """Terminal state of an orchestrated turn."""

    GATED = "gated"
    SILENT = "silent"
    DELIVERED = "delivered"
    HISTORY_FAILED = "history_failed"
    GATE_FAILED = "gate_failed"
    AGENT_FAILED = "agent_failed"
    DELIVERY_FAILED = "delivery_failed"
    HISTORY_APPEND_FAILED = "history_append_failed"


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """Auditable outcome of one application-layer turn."""

    request_id: str
    status: TurnStatus
    history: tuple[ChatMessage, ...] = ()
    gate: GateDecision | None = None
    request: AgentRequest | None = None
    response: AgentResponse | None = None
    receipt: DeliveryReceipt | None = None
    history_appended: bool = False
    error: str | None = None

    @property
    def delivered(self) -> bool:
        """Whether the platform acknowledged delivery for this turn."""

        return self.receipt is not None and self.receipt.status == DeliveryStatus.DELIVERED


def workspace_key_for(conversation: ConversationRef) -> str:
    """Build a collision-resistant default workspace key.

    Platform adapters may pass an explicit key when they have a stronger
    tenancy policy.  This fallback keeps the application layer usable for a
    new adapter before that policy exists.
    """

    fields = (
        conversation.platform,
        conversation.account_id,
        conversation.tenant_id or "-",
        conversation.kind,
        conversation.conversation_id,
        conversation.parent_id or "-",
    )
    return normalize_workspace_key(":".join(quote(value, safe="") for value in fields))


def _failure_text(error: Exception) -> str:
    """Return a bounded, type-qualified error suitable for audit metadata."""

    detail = str(error).strip()
    if len(detail) > 300:
        detail = detail[:297] + "..."
    return f"{type(error).__name__}: {detail}" if detail else type(error).__name__


def _assistant_message(
    message: InboundMessage,
    response: AgentResponse,
    receipt: DeliveryReceipt,
) -> StoredMessage:
    """Convert a delivered neutral response to the history representation."""

    # A response may produce multiple platform messages (for example an
    # attachment followed by text). The final message is the assistant turn
    # boundary used by session checkpoints and history deduplication.
    message_id = receipt.message_refs[-1].message_id if receipt.message_refs else None
    metadata: dict[str, object] = {
        "run_id": response.run_id,
        "artifact_count": len(response.artifacts),
    }
    return ChatMessage(
        role="assistant",
        content=response.text,
        message_id=message_id,
        conversation=message.conversation,
        created_at=datetime.now(UTC),
        metadata=metadata,
    )


class ConversationOrchestrator:
    """Run the shared application flow for one normalized inbound message.

    The orchestrator owns ordering and persistence semantics.  In particular,
    an assistant message is appended only after ``DeliveryStatus.DELIVERED``;
    a transport failure never causes an Agent retry or a false history entry.
    """

    def __init__(
        self,
        core: AgentCore,
        *,
        history_limit: int = 50,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be positive")
        self._core = core
        self._history_limit = history_limit
        self._request_id_factory = request_id_factory or (lambda: uuid4().hex)

    async def handle(  # noqa: C901
        self,
        message: InboundMessage,
        *,
        policy: ReplyPolicy,
        history: HistoryStore,
        delivery: DeliveryPort,
        tools: PlatformToolProvider | None = None,
        workspace_key: str | None = None,
        capabilities: frozenset[str] = frozenset(),
        execution_profile: str = "default",
        allow_silent_reply: bool = False,
        session_turn: object | None = None,
    ) -> TurnOutcome:
        """Process a normalized message through the application ports."""

        request_id = self._request_id_factory()
        try:
            loaded_history = tuple(
                await history.load(
                    HistoryQuery(
                        conversation=message.conversation,
                        limit=self._history_limit,
                        before=message.created_at,
                    )
                )
            )
        except Exception as error:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.HISTORY_FAILED,
                error=_failure_text(error),
            )

        try:
            gate = await policy.decide(message, loaded_history)
        except Exception as error:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.GATE_FAILED,
                history=loaded_history,
                error=_failure_text(error),
            )
        if not gate.should_reply:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.GATED,
                history=loaded_history,
                gate=gate,
            )

        request = AgentRequest(
            request_id=request_id,
            current=message,
            history=loaded_history,
            workspace_key=normalize_workspace_key(workspace_key)
            if workspace_key
            else workspace_key_for(message.conversation),
            capabilities=capabilities,
            execution_profile=execution_profile,
            allow_silent_reply=allow_silent_reply,
            session_turn=session_turn,
        )
        try:
            selected_tools: Sequence[object] = tools.tools(capabilities) if tools else ()
            response = await self._core.run(request, tools=selected_tools)
        except Exception as error:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.AGENT_FAILED,
                history=loaded_history,
                gate=gate,
                request=request,
                error=_failure_text(error),
            )

        if not isinstance(response, AgentResponse):
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.AGENT_FAILED,
                history=loaded_history,
                gate=gate,
                request=request,
                error="Agent Core returned an invalid response",
            )

        if response.status not in {"success", "silent"}:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.AGENT_FAILED,
                history=loaded_history,
                gate=gate,
                request=request,
                response=response,
                error=f"agent response status: {response.status}",
            )
        if response.status == "silent" or not response.should_reply:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.SILENT,
                history=loaded_history,
                gate=gate,
                request=request,
                response=response,
            )

        try:
            receipt = await delivery.send(message.conversation, response)
        except Exception as error:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.DELIVERY_FAILED,
                history=loaded_history,
                gate=gate,
                request=request,
                response=response,
                error=_failure_text(error),
            )
        if receipt.status != DeliveryStatus.DELIVERED:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.DELIVERY_FAILED,
                history=loaded_history,
                gate=gate,
                request=request,
                response=response,
                receipt=receipt,
            )

        # Assistant history is a text-turn boundary.  Artifact-only replies
        # can still be delivered, but there is no textual assistant message to
        # append and no platform-independent artifact history representation.
        if not response.text.strip():
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.DELIVERED,
                history=loaded_history,
                gate=gate,
                request=request,
                response=response,
                receipt=receipt,
            )

        try:
            await history.append(_assistant_message(message, response, receipt))
        except Exception as error:
            return TurnOutcome(
                request_id=request_id,
                status=TurnStatus.HISTORY_APPEND_FAILED,
                history=loaded_history,
                gate=gate,
                request=request,
                response=response,
                receipt=receipt,
                error=_failure_text(error),
            )
        return TurnOutcome(
            request_id=request_id,
            status=TurnStatus.DELIVERED,
            history=loaded_history,
            gate=gate,
            request=request,
            response=response,
            receipt=receipt,
            history_appended=True,
        )


__all__ = ["ConversationOrchestrator", "TurnOutcome", "TurnStatus", "workspace_key_for"]
