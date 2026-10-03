"""Platform-neutral decision providers used by gates and routers.

The package deliberately has no import-time dependency on Laya or any model
runtime.  Providers are loaded lazily so the default decision path remains
lightweight when the optional Laya dependency is not installed.
"""

from utils.decision_llm import DecisionLLM, decision_structured

from .laya import LayaDecisionProvider, LayaProviderError
from .llm import DecisionEnvelope, LLMDecisionProvider
from .models import DecisionProvider, DecisionQuestions, DecisionResult, DecisionState
from .reply_gate import REPLY_GATE_QUESTIONS, ReplyGateScore, build_reply_gate_state, score_reply_gate

__all__ = [
    "DecisionProvider",
    "DecisionQuestions",
    "DecisionResult",
    "DecisionState",
    "DecisionEnvelope",
    "LLMDecisionProvider",
    "DecisionLLM",
    "decision_structured",
    "LayaDecisionProvider",
    "LayaProviderError",
    "REPLY_GATE_QUESTIONS",
    "ReplyGateScore",
    "build_reply_gate_state",
    "score_reply_gate",
]
