"""Typed immutable context shared by the main agent and injected tools."""

from dataclasses import dataclass

from utils.agent_protocol import ConversationRef, Participant


@dataclass(frozen=True, slots=True)
class FrontierRuntimeContext:
    """Identity and authorization data for one Agent invocation."""

    user_id: str
    group_id: int | None
    group_member_role: str | None
    workspace_dir: str
    conversation: ConversationRef | None = None
    principal: Participant | None = None
    capabilities: frozenset[str] = frozenset()
