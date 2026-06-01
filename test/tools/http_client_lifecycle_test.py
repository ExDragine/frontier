# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client_name", "client_attr"),
    [
        ("heavens_above", "httpx_client"),
        ("satellite", "httpx_client"),
        ("space_weather", "httpx_client"),
        ("weather", "httpx_client"),
        ("deepseek_balance", "httpx_client"),
        ("rocket", "http_client"),
    ],
)
async def test_tool_module_http_clients_use_registry(load_tool_module, client_name, client_attr):
    """验证工具模块通过 http_client 注册表获取客户端而非各自创建。"""
    from utils import http_client as registry

    mod = load_tool_module(client_name)
    client = getattr(mod, client_attr, None)

    assert client is not None, f"{client_name}.{client_attr} is None"
    # 验证通过注册表获取（同一 name 返回同一实例）
    assert registry.get_http_client(client_name) is client


@pytest.mark.asyncio
async def test_http_client_aclose_all_unifies_lifecycle():
    """验证 aclose_all() 统一关闭所有注册客户端。"""
    from utils import http_client as registry

    # Clean start
    registry._clients.clear()
    registry._aclose_all_called = False

    client_a = registry.get_http_client("test_a")
    client_b = registry.get_http_client("test_b")
    assert client_a is registry.get_http_client("test_a")
    assert client_b is registry.get_http_client("test_b")

    closed = registry.aclose_all()
    assert "test_a" in closed
    assert "test_b" in closed
    assert len(registry._clients) == 0

    # Second call is no-op
    assert registry.aclose_all() == []
