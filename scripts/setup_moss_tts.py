"""Prefetch the pinned official MOSS-TTS-Nano PyTorch assets."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.moss_tts_assets import install  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "cache/speech/moss-tts")
    install(parser.parse_args().destination)
