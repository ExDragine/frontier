"""ENS 工具硬门控：仅 ve/vep 前缀消息触发的调用允许执行浏览器操作。

由 plugins/agent 在处理用户消息时设置，ENS 工具执行前检查。

会话级缓存：ENS 查询完成后，将文字摘要和媒体写入按 thread_id 索引的内存存储。
追问时，ens_read_cache 工具从缓存读取，避免重复调用 ENS 工具。
"""

import contextvars
import time as _time

_ens_caller_allowed: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "ens_caller_allowed", default=False
)

# 会话级 ENS 查询结果缓存，key = thread_id (str)
# value = {"text": str, "artifact_type": "video"|"image", "artifact_bytes": bytes, "timestamp": float}
_ens_session_store: dict[str, dict] = {}


def _write_ens_session(thread_id: str, text: str, artifact_type: str, artifact_bytes: bytes) -> None:
    """写入当前会话的 ENS 查询缓存，追问时由 ens_read_cache 读取。"""
    _ens_session_store[thread_id] = {
        "text": text,
        "artifact_type": artifact_type,
        "artifact_bytes": artifact_bytes,
        "timestamp": _time.time(),
    }


def clear_ens_session_store() -> None:
    """清理 ENS 会话缓存，由 shutdown hook 调用。"""
    _ens_session_store.clear()
    import logging
    logging.getLogger(__name__).info("ENS 会话缓存已清理")
