"""策略抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any

from .decisions import Decision
from .snapshots import InputSnapshot, OutputSnapshot


class BasePolicy(ABC):
    """所有策略的抽象基类。

    子类契约:
    - 必须设置 name 类属性（对应 manifesto 中的 policies.<name>）。
    - evaluate() 必须是无状态、确定性的。
    - configure() 在 __init__ 之后、evaluate() 之前由引擎调用。
    """

    name: str = ""
    severity: str = "normal"  # "safety" | "normal"
    config: dict[str, Any] = {}

    def configure(self, config: dict[str, Any]) -> None:
        self.config = config
        self.severity = config.get("severity", self.severity)

    @abstractmethod
    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        ...
