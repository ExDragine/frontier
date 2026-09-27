"""Contracts shared by optional decision backends."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

DecisionState = str | Mapping[str, Any] | list[Any]
DecisionQuestions = Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Normalized result returned by a decision provider.

    ``answers`` intentionally preserves the backend's typed answer shape.  A
    caller can use a ``choice``, ``score`` or ``noul`` answer without knowing
    whether it came from an in-process model or an HTTP service.
    """

    answers: Mapping[str, Mapping[str, Any]]
    provider: str
    latency_ms: float
    routing: Mapping[str, Any] = field(default_factory=dict)
    usage: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class DecisionProvider(Protocol):
    """Answer typed questions for one state."""

    async def decide(
        self,
        state: DecisionState,
        questions: DecisionQuestions,
    ) -> DecisionResult: ...


__all__ = ["DecisionQuestions", "DecisionProvider", "DecisionResult", "DecisionState"]
