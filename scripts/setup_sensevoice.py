"""Fetch a pinned official SenseVoice Q8 runtime and weights; never execute downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "runtime-llamacpp-v0.2.1"
ASSETS = (
    (
        "runtime.zip",
        f"https://github.com/QwenAudio/SenseVoice/releases/download/{RELEASE}/funasr-llamacpp-windows-x64.zip",
        "b8f2b8f241b57921d82d64068d9b5695629779f3db5f3205a730cb3810232bb4",
    ),
    (
        "sensevoice-small-q8.gguf",
        "https://huggingface.co/FunAudioLLM/SenseVoiceSmall-GGUF/resolve/"
        "90c1c61912018b70ada0fcc024ea24aca62f2e63/sensevoice-small-q8.gguf",
        "4ae45c94422de949b387e2e0fb10d7e14e4c42c69db30c3444ecc7d4b844b7c5",
    ),
    (
        "fsmn-vad.gguf",
        "https://huggingface.co/FunAudioLLM/fsmn-vad-GGUF/resolve/"
        "6840bae4c5c92ee8c04faaf4db23dd0105098d7f/fsmn-vad.gguf",
        "1270f2559c495f4e7b6e739541151027d360761a3fda43fc147034f5719f5479",
    ),
)
AVX2_RUNTIME = (
    "runtime-avx2.zip",
    f"https://github.com/QwenAudio/SenseVoice/releases/download/{RELEASE}/funasr-llamacpp-windows-x64-avx2.zip",
    "67e428a91614f8a0c1d53dc2d79cce8efc7916c030ae2ddce2cbcf667ec1c502",
)


def _sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def download_verified(target: Path, url: str, expected: str) -> None:
    if target.is_file() and _sha256(target) == expected:
        return
    partial = target.with_suffix(target.suffix + ".part")
    try:
        # URLs are a fixed HTTPS manifest, not user-provided URLs.
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as output:  # noqa: S310
            shutil.copyfileobj(response, output)
        if _sha256(partial) != expected:
            raise ValueError(f"SHA-256 mismatch: {target.name}")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)


def install(destination: Path, *, avx2: bool = False) -> None:
    if os.name != "nt":
        raise SystemExit(
            "This installer targets Windows x64. On other platforms, install the official native runtime."
        )
    destination.mkdir(parents=True, exist_ok=True)
    assets = (AVX2_RUNTIME, *ASSETS[1:]) if avx2 else ASSETS
    for name, url, expected in assets:
        print(f"Checking {name}...", flush=True)
        download_verified(destination / name, url, expected)
    runtime = destination / ("runtime-avx2" if avx2 else "runtime")
    runtime.mkdir(exist_ok=True)
    # Extract exactly one executable; never trust archive member paths.
    executable = runtime / "llama-funasr-sensevoice.exe"
    with zipfile.ZipFile(destination / assets[0][0]) as archive:
        matches = [item for item in archive.infolist() if Path(item.filename).name == executable.name]
        if len(matches) != 1:
            raise ValueError("Official runtime archive does not contain exactly one SenseVoice executable")
        with archive.open(matches[0]) as source, executable.open("wb") as output:
            shutil.copyfileobj(source, output)
    (destination / ("manifest-avx2.json" if avx2 else "manifest.json")).write_text(
        json.dumps(
            {
                "release": RELEASE,
                "assets": [{"file": name, "url": url, "sha256": digest} for name, url, digest in assets],
                "executable_sha256": _sha256(executable),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Verified runtime ready: {executable}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "cache/speech/sensevoice")
    parser.add_argument("--avx2", action="store_true", help="Requires AVX2, FMA, F16C and BMI2 CPU support")
    args = parser.parse_args()
    install(args.destination.resolve(), avx2=args.avx2)


if __name__ == "__main__":
    main()
