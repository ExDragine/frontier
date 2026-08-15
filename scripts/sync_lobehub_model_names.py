#!/usr/bin/env python3
"""Synchronize display names from LobeHub's published model-bank package."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REGISTRY_ROOT = "https://registry.npmjs.org/model-bank"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "models/data/lobehub_names.json"
LICENSE_URL = "https://github.com/lobehub/lobehub/blob/canary/LICENSE"
_PROVIDER_MODULE_RE = re.compile(r"^package/dist/aiModels/(?P<provider>[A-Za-z0-9_-]+)\.mjs$")
_JS_STRING = r'"(?:\\.|[^"\\])*"'
_MODEL_PAIR_RE = re.compile(
    rf"\bdisplayName\s*:\s*(?P<name>{_JS_STRING})"
    rf"(?:(?!\bdisplayName\s*:)[\s\S])*?\bid\s*:\s*(?P<id>{_JS_STRING})"
)


def _request_bytes(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "registry.npmjs.org":
        raise ValueError(f"refusing unexpected model-bank URL: {url}")
    request = urllib.request.Request(  # noqa: S310 - HTTPS host is allowlisted above
        url, headers={"User-Agent": "frontier-model-bank-sync/1"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed HTTPS registry
        return response.read()


def _package_metadata(version: str) -> dict[str, Any]:
    encoded_version = urllib.parse.quote(version, safe="")
    raw = json.loads(_request_bytes(f"{REGISTRY_ROOT}/{encoded_version}"))
    if raw.get("name") != "model-bank":
        raise ValueError("NPM registry returned an unexpected package")
    return raw


def _verify_integrity(archive: bytes, integrity: str) -> None:
    candidates = integrity.split()
    for candidate in candidates:
        algorithm, separator, expected = candidate.partition("-")
        if not separator or algorithm not in hashlib.algorithms_available:
            continue
        actual = base64.b64encode(hashlib.new(algorithm, archive).digest()).decode("ascii")
        if actual == expected:
            return
    raise ValueError("model-bank package integrity verification failed")


def _extract_models(module_source: str) -> dict[str, str]:
    models: dict[str, str] = {}
    for match in _MODEL_PAIR_RE.finditer(module_source):
        model_id = json.loads(match.group("id")).strip()
        display_name = json.loads(match.group("name")).strip()
        if not model_id or not display_name:
            continue
        key = model_id.casefold()
        existing = models.get(key)
        if existing is not None and existing != display_name:
            raise ValueError(f"conflicting display names for model {model_id!r}")
        models[key] = display_name
    return models


def _extract_providers(archive: bytes) -> dict[str, dict[str, str]]:
    providers: dict[str, dict[str, str]] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
        for member in package.getmembers():
            match = _PROVIDER_MODULE_RE.fullmatch(member.name)
            if match is None or match.group("provider") == "index" or not member.isfile():
                continue
            module = package.extractfile(member)
            if module is None:
                continue
            models = _extract_models(module.read().decode("utf-8"))
            if models:
                provider = match.group("provider").casefold()
                if provider in providers:
                    raise ValueError(f"duplicate provider module {provider!r}")
                providers[provider] = dict(sorted(models.items()))
    if not providers:
        raise ValueError("model-bank package did not contain recognizable model metadata")
    return dict(sorted(providers.items()))


def build_snapshot(metadata: dict[str, Any], archive: bytes) -> dict[str, Any]:
    dist = metadata.get("dist")
    if not isinstance(dist, dict):
        raise ValueError("model-bank package metadata has no dist information")
    integrity = str(dist.get("integrity", ""))
    if not integrity:
        raise ValueError("model-bank package metadata has no integrity hash")
    _verify_integrity(archive, integrity)
    providers = _extract_providers(archive)
    return {
        "schema_version": "1.0",
        "source": {
            "package": "model-bank",
            "version": str(metadata["version"]),
            "registry": REGISTRY_ROOT,
            "tarball": str(dist["tarball"]),
            "integrity": integrity,
            "git_commit": str(metadata.get("gitHead", "")),
            "license": "LobeHub Community License",
            "license_url": LICENSE_URL,
        },
        "provider_count": len(providers),
        "model_count": sum(len(models) for models in providers.values()),
        "providers": providers,
    }


def _serialized(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def sync(*, version: str, output: Path, check: bool) -> bool:
    metadata = _package_metadata(version)
    tarball = str(metadata.get("dist", {}).get("tarball", ""))
    if not tarball.startswith("https://registry.npmjs.org/model-bank/-/"):
        raise ValueError("model-bank package returned an unexpected tarball URL")
    archive = _request_bytes(tarball)
    content = _serialized(build_snapshot(metadata, archive))
    if check:
        return output.exists() and output.read_text(encoding="utf-8") == content
    _write_atomic(output, content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="latest", help="NPM model-bank version or dist-tag")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail when the checked-in snapshot is stale")
    args = parser.parse_args()
    try:
        current = sync(version=args.version, output=args.output, check=args.check)
    except (KeyError, OSError, UnicodeError, ValueError, tarfile.TarError) as exc:
        print(f"LobeHub model-bank sync failed: {exc}", file=sys.stderr)
        return 1
    if args.check and not current:
        print(f"LobeHub model names are stale: {args.output}", file=sys.stderr)
        return 1
    action = "verified" if args.check else "updated"
    print(f"LobeHub model names {action}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
