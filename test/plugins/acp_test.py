# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from plugins import acp


def _event():
    return SimpleNamespace(
        data=SimpleNamespace(segments=[], group=None, message_seq=9),
        get_user_id=lambda: "42",
    )


def test_parse_acp_command_supports_agent_and_control_actions():
    run = acp._parse_command("/acp --agent demo inspect this")
    reset = acp._parse_command("/acp --reset --agent=demo")

    assert (run.action, run.agent_name, run.prompt) == ("run", "demo", "inspect this")
    assert (reset.action, reset.agent_name, reset.prompt) == ("reset", "demo", "")


def test_acp_command_reuses_agent_access_policy(monkeypatch):
    monkeypatch.setattr(acp.EnvConfig, "AGENT_WHITELIST_MODE", False)
    monkeypatch.setattr(acp.EnvConfig, "AGENT_BLACKLIST_GROUP_LIST", [])
    monkeypatch.setattr(acp.EnvConfig, "AGENT_BLACKLIST_PERSON_LIST", [42])

    assert acp._has_agent_access(_event()) is False


@pytest.mark.asyncio
async def test_acp_command_runs_prompt_with_media(monkeypatch):
    captured = {}
    sent_responses = []

    async def fake_extract(_segments):
        return "/acp --agent demo build it", [b"lazy-image"], [b"lazy-audio"], []

    async def fake_download(images, audios, videos):
        assert images == [b"lazy-image"]
        assert audios == [b"lazy-audio"]
        assert videos == []
        return [b"image"], [b"audio"], []

    async def fake_chat(prompt, **kwargs):
        captured["prompt"] = prompt
        captured.update(kwargs)
        return {"response": {"messages": [SimpleNamespace(content="result")]}, "uni_messages": []}

    async def fake_send_messages(group_id, event_id, response):
        sent_responses.append((group_id, event_id, response))

    async def fake_sanitize(text):
        return text

    monkeypatch.setattr(acp, "message_extract", fake_extract)
    monkeypatch.setattr(acp, "download_media", fake_download)
    monkeypatch.setattr(acp.acp_agent, "chat_agent", fake_chat)
    monkeypatch.setattr(acp, "send_messages", fake_send_messages)
    monkeypatch.setattr(acp, "sanitize_outgoing_text", fake_sanitize)

    await acp.handle_acp(_event())

    assert captured["prompt"] == "build it"
    assert captured["workspace_key"] == "dm:42"
    assert captured["agent_name"] == "demo"
    assert [item.kind for item in captured["media"]] == ["image", "audio"]
    assert sent_responses[0][:2] == (None, 9)
