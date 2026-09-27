"""Platform-neutral decision providers used by gates and routers.

The package deliberately has no import-time dependency on Laya or any model
runtime.  Providers are loaded lazily so the default Signal path remains
lightweight when the optional Laya dependency is not installed.
"""

from .laya import LayaDecisionProvider, LayaProviderError
from .models import DecisionProvider, DecisionQuestions, DecisionResult, DecisionState
from .reply_gate import REPLY_GATE_QUESTIONS, ReplyGateScore, build_reply_gate_state, score_reply_gate

__all__ = [
    "DecisionProvider",
    "DecisionQuestions",
    "DecisionResult",
    "DecisionState",
    "LayaDecisionProvider",
    "LayaProviderError",
    "REPLY_GATE_QUESTIONS",
    "ReplyGateScore",
    "build_reply_gate_state",
    "score_reply_gate",
]
