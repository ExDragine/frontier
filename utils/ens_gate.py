"""ENS 工具硬门控：仅 ve/vep 前缀消息触发的调用允许执行浏览器操作。

由 plugins/agent 在处理用户消息时设置，ENS 工具执行前检查。
"""

import contextvars

_ens_caller_allowed: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "ens_caller_allowed", default=False
)

# ve/vep 前缀区分：plugins/agent 设置，ens_normal/ens_professional 校验
# 值："ve" | "vep" | ""（未触发）
_ens_prefix: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ens_prefix", default=""
)
