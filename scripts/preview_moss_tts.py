"""Generate local audition files without reading the bot's real configuration."""

import argparse
import asyncio
import json
import os
import platform
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


async def preview(args) -> None:
    import psutil

    from utils.configs import SpeechSynthesisConfig
    from utils.speech_synthesis import synthesize_speech

    settings = SpeechSynthesisConfig(
        enabled=True,
        model_dir=str(args.model_dir.resolve()),
        max_cpu_cores=args.cores,
        timeout_seconds=args.timeout,
    )
    process = psutil.Process()
    task = asyncio.create_task(synthesize_speech(args.text, settings=settings))
    peak_bytes = 0
    while not task.done():
        total = 0
        for child in process.children(recursive=True):
            try:
                total += child.memory_info().rss
            except psutil.NoSuchProcess:
                pass
        peak_bytes = max(peak_bytes, total)
        await asyncio.sleep(0.05)
    result = await task
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".wav").write_bytes(result.wav)
    args.output.with_suffix(".silk").write_bytes(result.silk)
    metadata = {
        "backend": "pytorch-cpu",
        "voice": settings.voice,
        "text": args.text,
        "audio_seconds": result.audio_seconds,
        "elapsed_seconds": result.elapsed_seconds,
        "real_time_factor": result.elapsed_seconds / result.audio_seconds,
        "peak_child_rss_mib": peak_bytes / 1024**2,
        "cpu_limit": args.cores,
        "machine": platform.processor(),
        "os": platform.platform(),
        "host_memory_gib": psutil.virtual_memory().total / 1024**3,
        "wav": str(args.output.with_suffix(".wav").resolve()),
    }
    args.output.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="你好，我是小芙。这是本地生成的语音，今天也要开心一点。")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "cache/speech/moss-tts")
    parser.add_argument("--output", type=Path, default=ROOT / "cache/speech/previews/moss-native")
    parser.add_argument("--cores", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="frontier-tts-config-") as temporary:
        config = Path(temporary) / "env.toml"
        config.write_text(
            'config_version = 2\n[dashboard]\npassword = "preview-local"\n'
            'jwt_secret = "preview-isolated-secret-only"\n',
            encoding="utf-8",
        )
        os.environ["FRONTIER_CONFIG"] = str(config)
        sys.path.insert(0, str(ROOT))
        asyncio.run(preview(args))


if __name__ == "__main__":
    main()
