"""Reply-gate question and result helpers for decision providers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .models import DecisionProvider, DecisionResult

REPLY_GATE_QUESTIONS: dict[str, dict[str, Any]] = {
    "should_reply": {
        "type": "noul",
        "instructions": (
            "Should the assistant proactively reply to the latest group message? "
            "Return true only when the user is asking for help, asking a question, "
            "reporting a problem, or clearly addressing an AI assistant. Return false "
            "for casual conversation, acknowledgements, jokes, or messages addressed "
            "to another person."
        ),
        "criteria": {
            "false": "casual conversation or not addressed to the assistant",
            "true": "a question, request for help, problem report, or clear assistant request",
        },
    }
}


@dataclass(frozen=True, slots=True)
class ReplyGateScore:
    """One provider's reply-gate score."""

    should_reply: bool
    probability: float
    confidence: float
    decision: DecisionResult


def _content_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return str(value.get("text", value.get("content", "")))
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return " ".join(_content_text(item) for item in value)
    return str(value or "")


def build_reply_gate_state(plaintext: str, history: Sequence[object] = (), *, limit: int = 5) -> str:
    """Render a bounded, platform-neutral state for the gate model."""

    if limit < 1:
        raise ValueError("limit must be positive")
    rows = []
    for item in history[-limit:]:
        if isinstance(item, Mapping):
            role = str(item.get("role", "user"))
            content = _content_text(item.get("content", ""))
        else:
            role = str(getattr(item, "role", "user"))
            content = _content_text(getattr(item, "content", item))
        if content.strip():
            rows.append(f"{role}: {content.strip()}")
    rows.append(f"user: {plaintext.strip()}")
    return "\n".join(rows)


def _noul_probability(answer: Mapping[str, Any]) -> float:
    value = answer.get("noul")
    if isinstance(value, bool):
        return float(value)
    try:
        probability = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("reply-gate answer does not contain a numeric 'noul' probability") from error
    if not 0 <= probability <= 1:
        raise ValueError("reply-gate probability must be between 0 and 1")
    return probability


async def score_reply_gate(
    provider: DecisionProvider,
    plaintext: str,
    history: Sequence[object] = (),
    *,
    threshold: float = 0.5,
) -> ReplyGateScore:
    """Ask a provider for the reply probability and apply a local threshold."""

    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    decision = await provider.decide(build_reply_gate_state(plaintext, history), REPLY_GATE_QUESTIONS)
    answer = decision.answers.get("should_reply")
    if answer is None:
        raise ValueError("reply-gate provider omitted the 'should_reply' answer")
    probability = _noul_probability(answer)
    confidence = answer.get("answer_confidence", answer.get("confidence", max(probability, 1 - probability)))
    try:
        normalized_confidence = float(confidence)
    except (TypeError, ValueError) as error:
        raise ValueError("reply-gate answer confidence must be numeric") from error
    return ReplyGateScore(
        should_reply=probability >= threshold,
        probability=probability,
        confidence=normalized_confidence,
        decision=decision,
    )


__all__ = [
    "REPLY_GATE_QUESTIONS",
    "ReplyGateScore",
    "build_reply_gate_state",
    "score_reply_gate",
]
