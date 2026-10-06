# ruff: noqa: S101

"""Shared stubs for the Milky platform tool tests.

The five ``milky_*_test.py`` modules each emulate a different slice of the
Milky adapter, but every one of them needs the same recording shell: a ``calls``
list plus a method that forwards keyword arguments to the tool under test.  The
slice each module emulates is expressed as a *response table* so the per-test
differences (return values, result objects built from the forwarded arguments)
stay explicit instead of collapsing into one do-everything dummy.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest


class MilkyBotStub:
    """Record Milky API calls and reply from a per-test response table.

    ``responses`` maps a Milky API method name to the value the tool should
    receive.  A callable value is invoked with the forwarded keyword arguments,
    which covers APIs whose objects echo their own request (``get_message``).
    Methods that return ``None`` need no entry at all.  Every call is recorded
    as ``(method, kwargs)`` so tests keep pinning the exact platform arguments
    a tool produced.
    """

    def __init__(self, responses: Mapping[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._responses: dict[str, Any] = dict(responses or {})

    def __getattr__(self, name: str) -> Callable[..., Any]:
        if name.startswith("_"):
            raise AttributeError(name)

        async def milky_call(**kwargs: Any) -> Any:
            self.calls.append((name, kwargs))
            response = self._responses.get(name)
            return response(kwargs) if callable(response) else response

        return milky_call


@pytest.fixture
def install_milky_bot(monkeypatch: pytest.MonkeyPatch):
    """Bind a :class:`MilkyBotStub` to a tool module's ``get_bot``."""

    def _install(module, responses: Mapping[str, Any] | None = None) -> MilkyBotStub:
        bot = MilkyBotStub(responses)
        monkeypatch.setattr(module, "get_bot", lambda: bot)
        return bot

    return _install
