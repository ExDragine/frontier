import asyncio
import concurrent.futures
import json

from langchain_mcp_adapters.client import MultiServerMCPClient

with open("mcp.json", encoding="utf-8") as f:
    tools_description: dict = json.load(f)
client = MultiServerMCPClient(tools_description)


def mcp_get_tools():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(client.get_tools())
    # 运行中的事件循环：在单独线程中执行避免冲突
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, client.get_tools()).result()
