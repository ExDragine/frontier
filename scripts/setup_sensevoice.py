"""Prefetch the pinned official Windows x64 SenseVoice Q8 runtime and weights."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.sensevoice_assets import install  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "cache/speech/sensevoice")
    parser.add_argument("--avx2", action="store_true", help="Requires AVX2, FMA, F16C and BMI2 CPU support")
    args = parser.parse_args()
    install(args.destination, avx2=args.avx2)


if __name__ == "__main__":
    main()
