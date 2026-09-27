"""Platform-neutral identity helpers used at the Agent boundary."""

import hashlib
import re

# Percent escapes are safe filesystem characters and are used by the
# orchestrator when encoding opaque platform identifiers.
_SAFE_WORKSPACE_KEY = re.compile(r"^[A-Za-z0-9_.:%-]+$")


def normalize_workspace_key(value: str) -> str:
    """Return a deterministic filesystem-safe workspace key.

    Safe keys are preserved for readable diagnostics and legacy compatibility.
    Opaque platform identifiers containing separators or control characters are
    hashed so they cannot escape the workspace root.
    """

    if value and _SAFE_WORKSPACE_KEY.fullmatch(value) and value not in {".", ".."}:
        return value
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"workspace-h-{digest}"


__all__ = ["normalize_workspace_key"]
