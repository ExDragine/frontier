# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from plugins import dsh


class DummyMessage:
    def __init__(self, text, sent):
        self.text = text
        self.sent = sent

    async def send(self, *_args, **_kwargs):
        self.sent.append(self.text)


class DummyUniMessage:
    sent = []

    @classmethod
    def text(cls, text):
        return DummyMessage(text, cls.sent)


def _event():
    return SimpleNamespace(
        data=SimpleNamespace(
            segments=[],
            group=None,
            message_seq=7,
        ),
        get_user_id=lambda: "42",
    )


@pytest.mark.asyncio
async def test_dsh_command_runs_explicit_prompt(monkeypatch):
    sent_responses = []
    captured = {}

    async def fake_extract(_segments):
        return "/dsh build it", [], [], []

    async def fake_chat(prompt, **kwargs):
        captured["prompt"] = prompt
        captured.update(kwargs)
        return {"response": {"messages": [SimpleNamespace(content="result")]}, "uni_messages": []}

    async def fake_send_messages(group_id, event_id, response):
        sent_responses.append((group_id, event_id, response))

    async def fake_sanitize(text):
        return text

    monkeypatch.setattr(dsh.EnvConfig, "AGENT_JOB_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(dsh, "message_extract", fake_extract)
    monkeypatch.setattr(dsh.dsh_agent, "chat_agent", fake_chat)
    monkeypatch.setattr(dsh, "send_messages", fake_send_messages)
    monkeypatch.setattr(dsh, "sanitize_outgoing_text", fake_sanitize)

    await dsh.handle_dsh(_event())

    assert captured["prompt"] == "build it"
    assert captured["workspace_key"] == "dm:42"
    assert captured["session_id"].startswith("frontier-")
    assert sent_responses[0][:2] == (None, 7)
