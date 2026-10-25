"""Media-only inputs remain executable after the reply gateway has passed."""

# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from utils.agents.message_envelope import content_for_persisted_images


@pytest.fixture
def agent(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins.agent import handlers

    return handlers


def _context(agent, **overrides):
    values = {
        "event": SimpleNamespace(self_id="42"),
        "user_id": "7",
        "user_name": "Alice",
        "event_id": 9,
        "group_id": None,
        "msg_time": 1_000,
        "text": "",
        "quoted_images": [],
        "images": [],
        "videos": [],
        "direct_mention": False,
    }
    values.update(overrides)
    return agent.AgentRequestContext(**values)


@pytest.mark.parametrize("payload", [
    {"images": [b"image"]},
    {"audio": [b"audio"]},
    {"videos": [b"video"]},
    {"quoted_images": [b"quote-image"]},
    {"recent_images": [b"recent-image"]},
    {"attachments": [{"kind": "image", "path": "/memory/image.png"}]},
    {"current_attachments": [{"kind": "file", "path": "/memory/file.txt"}]},
    {"recent_attachments": [{"kind": "file", "path": "/memory/recent.txt"}]},
    {"reply_to": {"message_id": "8", "content": "quoted"}},
    {"reply_seq": 8},
])
def test_empty_text_with_payload_is_an_agent_turn(agent, payload):
    assert agent._qq_neutral_eligible(_context(agent, **payload))


def test_truly_empty_unaddressed_input_is_not_an_agent_turn(agent):
    assert not agent._qq_neutral_eligible(_context(agent, text=" \n "))


@pytest.mark.asyncio
async def test_persisted_image_without_placeholder_reaches_neutral_runner(agent, monkeypatch):
    captured = []

    async def run(context, history, session_turn=None):
        captured.append((context, history, session_turn))
        return True

    monkeypatch.setattr(agent, "_run_qq_neutral", run)
    text = content_for_persisted_images("[图片]", 1)
    assert text == ""
    context = _context(agent, text=text, images=[b"image"])
    history = [{"role": "user", "content": "previous"}]

    assert await agent._execute_agent_request(context, history)
    assert captured == [(context, history, None)]
