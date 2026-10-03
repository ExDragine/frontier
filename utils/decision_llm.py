"""Canonical decision-model entry points.

The implementation remains in :mod:`utils.signal_llm` for one migration
cycle so older plugins importing that module keep working.  New code should
import from this module.
"""

from .signal_llm import DecisionLLM, decision_structured

__all__ = ["DecisionLLM", "decision_structured"]
