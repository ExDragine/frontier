# ruff: noqa: S101
"""Exercise the real HTTP MCP stack outside the suite's LangChain stubs."""

import json
import subprocess
import sys
from pathlib import Path


def test_native_http_mcp_transport_and_cross_loop_tool_call():
    script = """
import asyncio
import socket
import threading
import time

import uvicorn
from fastmcp import FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server.dependencies import get_http_headers
from utils.mcp import build_mcp_adapter, decline_elicitation

mcp = FastMCP("http-contract-test")
@mcp.tool
def echo(value: str) -> dict:
    return {"value": value, "marker": get_http_headers()["x-test-marker"]}

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
port = sock.getsockname()[1]
server = uvicorn.Server(uvicorn.Config(mcp.http_app(), log_level="error"))
thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
thread.start()
try:
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started, "HTTP MCP server did not start"
    for name in [None, "http", "streamable_http"]:
        entry = {"url": f"http://127.0.0.1:{port}/mcp",
                 "headers": {"x-test-marker": "preserved"}}
        if name is not None:
            entry["transport"] = name
        adapter = build_mcp_adapter(entry)
        assert isinstance(adapter.client.transport, StreamableHttpTransport)
        tools = asyncio.run(adapter.list_tools())
        assert [tool.name for tool in tools] == ["echo"]
        # Discovery closes its loop; each invocation must reconnect with headers.
        for value in ["first", "second"]:
            result = asyncio.run(tools[0].ainvoke({
                "type": "tool_call", "id": "test", "name": "echo", "args": {"value": value},
            }))
            assert result.artifact["structured_content"] == {"value": value, "marker": "preserved"}
    for name in ["stdio", "sse"]:
        try:
            build_mcp_adapter({"transport": name, "url": "http://127.0.0.1/mcp"})
        except ValueError:
            pass
        else:
            raise AssertionError(f"Legacy transport accepted: {name}")
    assert asyncio.run(decline_elicitation()).action == "decline"
finally:
    server.should_exit = True
    thread.join(timeout=10)
    sock.close()
    assert not thread.is_alive(), "HTTP MCP server did not stop"
"""
    result = subprocess.run(  # noqa: S603 - fixed isolated test script with loopback HTTP server
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_exa_example_uses_direct_streamable_http():
    repo_root = Path(__file__).resolve().parents[2]
    config = json.loads((repo_root / "mcp.json.example").read_text(encoding="utf-8"))

    assert config["exa"]["transport"] == "http"
    assert config["exa"]["url"] == "https://mcp.exa.ai/mcp"
    assert config["exa"]["startup_timeout_seconds"] == 60
    assert "command" not in config["exa"]
