"""Immutable, bounded request envelope; deliberately separate from chat history."""

import hashlib
import json
import time

from pydantic import BaseModel, ConfigDict

from utils.event_policy import EventKind


class InboundEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    bot_id: str
    kind: EventKind
    occurred_at: int
    received_at: float
    group_id: int | None = None
    data: dict


def normalize_request(event) -> InboundEvent:
    kind = event.get_event_name()
    data = event.data.model_dump()
    group_id = data.get("group_id")
    bot_id = str(event.self_id)
    if kind == "friend_request":
        identity = [bot_id, kind, data["initiator_uid"], event.time, data.get("comment"), data.get("via")]
    else:
        identity = [bot_id, kind, group_id, data.get("notification_seq", data.get("invitation_seq"))]
    key = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
    # Keep routing identifiers intact; only human-written fields are bounded.
    for field in ("comment", "via"):
        if field in data:
            data[field] = str(data[field])[:4000]
    return InboundEvent(
        key=key, bot_id=bot_id, kind=kind, occurred_at=event.time,
        received_at=time.time(), group_id=group_id, data=data,
    )
