"""ENS 工具上下文变量。"""

import contextvars

_ens_prefix: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ens_prefix", default=""
)
