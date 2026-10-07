"""Explicit policy for request events; no model-supplied authorization."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EventKind = Literal[
    "friend_request", "group_join_request", "group_invited_join_request", "group_invitation",
]
EventAction = Literal["accept", "reject", "defer"]


class EventRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["ignore", "record", "rule", "shadow", "decision"] = "record"
    actions: tuple[EventAction, ...] = ("defer",)
    action: EventAction = "defer"
    instructions: str = Field(default="信息不足时选择 defer。", max_length=4000)
    initiator_ids: tuple[int, ...] = ()
    allow_filtered: bool = False


class EventConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    workers: int = Field(default=2, ge=1, le=8)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    max_pending: int = Field(default=1000, ge=1, le=10000)
    retention_days: int = Field(default=30, ge=1, le=365)
    rules: dict[EventKind, EventRule] = Field(default_factory=dict)
    # Configuration-file overrides only; no untrusted group message can edit them.
    groups: dict[str, dict[EventKind, EventRule]] = Field(default_factory=dict)

    def rule_for(self, kind: str, group_id: int | None) -> EventRule:
        return self.groups.get(str(group_id), {}).get(kind, self.rules.get(kind, EventRule()))


def allowed_actions(rule: EventRule, data: dict) -> tuple[str, ...]:
    if rule.initiator_ids and data.get("initiator_id") not in rule.initiator_ids:
        return ("defer",)
    if data.get("is_filtered") and not rule.allow_filtered:
        return ("defer",)
    return tuple(dict.fromkeys((*rule.actions, "defer")))
