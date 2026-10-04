"""Platform-neutral decision providers used by gates and routers.

The package keeps Laya and model construction lazy.  Importing this package
does not load torch, transformers, or model weights, while the SDK itself is
installed as a regular project dependency.
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
