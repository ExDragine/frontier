# ruff: noqa: E402, I001
"""Run the daily news pipeline without sending group messages."""

import argparse
import asyncio
import datetime
import json
import os
import sys
import types
import zoneinfo
from pathlib import Path

import dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_tavily import TavilySearch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PLUGINS_DIR = ROOT_DIR / "plugins"
plugins_pkg = types.ModuleType("plugins")
plugins_pkg.__path__ = [str(PLUGINS_DIR)]
sys.modules.setdefault("plugins", plugins_pkg)

clockwork_pkg = types.ModuleType("plugins.clockwork")
clockwork_pkg.__path__ = [str(PLUGINS_DIR / "clockwork")]
sys.modules.setdefault("plugins.clockwork", clockwork_pkg)

tools_stub = types.ModuleType("tools")
tools_stub.agent_tools = types.SimpleNamespace(
    mcp_tools=[],
    web_tools=[],
    main_tools=[],
    all_tools=[],
)
sys.modules.setdefault("tools", tools_stub)

from plugins.clockwork import task_handlers  # noqa: E402
from plugins.clockwork.task_handlers import (  # noqa: E402
    build_daily_news_artifacts,
    load_daily_news_css,
)
from utils.markdown_render import html_to_image  # noqa: E402


EXA_MCP_CONFIG = {
    "exa": {
        "command": "npx",
        "args": [
            "-y",
            "mcp-remote",
            "https://mcp.exa.ai/mcp",
        ],
        "transport": "stdio",
    }
}
SEARCH_TOOL_NAMES = {"web_search_exa", "tavily_search"}


def _parse_now(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zoneinfo.ZoneInfo("Asia/Shanghai"))
    return parsed


def _safe_stamp(value: str) -> str:
    return value.replace("年", "").replace("月", "").replace("日", "").replace(":", "")


async def _preview_search_tools(backend: str) -> list:
    selected_tools = []

    if backend in {"exa", "both"}:
        mcp_client = MultiServerMCPClient(EXA_MCP_CONFIG)
        selected_tools.extend(
            tool for tool in await mcp_client.get_tools() if str(getattr(tool, "name", "")) in SEARCH_TOOL_NAMES
        )

    if backend in {"tavily", "both"}:
        dotenv.load_dotenv()
        tavily_api_key = os.getenv("TAVILY_API_KEY") or os.getenv("tavily_api_key")
        if tavily_api_key:
            selected_tools.append(TavilySearch(max_results=10, tavily_api_key=tavily_api_key))
        elif backend == "tavily":
            raise RuntimeError("missing TAVILY_API_KEY; add it to the environment or .env before running preview")

    if not selected_tools:
        raise RuntimeError(f"no search tools available for backend {backend!r}")
    return selected_tools


async def _run(args: argparse.Namespace) -> int:
    task_handlers.tools = await _preview_search_tools(args.search_backend)

    now_cn = _parse_now(args.now)
    artifacts = await build_daily_news_artifacts(now_cn=now_cn)
    if artifacts is None:
        print("daily news pipeline returned no artifacts")
        return 1
    if not artifacts.payload.top_stories and not artifacts.payload.worth_reading:
        print("daily news formatter returned an empty payload")
        return 1

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"daily_news_{_safe_stamp(artifacts.today)}_{artifacts.period}_{artifacts.report_time.replace(':', '')}"

    material_path = out_dir / f"{stem}.material.txt"
    payload_path = out_dir / f"{stem}.payload.json"
    html_path = out_dir / f"{stem}.html"

    material_path.write_text(artifacts.material, encoding="utf-8")
    payload_path.write_text(
        json.dumps(artifacts.payload.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    html_path.write_text(artifacts.html, encoding="utf-8")

    print(f"material: {material_path}")
    print(f"payload:  {payload_path}")
    print(f"html:     {html_path}")

    if args.image:
        image_path = out_dir / f"{stem}.png"
        image = await html_to_image(artifacts.html, css=load_daily_news_css())
        if not image:
            print("image render returned no bytes")
            return 1
        image_path.write_bytes(image)
        print(f"image:    {image_path}")

    return 0


async def _main(args: argparse.Namespace) -> int:
    try:
        return await _run(args)
    finally:
        from utils.http_client import aclose_all

        await aclose_all()


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview the daily news pipeline without sending messages.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("cache/daily_news_preview"),
        help="Directory for material, payload, HTML, and optional image output.",
    )
    parser.add_argument(
        "--now",
        help="Override current Asia/Shanghai time, for example 2026-05-21T09:00:00+08:00.",
    )
    parser.add_argument(
        "--search-backend",
        choices=["exa", "tavily", "both"],
        default="exa",
        help="Search backend for preview runs.",
    )
    parser.add_argument("--image", action="store_true", help="Also render the final HTML to a PNG image.")
    return asyncio.run(_main(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
