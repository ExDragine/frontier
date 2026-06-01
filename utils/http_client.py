"""统一的 HTTP 客户端管理。

使用注册表模式：各模块通过 get_http_client(name) 获取或创建客户端，
shutdown 时调用 aclose_all() 统一关闭所有客户端。
"""

from __future__ import annotations

import httpx
from nonebot import logger

_clients: dict[str, httpx.AsyncClient] = {}
_aclose_all_called: bool = False


def get_http_client(name: str, *, timeout: float = 30.0) -> httpx.AsyncClient:
    """获取或创建命名的 HTTP 客户端。同名多次调用返回同一实例。"""
    if name not in _clients:
        transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
        _clients[name] = httpx.AsyncClient(transport=transport, timeout=timeout)
    return _clients[name]


async def aclose_all() -> list[str]:
    """关闭所有已注册的 HTTP 客户端，返回已关闭的客户端名称列表。"""
    global _aclose_all_called
    if _aclose_all_called:
        return []
    _aclose_all_called = True
    closed: list[str] = []
    for name, client in list(_clients.items()):
        try:
            await client.aclose()
            closed.append(name)
        except Exception as exc:
            logger.warning(f"关闭 HTTP 客户端 '{name}' 失败: {exc}")
    _clients.clear()
    if closed:
        logger.debug(f"已关闭 {len(closed)} 个 HTTP 客户端: {', '.join(closed)}")
    return closed
