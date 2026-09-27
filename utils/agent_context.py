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
    # Generic identity fields are optional during the QQ compatibility phase.
    # New platform adapters should populate these fields and stop relying on
    # the legacy user_id/group_id pair once their tools have migrated.
    conversation: ConversationRef | None = None
    principal: Participant | None = None
    capabilities: frozenset[str] = frozenset()
