"""Durable media paths must survive the current-message capability boundary."""

# ruff: noqa: S101

import json
from datetime import UTC, datetime

import pytest

from plugins.agent.adapters.qq import QqMessageAdapter
from utils.agent_protocol import AgentRequest, AudioPart, FilePart, ImagePart, TextPart, VideoPart
from utils.agents import inputs
from utils.agents.neutral_core import _current_message


@pytest.mark.parametrize("kind,part_type", [("image", ImagePart), ("audio", AudioPart), ("video", VideoPart)])
@pytest.mark.parametrize("recent", [False, True])
def test_media_reference_survives_without_model_media_support(monkeypatch, kind, part_type, recent):
    path = f"/memory/group-100/{kind}/sample.bin"
    reference = {"kind": kind, "file_name": "sample.bin", "path": path}
    media_key = {"image": "images", "audio": "audio", "video": "videos"}[kind]
    kwargs = {media_key: (b"media-bytes",)}
    if recent:
        kwargs["recent_attachments"] = (reference,)
    else:
        kwargs["attachments"] = (reference,)
    message = QqMessageAdapter("42").text_message(
        message_id=9, group_id=100, user_id=7, user_name="Alice",
        text="Read the attachment", created_at=datetime(2026, 1, 1, tzinfo=UTC), **kwargs,
    )
    # The reference adds text, rather than another media payload consuming budget.
    assert sum(isinstance(part, part_type) for part in message.parts) == 1
    refs = [json.loads(part.text)["attachment"] for part in message.parts
            if isinstance(part, TextPart) and part.text.startswith('{"attachment":')]
    assert refs == [reference]

    request = AgentRequest("r", message, (), "group-100", frozenset(), "default")
    monkeypatch.setattr(inputs, "model_supports", lambda *_args, **_kwargs: False)
    bounded = inputs.filter_messages_for_model_capabilities([_current_message(request)], "text-only")
    assert path in str(bounded[0]["content"])
    assert "不支持" in str(bounded[0]["content"])


def test_file_refs_keep_their_native_parts_and_invalid_refs_are_ignored():
    parts = QqMessageAdapter._file_parts((
        {"kind": "file", "path": "/memory/report.txt", "file_name": "report.txt"},
        {"kind": "image"},
        {"kind": "unknown", "path": "/memory/unknown"},
    ))
    assert parts == [FilePart(url="/memory/report.txt", name="report.txt")]
