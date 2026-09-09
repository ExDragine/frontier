"""Build native LangChain MCP adapters from Frontier server entries."""

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from fastmcp.client.transports import SSETransport, StdioTransport, StreamableHttpTransport
from langchain.mcp import MCPAdapter


async def decline_elicitation(*_args) -> ElicitResult:
    """Frontier has no MCP question/resume UI; never suspend an Agent turn."""
    return ElicitResult(action="decline")


def build_mcp_adapter(entry: dict) -> MCPAdapter:
    """Preserve explicit transports and unprefixed server tool names."""
    transport_name = entry["transport"]
    if transport_name == "stdio":
        # Discovery runs in a temporary event loop. Do not keep its process alive.
        transport = StdioTransport(
            command=entry["command"],
            args=entry.get("args", []),
            env=entry.get("env"),
            keep_alive=False,
        )
    elif transport_name == "sse":
        transport = SSETransport(entry["url"])
    elif transport_name in {"http", "streamable_http"}:
        transport = StreamableHttpTransport(entry["url"])
    else:
        raise ValueError(f"Unsupported MCP transport: {transport_name}")
    return MCPAdapter(Client(transport, elicitation_handler=decline_elicitation))
