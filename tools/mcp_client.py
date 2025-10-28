import asyncio
import json

from langchain_mcp_adapters.client import MultiServerMCPClient

with open("mcp.json", encoding="utf-8") as f:
    tools_description: dict = json.load(f)
client = MultiServerMCPClient(tools_description)


def mcp_get_tools():
    return asyncio.run(client.get_tools())
