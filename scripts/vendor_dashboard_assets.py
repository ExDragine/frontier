"""Vendor the pinned Dashboard front-end assets so it can run without a CDN.

`plugins/dashboard/web/index.html` loads Vue, Vue Router and the Tailwind Play
CDN from public CDNs unless the identical pinned files are present under
`plugins/dashboard/web/vendor/`.  Run this script once on a machine with
network access (or inside the image build) to remove that dependency:

    uv run python scripts/vendor_dashboard_assets.py          # download what is missing
    uv run python scripts/vendor_dashboard_assets.py --check  # report status, never touches the network

`--check` exits non-zero while any pinned file is missing, so it can gate a
deployment that is supposed to be CDN-free.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "plugins" / "dashboard" / "web"
VENDOR_DIR = WEB_DIR / "vendor"
INDEX_HTML = WEB_DIR / "index.html"

_USER_AGENT = "Mozilla/5.0 (compatible; frontier-dashboard-vendor/1.0)"

# Keep in sync with the `<script src="/dashboard/vendor/...">` tags and the
# pinned CDN fallback URLs in index.html; test/plugins/dashboard_vendor_test.py
# fails when these two files disagree.
ASSETS: tuple[tuple[str, str], ...] = (
    ("tailwindcss.js", "https://cdn.tailwindcss.com/3.4.17"),
    ("vue.global.prod.js", "https://unpkg.com/vue@3.5.13/dist/vue.global.prod.js"),
    ("vue-router.global.prod.js", "https://unpkg.com/vue-router@4.5.0/dist/vue-router.global.prod.js"),
)


@dataclass(frozen=True, slots=True)
class Asset:
    filename: str
    url: str

    @property
    def local_source(self) -> str:
        return f"/dashboard/vendor/{self.filename}"


def assets() -> tuple[Asset, ...]:
    return tuple(Asset(filename, url) for filename, url in ASSETS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def missing_assets(vendor_dir: Path | None = None) -> list[Asset]:
    directory = vendor_dir if vendor_dir is not None else VENDOR_DIR
    return [asset for asset in assets() if not (directory / asset.filename).is_file()]


def download(asset: Asset, vendor_dir: Path | None = None) -> Path:
    directory = vendor_dir if vendor_dir is not None else VENDOR_DIR
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / asset.filename
    # cdn.tailwindcss.com answers 403 to the default Python-urllib user agent.
    request = urllib.request.Request(asset.url, headers={"User-Agent": _USER_AGENT})  # noqa: S310 (pinned https)
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 (pinned https URLs)
        payload = response.read()
    destination.write_bytes(payload)
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report status without downloading")
    args = parser.parse_args(argv)

    missing = missing_assets()
    if args.check:
        for asset in assets():
            state = "missing" if asset in missing else "present"
            print(f"{state:>8}  {asset.filename}  ({asset.url})")
        if missing:
            print(f"{len(missing)} pinned asset(s) missing: the Dashboard still needs a CDN.", file=sys.stderr)
            return 1
        print("All pinned Dashboard assets are vendored; no CDN request is made.")
        return 0

    for asset in missing:
        path = download(asset)
        print(f"downloaded {asset.filename}: {path.stat().st_size} bytes sha256={sha256(path)}")
    for asset in assets():
        if asset not in missing:
            path = VENDOR_DIR / asset.filename
            print(f"kept      {asset.filename}: sha256={sha256(path)}")
    print(f"vendor directory: {VENDOR_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
