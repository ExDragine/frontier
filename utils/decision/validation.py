"""Validate Frontier's provider-neutral answer contract (not an API wire format)."""

from collections.abc import Mapping
from math import isfinite
from typing import Any

from .models import DecisionQuestions


def _number(value: object, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}")
    return float(value)


def validate_questions(questions: DecisionQuestions) -> None:
    if not isinstance(questions, Mapping) or not questions:
        raise ValueError("questions must be a nonempty mapping")
    for name, question in questions.items():
        if not isinstance(name, str) or not name or not isinstance(question, Mapping):
            raise ValueError("question IDs must be nonempty strings with object definitions")
        kind = question.get("type")
        if kind not in {"predicate", "choice", "score"}:
            raise ValueError(f"unsupported decision question type: {kind!r}")
        if kind in {"choice", "score"}:
            options = question.get("choices" if kind == "choice" else "levels")
            if (not isinstance(options, list) or not options
                    or any(not isinstance(option, str) or not option for option in options)
                    or len(set(options)) != len(options)):
                raise ValueError(f"{name}: choices/levels must be unique nonempty strings")


def _refusal(answer: Mapping[str, Any]) -> dict[str, Any]:
    reason = answer.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("refusal must include a reason")
    return {"type": "refusal", "reason": reason}


def validate_answers(
    answers: Mapping[str, Mapping[str, Any]], questions: DecisionQuestions,
) -> dict[str, dict[str, Any]]:
    validate_questions(questions)
    if not isinstance(answers, Mapping) or set(answers) != set(questions):
        raise ValueError("decision answer IDs must exactly match question IDs")
    normalized = {}
    for name, question in questions.items():
        answer = answers[name]
        if not isinstance(answer, Mapping):
            raise ValueError(f"decision answer {name!r} must be an object")
        kind = answer.get("type")
        if kind == "refusal":
            normalized[name] = _refusal(answer)
            continue
        if kind != question["type"]:
            raise ValueError(f"decision answer {name!r} type does not match question")
        item = {"type": kind}
        if kind == "predicate":
            item["probability"] = _number(answer.get("probability"), "probability", 0, 1)
        elif kind == "choice":
            if answer.get("choice") not in question["choices"]:
                raise ValueError(f"decision answer {name!r} has an invalid choice")
            item["choice"] = answer["choice"]
        else:
            item["score"] = _number(answer.get("score"), "score", 0, len(question["levels"]) - 1)
        if "confidence" in answer:
            item["confidence"] = _number(answer["confidence"], "confidence", 0, 1)
        normalized[name] = item
    return normalized
