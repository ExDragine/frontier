"""Specialized Deep Agent subagent builders."""

from .acp import build_acp_subagents
from .document import build_document_subagent
from .research import build_research_subagent

__all__ = [
    "build_acp_subagents",
    "build_document_subagent",
    "build_research_subagent",
]
