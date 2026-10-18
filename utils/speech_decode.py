"""Decode Tencent/standard SILK in a disposable, bounded worker process.

Do not import the application config here: this file is also a child entry point.
"""

import argparse
import io
import wave
from collections.abc import Buffer
from pathlib import Path

SAMPLE_RATE = 16000


class _BoundedPcm(io.BytesIO):
    def __init__(self, limit: int):
        super().__init__()
        self.limit = limit

    def write(self, buffer: Buffer, /) -> int:
        with memoryview(buffer) as data:
            if self.tell() + data.nbytes > self.limit:
                raise ValueError("audio_duration_limit")
            return super().write(data)


def decode_silk(source: Path, target: Path, max_seconds: int) -> None:
    import pysilk

    with source.open("rb") as audio, _BoundedPcm(SAMPLE_RATE * 2 * max_seconds) as pcm:
        pysilk.decode(audio, pcm, SAMPLE_RATE)
        pcm.seek(0)
        with wave.open(str(target), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(SAMPLE_RATE)
            output.writeframes(pcm.getbuffer())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("max_seconds", type=int)
    args = parser.parse_args()
    decode_silk(args.source, args.target, args.max_seconds)


if __name__ == "__main__":
    main()
