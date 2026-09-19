"""Preview the production news pipeline without sending messages."""

import argparse
import asyncio
import json
from pathlib import Path

from plugins.news.rendering import render_html
from plugins.news.scheduler import generate
from utils.http_client import aclose_all


async def run(args):
    try:
        _, _, report = await generate(namespace="preview")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "report.json").write_text(
            json.dumps(report["payload"], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (args.out_dir / "report.html").write_text(render_html(report), encoding="utf-8")
        if report.get("image"):
            (args.out_dir / "report.png").write_bytes(report["image"])
        print(report["id"], report["status"])
        return 0
    finally:
        await aclose_all()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("cache/news-preview"))
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
