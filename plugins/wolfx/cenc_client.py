"""Wolfx CENC earthquake early-warning WebSocket client."""

import asyncio
import json
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from nonebot import logger
from websockets.asyncio.client import connect

CENC_WEBSOCKET_URL = "wss://ws-api.wolfx.jp/cenc_eew"
CENC_QUERY_COMMAND = "query_cenceew"
CENC_PING_COMMAND = "ping"
CENC_RECEIVE_TIMEOUT_SECONDS = 90.0
CENC_RECONNECT_INITIAL_SECONDS = 1.0
CENC_RECONNECT_MAX_SECONDS = 60.0
CENC_STABLE_CONNECTION_SECONDS = 30.0


class CencEventHandler(Protocol):
    def __call__(self, data: dict[str, Any], *, is_snapshot: bool) -> Awaitable[Any]: ...


class CencWebSocketService:
    """Maintain one Wolfx CENC WebSocket connection for the process lifetime."""

    def __init__(
        self,
        *,
        connector: Callable[..., Any] = connect,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[float, float], float] = random.uniform,
        receive_timeout: float = CENC_RECEIVE_TIMEOUT_SECONDS,
    ) -> None:
        self._connector = connector
        self._sleep = sleep
        self._jitter = jitter
        self._receive_timeout = receive_timeout
        self._handler: CencEventHandler | None = None
        self._task: asyncio.Task[None] | None = None
        self._connected = False
        self._last_error: str | None = None
        self._last_message_at: float | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self, handler: CencEventHandler) -> bool:
        """Start the listener once; return whether a new task was created."""
        if self.is_running:
            return False
        self._handler = handler
        self._task = asyncio.create_task(self._run(), name="wolfx-cenc-websocket-listener")
        return True

    async def stop(self) -> None:
        """Cancel the listener and wait for WebSocket cleanup."""
        task = self._task
        if task is None:
            return
        if not task.done():
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("停止 Wolfx CENC WebSocket 服务时发现后台任务异常")
        finally:
            self._task = None
            self._connected = False

    async def _run(self) -> None:
        reconnect_delay = CENC_RECONNECT_INITIAL_SECONDS
        while True:
            connected_at: float | None = None
            try:
                async with self._connector(
                    CENC_WEBSOCKET_URL,
                    open_timeout=10,
                    close_timeout=5,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=64 * 1024,
                    max_queue=16,
                ) as websocket:
                    connected_at = time.monotonic()
                    self._connected = True
                    self._last_error = None
                    logger.info("Wolfx CENC WebSocket 已连接")
                    await self._consume(websocket)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("Wolfx CENC WebSocket 连接中断: %s", self._last_error)
            finally:
                self._connected = False

            if connected_at is not None and time.monotonic() - connected_at >= CENC_STABLE_CONNECTION_SECONDS:
                reconnect_delay = CENC_RECONNECT_INITIAL_SECONDS

            sleep_for = self._jitter(reconnect_delay * 0.75, reconnect_delay * 1.25)
            logger.info("Wolfx CENC WebSocket 将在 %.1f 秒后重连", sleep_for)
            await self._sleep(sleep_for)
            reconnect_delay = min(reconnect_delay * 2, CENC_RECONNECT_MAX_SECONDS)

    async def _consume(self, websocket: Any) -> None:
        if self._handler is None:
            raise RuntimeError("Wolfx CENC WebSocket event handler is not configured")

        await websocket.send(CENC_QUERY_COMMAND)
        snapshot_pending = True
        while True:
            raw_message = await asyncio.wait_for(websocket.recv(), timeout=self._receive_timeout)
            self._last_message_at = time.monotonic()
            data = self._decode_message(raw_message)
            if data is not None:
                snapshot_pending = await self._dispatch_message(websocket, data, snapshot_pending)

    @staticmethod
    def _decode_message(raw_message: Any) -> dict[str, Any] | None:
        if isinstance(raw_message, bytes):
            logger.debug("忽略 Wolfx CENC WebSocket 二进制消息")
            return None
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning("忽略无效的 Wolfx CENC WebSocket JSON")
            return None
        if not isinstance(data, dict):
            logger.warning("忽略非对象的 Wolfx CENC WebSocket JSON")
            return None
        return data

    async def _dispatch_message(self, websocket: Any, data: dict[str, Any], snapshot_pending: bool) -> bool:
        message_type = data.get("type")
        if message_type == "heartbeat":
            await websocket.send(CENC_PING_COMMAND)
            return snapshot_pending
        if message_type == "pong":
            return snapshot_pending
        if message_type != "cenc_eew":
            logger.debug("忽略未知 Wolfx CENC WebSocket 消息类型: %s", message_type)
            return snapshot_pending

        if self._handler is None:
            raise RuntimeError("Wolfx CENC WebSocket event handler is not configured")
        try:
            await self._handler(data, is_snapshot=snapshot_pending)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("处理 Wolfx CENC WebSocket 消息失败")
        return False


cenc_websocket_service = CencWebSocketService()
