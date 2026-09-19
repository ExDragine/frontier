"""Build native LangChain MCP adapters from Frontier server entries."""

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from fastmcp.client.transports import StreamableHttpTransport
from langchain.mcp import MCPAdapter


async def decline_elicitation(*_args) -> ElicitResult:
    """Frontier has no MCP question/resume UI; never suspend an Agent turn."""
    return ElicitResult(action="decline")


def build_mcp_adapter(entry: dict) -> MCPAdapter:
    """Connect HTTP MCP endpoints, preserving headers and unprefixed tool names."""
    transport_name = entry.get("transport", "http")
    if transport_name not in {"http", "streamable_http"}:
        raise ValueError(f"Unsupported MCP transport: {transport_name}")
    transport = StreamableHttpTransport(entry["url"], headers=entry.get("headers"))
    return MCPAdapter(Client(transport, elicitation_handler=decline_elicitation))
