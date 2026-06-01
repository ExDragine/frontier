"""工具共享辅助函数 — paint.py 和 video.py 共用。

提取自 paint/video 中完全重复的状态/消息解析逻辑。
"""

from __future__ import annotations

import base64
from typing import Any

from utils.video_service import MediaReference


def state_user_id(state: dict | None) -> str:
    """从 Agent state 中提取当前用户 ID。"""
    if not isinstance(state, dict):
        return "tool"
    user_id = state.get("user_id")
    if user_id is None and isinstance(state.get("context"), dict):
        user_id = state["context"].get("user_id")
    return str(user_id or "tool")


def message_role(message: Any) -> str | None:
    """提取消息的 role 字段。"""
    if isinstance(message, dict):
        role = message.get("role")
    else:
        role = getattr(message, "role", None) or getattr(message, "type", None)
    return str(role) if role is not None else None


def message_content(message: Any) -> Any:
    """提取消息的 content 字段。"""
    if isinstance(message, dict):
        return message.get("content")
    return getattr(message, "content", None)


def latest_user_message_content(state: dict | None) -> Any:
    """从 state 的消息历史中获取最近一条用户消息的 content。"""
    if not isinstance(state, dict):
        return None
    messages = state.get("messages")
    if not isinstance(messages, list):
        return None
    for message in reversed(messages):
        if message_role(message) in {"user", "human"}:
            return message_content(message)
    return None


def media_part_url(part: dict, key: str) -> str | None:
    """从消息 part 字典中提取媒体 URL（image_url / video_url 等）。"""
    value = part.get(key)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        url = value.get("url")
        return url if isinstance(url, str) else None
    return None


def decode_data_url(url: str, *, expected_prefix: str) -> MediaReference | None:
    """解码 data: URL（base64 编码的媒体数据）。"""
    if not url.startswith(expected_prefix) or "," not in url:
        return None
    header, payload = url.split(",", 1)
    if ";base64" not in header:
        return None
    mime_type = header.removeprefix("data:").split(";", 1)[0]
    try:
        return MediaReference(data=base64.b64decode(payload, validate=True), mime_type=mime_type)
    except Exception:
        return None


# ── 工具计时 ────────────────────────────────────────────────────

import time as _time
from contextlib import asynccontextmanager as _asynccontextmanager
from nonebot import logger as _logger


@_asynccontextmanager
async def tool_timer(name: str, params: dict | None = None):
    """异步上下文管理器：统一记录工具调用的开始/结束时间和日志。"""
    start = _time.time()
    params_str = f", 参数: {params}" if params else ""
    _logger.info(f"🛠️ 调用工具: {name}{params_str}")
    try:
        yield
        elapsed = _time.time() - start
        _logger.info(f"✅ 工具执行成功: {name} (耗时: {elapsed:.2f}s)")
    except Exception:
        elapsed = _time.time() - start
        _logger.warning(f"⚠️ 工具执行失败: {name} (耗时: {elapsed:.2f}s)")
        raise
