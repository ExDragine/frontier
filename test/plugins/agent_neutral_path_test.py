"""Focused tests for the production QQ neutral boundary."""

# ruff: noqa: S101

from types import SimpleNamespace

import pytest

from utils.agent_protocol import AgentArtifact, AgentResponse
from utils.delivery import DeliveryResult


def _context(agent, **overrides):
    values = {
        "event": SimpleNamespace(self_id="42"),
        "user_id": "7",
        "user_name": "Alice",
        "event_id": 9,
        "group_id": 100,
        "msg_time": 1_000,
        "text": "hello",
        "quoted_images": [],
        "images": [],
        "videos": [],
        "audio": [],
        "recent_images": [],
        "attachments": [],
        "reply_to": None,
        "reply_seq": None,
        "direct_mention": True,
        "message_id": None,
    }
    values.update(overrides)
    return agent.AgentRequestContext(**values)


@pytest.fixture
def agent(monkeypatch):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins.agent import handlers

    return handlers


def test_neutral_path_accepts_all_normalized_message_shapes(agent, monkeypatch):
    context = _context(agent)
    assert agent._qq_neutral_eligible(context, None) is True
    assert agent._qq_neutral_eligible(_context(agent, group_id=None), None) is True
    assert agent._qq_neutral_eligible(_context(agent, images=[b"image"]), None) is True
    assert agent._qq_neutral_eligible(_context(agent, audio=[b"audio"]), None) is True
    assert agent._qq_neutral_eligible(_context(agent, videos=[b"video"]), None) is True
    assert agent._qq_neutral_eligible(
        _context(agent, images=[b"image"], attachments=[{"kind": "image", "path": "/memory/image.png"}]), None
    ) is True
    assert agent._qq_neutral_eligible(
        _context(agent, current_attachments=[{"kind": "file", "path": "/memory/file.txt"}]), None
    ) is True
    assert agent._qq_neutral_eligible(
        _context(agent, recent_attachments=[{"kind": "file", "path": "/memory/recent.txt"}]), None
    ) is True
    assert agent._qq_neutral_eligible(
        _context(agent, recent_attachments=[{"path": "/memory/unknown.bin"}]), None
    ) is True
    assert agent._qq_neutral_eligible(_context(agent, recent_images=[b"recent-image"]), None) is True
    assert agent._qq_neutral_eligible(_context(agent, reply_to={"message_id": "1"}), None) is True
    assert agent._qq_neutral_eligible(_context(agent, reply_seq=17), None) is True
    assert agent._qq_neutral_eligible(
        _context(agent, reply_seq=17, reply_to={"message_id": "17", "content": "quoted"}), None
    ) is True
    assert agent._qq_neutral_eligible(_context(agent, reply_to={"message_id": "1"}, attachments=[{"path": "x"}]), None) is True
    assert agent._qq_neutral_eligible(context, object()) is True

    monkeypatch.setattr(agent.EnvConfig, "SESSIONS", SimpleNamespace(enabled=True))
    assert agent._qq_neutral_eligible(_context(agent, message_id=11), None) is True


@pytest.mark.asyncio
async def test_agent_failure_sends_one_notice_without_legacy_retry(agent, monkeypatch):
    sent = []

    class FailingCore:
        async def run(self, request, *, tools=()):
            raise RuntimeError("boom")

    async def send_messages(*args, **kwargs):
        sent.append((args, kwargs))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: FailingCore())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(_context(agent), [])
    assert (handled, result) == (True, True)
    assert len(sent) == 1
    assert "boom" not in sent[0][0][2]["messages"][0].content


@pytest.mark.asyncio
async def test_private_neutral_uses_neutral_delivery_scope(agent, monkeypatch):
    sent = []

    class Core:
        async def run(self, request, *, tools=()):
            assert request.current.conversation.kind == "private"
            return AgentResponse(text="private reply")

    async def send_messages(group_id, message_id, response):
        sent.append((group_id, message_id, response))
        return DeliveryResult(attempted=1, sent=1)

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(_context(agent, group_id=None), [])
    assert (handled, result) == (True, True)
    assert len(sent) == 1
    assert sent[0][0:2] == (None, None)


@pytest.mark.asyncio
async def test_session_neutral_forwards_lease_and_settles_after_delivery(agent, monkeypatch):
    seen = []
    settled = []
    session = SimpleNamespace(current_id="qq:42:message:9")

    class Core:
        async def run(self, request, *, tools=()):
            seen.append(request.session_turn)
            return AgentResponse(text="session reply")

    async def send_messages(*args, **kwargs):
        return DeliveryResult(attempted=1, sent=1, message_ids=(123,))

    async def settle(lease, **kwargs):
        settled.append((lease, kwargs))

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())
    monkeypatch.setattr(agent, "_settle_session", settle)

    handled, result = await agent._run_qq_neutral(_context(agent, message_id=9), [], session_turn=session)

    assert (handled, result) == (True, True)
    assert seen == [session]
    assert settled[0][0] is session
    assert settled[0][1]["delivered"] is True
    assert settled[0][1]["message_id"] == 123
    assert settled[0][1]["content"] == "session reply"


@pytest.mark.asyncio
async def test_media_neutral_passes_current_downloads_through_neutral_message(agent, monkeypatch):
    seen = []

    class Core:
        async def run(self, request, *, tools=()):
            seen.append(request.current.parts)
            return AgentResponse(text="media reply")

    async def send_messages(*args, **kwargs):
        return DeliveryResult(attempted=1, sent=1)

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(
        _context(agent, images=[b"image"], audio=[b"audio"], videos=[b"video"]), []
    )
    assert (handled, result) == (True, True)
    assert [type(part).__name__ for part in seen[0]] == [
        "TextPart",
        "ImagePart",
        "AudioPart",
        "VideoPart",
    ]


@pytest.mark.asyncio
async def test_file_neutral_passes_current_staged_ref_through_neutral_message(agent, monkeypatch):
    seen = []

    class Core:
        async def run(self, request, *, tools=()):
            seen.append(request.current.parts)
            return AgentResponse(text="file reply")

    async def send_messages(*args, **kwargs):
        return DeliveryResult(attempted=1, sent=1)

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(
        _context(agent, current_attachments=[{"kind": "file", "path": "/memory/report.txt", "file_name": "report.txt"}]),
        [],
    )

    assert (handled, result) == (True, True)
    assert [type(part).__name__ for part in seen[0]] == ["TextPart", "FilePart"]
    assert seen[0][1].url == "/memory/report.txt"


@pytest.mark.asyncio
async def test_recent_media_neutral_preserves_source_marker_and_parts(agent, monkeypatch):
    seen = []

    class Core:
        async def run(self, request, *, tools=()):
            seen.append(request.current.parts)
            return AgentResponse(text="recent reply")

    async def send_messages(*args, **kwargs):
        return DeliveryResult(attempted=1, sent=1)

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(
        _context(
            agent,
            recent_images=[b"recent-image"],
            recent_attachments=[{"kind": "file", "path": "/memory/recent.txt", "file_name": "recent.txt"}],
        ),
        [],
    )

    assert (handled, result) == (True, True)
    assert [type(part).__name__ for part in seen[0]] == ["TextPart", "TextPart", "ImagePart", "FilePart"]
    assert seen[0][1].text == "[以下媒体来自用户刚才发送的历史消息]"


@pytest.mark.asyncio
async def test_quote_neutral_maps_resolved_snapshot_and_media(agent, monkeypatch):
    seen = []

    class Core:
        async def run(self, request, *, tools=()):
            seen.append(request.current)
            return AgentResponse(text="quote reply")

    async def send_messages(*args, **kwargs):
        return DeliveryResult(attempted=1, sent=1)

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(
        _context(
            agent,
            text="",
            reply_seq=8,
            reply_to={"message_id": "8", "content": "quoted", "attachments": []},
            quoted_images=[b"quoted-image"],
        ),
        [],
    )

    assert (handled, result) == (True, True)
    assert [type(part).__name__ for part in seen[0].parts] == ["TextPart", "QuotePart"]
    quote = seen[0].parts[1]
    assert [type(part).__name__ for part in quote.parts] == ["TextPart", "ImagePart"]


@pytest.mark.asyncio
async def test_history_failure_is_handled_without_legacy_retry(agent, monkeypatch):
    core_calls = []

    class Core:
        async def run(self, request, *, tools=()):
            core_calls.append(request)
            return AgentResponse(text="must not run")

    class FailedHistory:
        def __init__(self, *args, **kwargs):
            pass

        async def load(self, query):
            raise RuntimeError("history unavailable")

        async def append(self, message):
            raise AssertionError("append must not run")

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "QqHistoryStore", FailedHistory)
    monkeypatch.setattr(agent, "messages_db", SimpleNamespace())

    async def send_notice(*_args, **_kwargs):
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "send_messages", send_notice)

    handled, result = await agent._run_qq_neutral(_context(agent), [])
    assert (handled, result) == (True, True)
    assert core_calls == []


@pytest.mark.asyncio
async def test_delivery_failure_is_handled_without_retry(agent, monkeypatch):
    sent = []

    class Core:
        async def run(self, request, *, tools=()):
            return AgentResponse(text="reply")

    async def send_messages(*args, **kwargs):
        sent.append((args, kwargs))
        return DeliveryResult(attempted=1, sent=0, errors=("transport_failed",))

    class Database:
        async def count_intervening_group_messages(self, **kwargs):
            return 5

        async def insert(self, **kwargs):
            raise AssertionError("history must not append after failed delivery")

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(_context(agent), [])
    assert (handled, result) == (True, False)
    assert len(sent) == 1


@pytest.mark.asyncio
async def test_empty_success_response_is_not_persisted(agent, monkeypatch):
    sent = []

    class Core:
        async def run(self, request, *, tools=()):
            return AgentResponse(text="")

    async def send_messages(*args, **kwargs):
        sent.append((args, kwargs))
        return DeliveryResult(attempted=1, sent=1)

    class Database:
        async def insert(self, **kwargs):
            raise AssertionError("empty response must not append history")

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(_context(agent), [])
    assert (handled, result) == (True, False)
    assert sent == []


@pytest.mark.asyncio
async def test_artifact_response_is_handled_without_legacy_retry(agent, monkeypatch):
    sent = []

    class Core:
        async def run(self, request, *, tools=()):
            return AgentResponse(
                text="generated image",
                artifacts=(AgentArtifact(kind="image", data=b"image", mime_type="image/png"),),
            )

    async def send_messages(*args, **kwargs):
        sent.append((args, kwargs))
        return DeliveryResult(attempted=1, sent=1)

    async def send_artifacts(artifacts):
        sent.append(("artifacts", tuple(artifacts)))
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "FrontierAgentCore", lambda *_args, **_kwargs: Core())
    monkeypatch.setattr(agent, "send_messages", send_messages)
    monkeypatch.setattr(agent, "send_artifacts", send_artifacts)

    class Database:
        async def insert(self, **kwargs):
            return None

    monkeypatch.setattr(agent, "messages_db", Database())

    handled, result = await agent._run_qq_neutral(_context(agent), [])
    assert (handled, result) == (True, True)
    assert len(sent) == 2
    assert sent[0][0] == "artifacts"
    assert sent[1][0][2]["messages"][0].content == "generated image"


@pytest.mark.asyncio
async def test_neutral_artifact_sender_maps_file_artifacts(agent, monkeypatch):
    captured = []

    async def send_artifacts(artifacts):
        captured.extend(artifacts)
        return DeliveryResult(attempted=1, sent=1)

    monkeypatch.setattr(agent, "send_artifacts", send_artifacts)
    result = await agent._send_qq_neutral_artifacts(
        SimpleNamespace(platform="qq"),
        (AgentArtifact(kind="file", data=b"file", mime_type="text/plain", name="notes.txt"),),
    )

    assert result.successful
    assert len(captured) == 1
    assert captured[0][0].type == "file"
    assert captured[0][0].name == "notes.txt"
