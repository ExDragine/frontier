# ruff: noqa: S101
"""Invalid provider output must never enable unsolicited replies."""

from types import SimpleNamespace

import pytest

from utils.decision import DecisionResult, LayaDecisionProvider, LayaProviderError, score_reply_gate
from utils.decision.validation import validate_answers

QUESTIONS = {"should_reply": {"type": "predicate"}}


@pytest.mark.parametrize("answers", [
    {},
    {"other": {"type": "predicate", "probability": 0.9}},
    {"should_reply": {"type": "choice", "choice": "yes"}},
    {"should_reply": {"probability": 0.9}},
    {"should_reply": {"type": "refusal"}},
])
def test_rejects_missing_ids_wrong_types_and_invalid_refusal(answers):
    with pytest.raises(ValueError):
        validate_answers(answers, QUESTIONS)


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf"), True, "0.9", None])
@pytest.mark.parametrize("field", ["probability", "confidence"])
def test_rejects_invalid_numbers(value, field):
    answer = {"type": "predicate", "probability": 0.8, field: value}
    with pytest.raises(ValueError):
        validate_answers({"should_reply": answer}, QUESTIONS)


def test_validates_choice_and_score_contracts():
    questions = {
        "route": {"type": "choice", "choices": ["search", "answer"]},
        "quality": {"type": "score", "levels": ["bad", "good", "great"]},
    }
    answers = {
        "route": {"type": "choice", "choice": "search"},
        "quality": {"type": "score", "score": 1.5, "confidence": 0.8},
    }
    assert validate_answers(answers, questions) == answers
    with pytest.raises(ValueError, match="choice"):
        validate_answers({**answers, "route": {"type": "choice", "choice": "delete"}}, questions)
    with pytest.raises(ValueError, match="score"):
        validate_answers({**answers, "quality": {"type": "score", "score": 3}}, questions)


@pytest.mark.asyncio
@pytest.mark.parametrize("answer, expected", [
    ({"type": "predicate", "probability": 0.9}, True),
    ({"type": "predicate", "probability": 0.5}, False),
    ({"type": "predicate", "probability": 0.1, "confidence": 0.99}, False),
    ({"type": "refusal", "reason": "Cannot decide"}, False),
])
async def test_gate_keeps_probability_confidence_and_refusal_separate(answer, expected):
    async def decide(state, questions):
        return DecisionResult({"should_reply": answer}, "test", 0)

    score = await score_reply_gate(SimpleNamespace(decide=decide), "help")
    assert score.should_reply is expected
    assert score.probability == answer.get("probability")
    assert score.confidence == answer.get("confidence")


@pytest.mark.asyncio
async def test_laya_translates_wire_contract_without_mutating_questions():
    def predict(state, questions):
        assert questions["should_reply"]["type"] == "noul"
        return {"answers": {"should_reply": {"type": "noul", "noul": True}}}

    provider = LayaDecisionProvider(router=SimpleNamespace(predict=predict))
    result = await provider.decide("help", QUESTIONS)
    assert result.answers == {"should_reply": {"type": "predicate", "probability": 1.0}}
    assert QUESTIONS["should_reply"]["type"] == "predicate"


@pytest.mark.asyncio
async def test_laya_rejects_missing_answers():
    provider = LayaDecisionProvider(router=SimpleNamespace(predict=lambda *_: {"answers": {}}))
    with pytest.raises(LayaProviderError, match="IDs"):
        await provider.decide("help", QUESTIONS)
