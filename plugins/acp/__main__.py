"""Run Frontier's ACP stdio server: python -m plugins.acp."""

import argparse
import asyncio
import sys

from loguru import logger


def main() -> None:
    logger.remove()
    logger.add(sys.stderr, colorize=False)
    parser = argparse.ArgumentParser(description="Frontier ACP stdio server")
    parser.add_argument("--protocol-version", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()

    from .server import run_frontier_acp_server

    asyncio.run(run_frontier_acp_server(args.protocol_version))


if __name__ == "__main__":
    main()
