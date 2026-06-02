"""Shared helpers for media-capable tools."""

from __future__ import annotations

import base64
import binascii
import time
from collections.abc import Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from nonebot import logger

from utils.video_service import MediaReference


@dataclass(slots=True)
class ToolStateView:
    state: dict | None

    @property
    def user_id(self) -> str:
        if not isinstance(self.state, dict):
            return "tool"
        user_id = self.state.get("user_id")
        if user_id is None and isinstance(self.state.get("context"), dict):
            user_id = self.state["context"].get("user_id")
        return str(user_id or "tool")

    @property
    def latest_user_content(self) -> Any:
        if not isinstance(self.state, dict) or not isinstance(self.state.get("messages"), list):
            return None
        for message in reversed(self.state["messages"]):
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")
            else:
                role = getattr(message, "role", None) or getattr(message, "type", None)
                content = getattr(message, "content", None)
            if role in {"user", "human"}:
                return content
        return None

    def latest_binary(self, key: str, mime_type: str) -> MediaReference | None:
        if not isinstance(self.state, dict) or not isinstance(self.state.get(key), list):
            return None
        for item in reversed(self.state[key]):
            if isinstance(item, bytes):
                return MediaReference(data=item, mime_type=mime_type)
        return None

    def iter_media(
        self, part_type: str, key: str, expected_prefix: str, *, reverse: bool = False
    ) -> Iterator[MediaReference]:
        content = self.latest_user_content
        if not isinstance(content, list):
            return
        parts = reversed(content) if reverse else content
        for part in parts:
            if not isinstance(part, dict) or part.get("type") != part_type:
                continue

            value = part.get(key)
            if isinstance(value, dict):
                value = value.get("url")
            if not isinstance(value, str) or not value.startswith(expected_prefix) or "," not in value:
                continue

            header, payload = value.split(",", 1)
            if ";base64" not in header:
                continue
            try:
                yield MediaReference(
                    data=base64.b64decode(payload, validate=True),
                    mime_type=header.removeprefix("data:").split(";", 1)[0],
                )
            except binascii.Error, ValueError:
                continue


@asynccontextmanager
async def tool_timer(name: str, params: dict | None = None):
    """统一记录工具调用的开始/结束时间和日志。"""
    start = time.time()
    params_str = f", 参数: {params}" if params else ""
    logger.info(f"🛠️ 调用工具: {name}{params_str}")
    try:
        yield
        elapsed = time.time() - start
        logger.info(f"✅ 工具执行成功: {name} (耗时: {elapsed:.2f}s)")
    except Exception:
        elapsed = time.time() - start
        logger.warning(f"⚠️ 工具执行失败: {name} (耗时: {elapsed:.2f}s)")
        raise
