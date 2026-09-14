# ruff: noqa: E402, I001
"""Deterministic real-stdio ACP peer, with no model or external service calls."""

import asyncio
import sys
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stderr)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import acp
from acp.experimental import v2

from plugins.acp.server import FrontierAcpServer
from plugins.acp.server_v2 import FrontierAcpV2Server
from utils.agents.progress import ProgressEvent
from utils.agents.runtime_gateway import AgentRuntimeMedia, AgentRuntimeResult


class Runtime:
    async def prompt(self, request, *, progress_reporter):
        if request.prompt == "wait":
            await progress_reporter(ProgressEvent(type="thinking", message="waiting"))
            await asyncio.Event().wait()
        return AgentRuntimeResult(
            text=f"echo:{request.prompt}",
            artifacts=(AgentRuntimeMedia("image", b"contract-image", "image/png"),),
        )


async def main():
    if sys.argv[1] == "1":
        await acp.run_agent(FrontierAcpServer(Runtime()))
    else:
        server = FrontierAcpV2Server(Runtime())
        try:
            await v2.run_agent(server)
        finally:
            await server.aclose()


if __name__ == "__main__":
    asyncio.run(main())
