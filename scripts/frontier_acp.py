# ruff: noqa: E402, I001
"""Run Frontier as an ACP v1 stdio agent without polluting protocol stdout."""

import asyncio
import sys
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stderr, colorize=False)

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.agents.acp.server import FrontierAcpServer


def main() -> None:
    import acp

    asyncio.run(acp.run_agent(FrontierAcpServer()))


if __name__ == "__main__":
    main()
