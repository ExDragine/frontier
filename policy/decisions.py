"""策略判决值对象。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


@dataclass
class Decision:
    """策略链执行的判决结果。

    - allow: 继续执行下一条策略
    - deny:  短路，立即返回，不再执行后续策略。必须携带 message。
    - warn:  继续执行后续策略，可携带 message 和 metadata。
    """

    verdict: Verdict
    reason: str
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls, reason: str = "ok") -> "Decision":
        return cls(verdict=Verdict.ALLOW, reason=reason)

    @classmethod
    def deny(cls, reason: str, *, message: str) -> "Decision":
        if not message:
            raise ValueError("deny decision must carry a non-empty message")
        return cls(verdict=Verdict.DENY, reason=reason, message=message)

    @classmethod
    def warn(cls, reason: str, *, message: str = "") -> "Decision":
        return cls(verdict=Verdict.WARN, reason=reason, message=message)
