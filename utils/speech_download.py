"""Atomic, verified speech asset downloads shared by runtime and setup CLIs."""

import hashlib
import shutil
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile

from filelock import FileLock


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def installation_lock(destination: Path) -> FileLock:
    destination.mkdir(parents=True, exist_ok=True)
    return FileLock(str(destination / ".install.lock"), timeout=600)


def download_verified(target: Path, url: str, expected: str) -> None:
    if target.is_file() and sha256(target) == expected:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", suffix=".part", delete=False) as output:
        partial = Path(output.name)
        try:
            with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
                shutil.copyfileobj(response, output)
        except BaseException:
            output.close()
            partial.unlink(missing_ok=True)
            raise
    try:
        if sha256(partial) != expected:
            raise ValueError("Speech asset checksum mismatch")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
