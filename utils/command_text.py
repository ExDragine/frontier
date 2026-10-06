"""Shared helpers for text commands that carry a slash/alias prefix."""

from collections.abc import Iterable

__all__ = ["strip_command_prefix"]


def strip_command_prefix(text: str, prefixes: Iterable[str]) -> str:
    """Strip the longest matching command prefix and return the remaining argument text.

    Matching is case-insensitive on both sides and the text is stripped before and
    after the prefix. Longest-first ordering lets a longer alias win when two
    prefixes overlap. When nothing matches, the stripped text is returned unchanged.
    """
    stripped = text.strip()
    for prefix in sorted(prefixes, key=len, reverse=True):
        if stripped.lower().startswith(prefix.lower()):
            return stripped[len(prefix) :].strip()
    return stripped
