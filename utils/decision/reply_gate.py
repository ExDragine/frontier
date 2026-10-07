"""Reply-gate question and result helpers for decision providers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .models import DecisionProvider, DecisionResult
from .validation import validate_answers

REPLY_GATE_QUESTIONS: dict[str, dict[str, Any]] = {
    "should_reply": {
        "type": "predicate",
        "instructions": (
            "Does the latest message ask the AI assistant for help or an answer? "
            "Return true for a direct question, request, or problem report. Return "
            "false for casual conversation, acknowledgements, jokes, or a message "
            "addressed to other people."
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
    probability: float | None
    confidence: float | None
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


async def score_reply_gate(
    provider: DecisionProvider,
    plaintext: str,
    history: Sequence[object] = (),
    *,
    threshold: float = 0.5,
    instructions: str | None = None,
) -> ReplyGateScore:
    """Ask a provider for the reply probability and apply a local threshold."""

    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    questions = {name: dict(question) for name, question in REPLY_GATE_QUESTIONS.items()}
    if instructions is not None:
        questions["should_reply"]["instructions"] = instructions
    decision = await provider.decide(build_reply_gate_state(plaintext, history), questions)
    answer = validate_answers(decision.answers, questions)["should_reply"]
    if answer["type"] == "refusal":
        return ReplyGateScore(False, None, None, decision)
    probability = answer["probability"]
    return ReplyGateScore(
        should_reply=probability > threshold,
        probability=probability,
        confidence=answer.get("confidence"),
        decision=decision,
    )


__all__ = [
    "REPLY_GATE_QUESTIONS",
    "ReplyGateScore",
    "build_reply_gate_state",
    "score_reply_gate",
]
