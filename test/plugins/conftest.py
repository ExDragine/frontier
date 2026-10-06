# ruff: noqa: S101

"""Shared stubs for the plugin tests.

Only stand-ins with a single, unambiguous meaning live here.  Fakes whose
behaviour differs per test (a send that raises, a no-op send, a recorded
delivery target) stay inline in the test that needs them so the difference
stays visible at the call site.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def unimessage_text_sends(monkeypatch: pytest.MonkeyPatch):
    """Install a ``UniMessage`` stand-in that records the text it is asked to send.

    ``install(module)`` swaps ``module.UniMessage`` for a stub whose
    ``.text(value).send()`` appends ``value`` to the returned list, i.e. the
    user-visible output the toolbox tests assert on.
    """

    def install(module) -> list[str]:
        sent: list[str] = []

        class DummyMessage:
            def __init__(self, text: str) -> None:
                self.text = text

            async def send(self, *_args, **_kwargs) -> None:
                sent.append(self.text)

        class DummyUniMessage:
            @classmethod
            def text(cls, text: str) -> DummyMessage:
                return DummyMessage(text)

        monkeypatch.setattr(module, "UniMessage", DummyUniMessage)
        return sent

    return install
