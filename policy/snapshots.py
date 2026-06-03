"""介入点快照数据类。"""

from dataclasses import dataclass, field
from typing import Any

from collections.abc import Callable


@dataclass
class InputSnapshot:
    """input 介入点的完整快照。"""

    user_id: str
    group_id: int | None
    chat_type: str  # "group" | "private"
    text: str
    images: list[Callable[[], bytes | None]] = field(default_factory=list)
    is_at_bot: bool = False
    is_bot_name_prefix: bool = False
    raw_message: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputSnapshot:
    """output 介入点的完整快照。"""

    user_id: str
    group_id: int | None
    text: str
    agent_response_raw: str = ""
