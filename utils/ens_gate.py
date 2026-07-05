"""ENS 工具上下文变量。"""

import contextvars

_ens_caller_allowed: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "ens_caller_allowed", default=False
)

_ens_prefix: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ens_prefix", default=""
)
