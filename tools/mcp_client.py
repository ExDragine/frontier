import asyncio
import json

import dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

dotenv.load_dotenv()

with open("mcp.json", encoding="utf-8") as f:
    tools_description: dict = json.load(f)
client = MultiServerMCPClient(tools_description)


def mcp_get_tools():
    return asyncio.run(client.get_tools())
