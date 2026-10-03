"""Validate relative links in Markdown files.

This intentionally checks only repository-local links.  Remote URLs are
outside the scope of CI and should not make a build depend on third-party
availability.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def _target_path(source: Path, target: str) -> Path | None:
    target = target.strip().strip("<>")
    if not target or target.startswith(("#", "/")):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    raw_path = unquote(parsed.path)
    if not raw_path:
        return None
    return (source.parent / raw_path).resolve()


def find_broken_links(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for source in sorted(root.rglob("*.md")):
        if any(part in {".git", ".venv", "node_modules"} for part in source.parts):
            continue
        text = source.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).split(" ", 1)[0]
            path = _target_path(source, target)
            if path is None:
                continue
            try:
                path.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{source.relative_to(root)}: link escapes repository: {target}")
                continue
            if not path.exists():
                errors.append(f"{source.relative_to(root)}: missing local link: {target}")
    return errors


def main() -> int:
    errors = find_broken_links()
    if errors:
        print("Broken local Markdown links:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Local Markdown links are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
