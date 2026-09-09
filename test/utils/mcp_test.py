# ruff: noqa: S101
"""Exercise the real MCP stack outside the suite's LangChain stubs."""

import subprocess
import sys
from pathlib import Path


def test_native_mcp_transport_and_cross_loop_tool_call(tmp_path):
    server = tmp_path / "server.py"
    server.write_text(
        'import os\n'
        'from fastmcp import FastMCP\n'
        'mcp = FastMCP("migration-test")\n'
        '@mcp.tool\n'
        'def echo(value: str) -> dict:\n'
        '    return {"value": value, "marker": os.environ["MCP_TEST_MARKER"]}\n'
        'mcp.run(transport="stdio", show_banner=False)\n',
        encoding="utf-8",
    )
    script = """
import asyncio
import sys
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
from utils.mcp import build_mcp_adapter, decline_elicitation

for name, expected in [("http", StreamableHttpTransport),
                       ("streamable_http", StreamableHttpTransport),
                       ("sse", SSETransport)]:
    adapter = build_mcp_adapter({"transport": name, "url": "https://example.com/mcp"})
    assert isinstance(adapter.client.transport, expected)

adapter = build_mcp_adapter({
    "transport": "stdio", "command": sys.executable, "args": [sys.argv[1]],
    "env": {"MCP_TEST_MARKER": "preserved"},
})
tools = asyncio.run(adapter.list_tools())
assert [tool.name for tool in tools] == ["echo"]
# Startup discovery closes its loop; runtime must reconnect in a new loop.
for value in ["first", "second"]:
    result = asyncio.run(tools[0].ainvoke({
        "type": "tool_call", "id": "test", "name": "echo", "args": {"value": value},
    }))
    assert result.artifact["structured_content"] == {"value": value, "marker": "preserved"}
assert asyncio.run(decline_elicitation()).action == "decline"
"""
    result = subprocess.run(  # noqa: S603 - fixed test script and pytest-owned server
        [sys.executable, "-c", script, str(server)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
