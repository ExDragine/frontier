#!/usr/bin/env python3
"""Synchronize display names from OpenRouter's public Models API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx2

MODELS_URL = "https://openrouter.ai/api/v1/models?output_modalities=all"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "models/data/openrouter_names.json"
_MODEL_ID_RE = re.compile(r"^~?[a-z0-9_-]+/[^\s]+$")


def _request_bytes() -> bytes:
    response = httpx2.get(
        MODELS_URL,
        timeout=30,
        follow_redirects=False,
    )
    response.raise_for_status()
    return response.content


def build_snapshot(response: bytes) -> dict[str, Any]:
    payload = json.loads(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list) or not payload["data"]:
        raise ValueError("OpenRouter response has no model list")
    links = payload.get("links")
    if links is not None and (not isinstance(links, dict) or links.get("next")):
        raise ValueError("OpenRouter returned an incomplete or paginated model list")

    models: dict[str, str] = {}
    for entry in payload["data"]:
        if not isinstance(entry, dict):
            raise ValueError("OpenRouter returned an invalid model entry")
        model_id, name = entry.get("id"), entry.get("name")
        if not isinstance(model_id, str) or not _MODEL_ID_RE.fullmatch(model_id.casefold()):
            raise ValueError("OpenRouter returned an invalid model ID")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"OpenRouter returned an empty display name for {model_id!r}")
        key = model_id.casefold()
        if key in models:
            raise ValueError(f"OpenRouter returned a duplicate model ID: {model_id!r}")
        models[key] = name.strip()

    return {
        "schema_version": "1.0",
        "source": {
            "url": MODELS_URL,
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "response_sha256": hashlib.sha256(response).hexdigest(),
        },
        "model_count": len(models),
        "models": dict(sorted(models.items())),
    }


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def sync(*, output: Path, check: bool, input_path: Path | None = None) -> bool:
    snapshot = build_snapshot(input_path.read_bytes() if input_path is not None else _request_bytes())
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        # Prices, response ordering, hashes and fetch times do not change display names.
        if (
            isinstance(previous, dict)
            and previous.get("schema_version") == snapshot["schema_version"]
            and isinstance(previous.get("source"), dict)
            and previous["source"].get("url") == MODELS_URL
            and previous.get("model_count") == snapshot["model_count"]
            and previous.get("models") == snapshot["models"]
        ):
            return True
    if check:
        return False
    _write_atomic(output, json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="read a saved Models API response instead of accessing the network")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail when model names differ without writing files")
    args = parser.parse_args()
    try:
        current = sync(output=args.output, check=args.check, input_path=args.input)
    except (OSError, UnicodeError, ValueError, httpx2.HTTPError) as exc:
        print(f"OpenRouter model names sync failed: {exc}", file=sys.stderr)
        return 1
    if not current:
        print(f"OpenRouter model names are stale: {args.output}", file=sys.stderr)
        return 1
    print(f"OpenRouter model names {'verified' if args.check else 'synchronized'}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
