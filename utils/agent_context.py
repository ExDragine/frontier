"""Typed immutable context shared by the main agent and injected tools."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FrontierRuntimeContext:
    """Identity and authorization data for one Agent invocation."""

    user_id: str
    group_id: int | None
    group_member_role: str | None
    workspace_dir: str
