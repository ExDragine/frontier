"""Protocols implemented by platform adapters and application services."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .models import (
    AgentRequest,
    AgentResponse,
    ChatMessage,
    ConversationRef,
    DeliveryReceipt,
    GateDecision,
    HistoryQuery,
    InboundMessage,
    StoredMessage,
)


@runtime_checkable
class AgentCore(Protocol):
    """Execute one platform-neutral Agent request."""

    async def run(
        self,
        request: AgentRequest,
        *,
        tools: Sequence[object] = (),
    ) -> AgentResponse: ...


@runtime_checkable
class ReplyPolicy(Protocol):
    """Decide whether an inbound message should enter Agent execution."""

    async def decide(
        self,
        message: InboundMessage,
        history: Sequence[ChatMessage],
    ) -> GateDecision: ...


@runtime_checkable
class HistoryStore(Protocol):
    """Load and append normalized conversation history."""

    async def load(self, query: HistoryQuery) -> list[ChatMessage]: ...

    async def append(self, message: StoredMessage) -> None: ...


@runtime_checkable
class DeliveryPort(Protocol):
    """Deliver a neutral Agent response through a platform adapter."""

    async def send(
        self,
        target: ConversationRef,
        response: AgentResponse,
    ) -> DeliveryReceipt: ...


@runtime_checkable
class PlatformToolProvider(Protocol):
    """Provide platform-specific tools selected by runtime capabilities."""

    def tools(self, capabilities: frozenset[str]) -> Sequence[object]: ...


__all__ = [
    "AgentCore",
    "DeliveryPort",
    "HistoryStore",
    "PlatformToolProvider",
    "ReplyPolicy",
]
