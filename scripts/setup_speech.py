"""Prefetch recognition and synthesis assets without enabling either feature."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.moss_tts_assets import install as install_synthesis  # noqa: E402
from utils.sensevoice_assets import install as install_recognition  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=("all", "recognition", "synthesis"), default="all")
    parser.add_argument("--destination", type=Path, default=ROOT / "cache/speech")
    args = parser.parse_args()
    if args.only in {"all", "recognition"}:
        install_recognition(args.destination / "sensevoice")
    if args.only in {"all", "synthesis"}:
        install_synthesis(args.destination / "moss-tts")
