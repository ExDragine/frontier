# ruff: noqa: S101

from types import SimpleNamespace

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.message import Message
from nonebot.adapters.milky.model.common import Friend, FriendCategory
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebug import App

from utils import speech_recognition as speech
from utils.configs import SpeechRecognitionConfig


def _event():
    incoming = IncomingMessage(
        message_scene="friend",
        peer_id=456,
        message_seq=1,
        sender_id=456,
        time=0,
        segments=[
            {"type": "record", "data": {"resource_id": "voice", "temp_url": "https://example.com/a", "duration": 1}}
        ],
        friend=Friend(
            user_id=456,
            nickname="u",
            sex="unknown",
            qid="",
            remark="",
            category=FriendCategory(category_id=0, category_name="default"),
        ),
        group=None,
        group_member=None,
    )
    return MessageEvent(data=incoming, to_me=True, time=0, self_id="1", message=Message(), original_message=Message())


@pytest.mark.asyncio
@pytest.mark.parametrize("gate_allowed", [True, False])
@pytest.mark.parametrize("recognition_fails", [False, True])
async def test_voice_gate_precedes_download_and_asr_then_checks_and_persists_text(  # noqa: C901
    monkeypatch,
    gate_allowed,
    recognition_fails,
):
    import nonebot

    monkeypatch.setattr(nonebot, "require", lambda *_args, **_kwargs: None)
    from plugins.agent import handlers as agent

    calls, captured = [], {}

    class Database:
        async def insert(self, **kwargs):
            captured["insert"] = kwargs
            return SimpleNamespace(inserted=True, message_id=101)

        async def prepare_message(self, *_args, **_kwargs):
            return []

        async def insert_media(self, **kwargs):
            calls.append("persist_audio")
            assert kwargs["media"][0].data == b"downloaded-voice"
            return []

        async def update_message_normalization(self, **kwargs):
            captured["update"] = kwargs

    async def download():
        calls.append("download")
        return b"downloaded-voice"

    async def extract(_segments):
        return "", [], [download], []

    async def gate(*_args):
        calls.append("gate")
        return gate_allowed

    async def recognize(data, **_kwargs):
        calls.append("asr")
        assert data == b"downloaded-voice"
        if recognition_fails:
            raise speech.SpeechRecognitionError("timeout")
        return speech.Transcription("明天北京的天气怎么样", 1, 0.1)

    async def check(text, _images):
        calls.append("check")
        captured["checked"] = text
        return "Safe"

    async def process(context, _history):
        calls.append("agent")
        captured["context"] = context

    monkeypatch.setattr(agent, "messages_db", Database())
    monkeypatch.setattr(agent, "get_bot", lambda: object())
    monkeypatch.setattr(agent, "message_extract", extract)
    monkeypatch.setattr(agent, "message_gateway", gate)
    monkeypatch.setattr(agent, "message_check", check)
    monkeypatch.setattr(agent, "_process_queued_agent_request", process)
    monkeypatch.setattr(speech, "transcribe_audio", recognize)
    settings = SpeechRecognitionConfig(enabled=True)
    monkeypatch.setattr(agent.EnvConfig, "SPEECH_RECOGNITION", settings)
    # The suite reloads configs between tests; collected helpers retain their
    # original class while the plugin can be imported after the reload.
    monkeypatch.setattr(speech.EnvConfig, "SPEECH_RECOGNITION", settings)
    monkeypatch.setattr(agent.EnvConfig, "CONTENT_CHECK_ENABLED", True)

    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, _event())
        ctx.should_finished()

    if not gate_allowed:
        assert calls == ["gate"]
        return
    assert calls == ["gate", "download", "persist_audio", "asr", "check", "agent"]
    assert captured["context"].audio == []
    assert captured["update"]["message_id"] == 101
    assert captured["update"]["raw_segments_json"] is None
    assert "语音" in captured["insert"]["content"]
    if recognition_fails:
        assert "识别失败" in captured["checked"] and "timeout" in captured["context"].text
    else:
        assert "明天北京的天气怎么样" in captured["checked"]
        assert "明天北京的天气怎么样" in captured["update"]["content"]
