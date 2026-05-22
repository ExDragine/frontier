# ruff: noqa: S101

import types

import pytest
from nonebot.adapters.milky.event import MessageEvent
from nonebot.adapters.milky.model.common import Group, Member
from nonebot.adapters.milky.model.message import IncomingMessage
from nonebot_plugin_alconna import UniMessage
from nonebug import App

from plugins import playground


class AllowLimiter:
    def check(self, *_args, **_kwargs):
        return types.SimpleNamespace(allowed=True, retry_after_seconds=0)


class DenyLimiter:
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds

    def check(self, *_args, **_kwargs):
        return types.SimpleNamespace(allowed=False, retry_after_seconds=self.retry_after_seconds)


def _env(**overrides):
    values = {
        "PAINT_MODULE_ENABLED": True,
        "VIDEO_MODULE_ENABLED": True,
        "PAINT_WHITELIST_MODE": False,
        "PAINT_WHITELIST_PERSON_LIST": [],
        "PAINT_WHITELIST_GROUP_LIST": [],
        "PAINT_BLACKLIST_PERSON_LIST": [],
        "PAINT_BLACKLIST_GROUP_LIST": [],
        "PAINT_RATE_LIMIT_MAX_REQUESTS": 3,
        "PAINT_RATE_LIMIT_WINDOW_SECONDS": 600,
        "VIDEO_RATE_LIMIT_MAX_REQUESTS": 1,
        "VIDEO_RATE_LIMIT_WINDOW_SECONDS": 900,
    }
    values.update(overrides)
    return types.SimpleNamespace(**values)


def _event(text: str, *, user_id: int = 456, group_id: int = 123) -> MessageEvent:
    incoming = IncomingMessage(
        message_scene="group",
        peer_id=group_id,
        message_seq=1,
        sender_id=user_id,
        time=0,
        segments=[{"type": "text", "data": {"text": text}}],
        friend=None,
        group=Group(group_id=group_id, group_name="g", member_count=1, max_member_count=1),
        group_member=Member(
            user_id=user_id,
            nickname="u",
            sex="unknown",
            group_id=group_id,
            card="",
            title="",
            level="0",
            role="member",
            join_time=0,
            last_sent_time=0,
            shut_up_end_time=0,
        ),
    )
    return MessageEvent(data=incoming, to_me=True, time=0, self_id="1")


def _install_message_spies(monkeypatch):
    sent = []

    class DummyMessage:
        def __init__(self, kind: str, payload):
            self.kind = kind
            self.payload = payload

        async def send(self, *_args, **_kwargs):
            sent.append((self.kind, self.payload))

    monkeypatch.setattr(UniMessage, "text", classmethod(lambda cls, text: DummyMessage("text", text)))
    monkeypatch.setattr(UniMessage, "image", classmethod(lambda cls, **kwargs: DummyMessage("image", kwargs)))
    monkeypatch.setattr(UniMessage, "video", classmethod(lambda cls, **kwargs: DummyMessage("video", kwargs)))
    return sent


async def _receive(event: MessageEvent):
    async with App().test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, self_id="1", auto_connect=False)
        ctx.receive_event(bot, event)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_paint_command_generates_image(monkeypatch):
    sent = _install_message_spies(monkeypatch)
    captured = {}

    async def fake_message_extract(_segments):
        return "/paint a cat", [], [], []

    async def fake_paint(prompt, reference_images):
        captured["prompt"] = prompt
        captured["reference_images"] = reference_images
        return b"image-bytes"

    monkeypatch.setattr(playground, "EnvConfig", _env(), raising=False)
    monkeypatch.setattr(playground, "message_extract", fake_message_extract, raising=False)
    monkeypatch.setattr(playground, "paint", fake_paint, raising=False)
    monkeypatch.setattr(playground, "paint_rate_limiter", AllowLimiter(), raising=False)

    await _receive(_event("/paint a cat"))

    assert captured == {"prompt": "a cat", "reference_images": []}
    assert sent == [("image", {"raw": b"image-bytes"})]


@pytest.mark.asyncio
async def test_paint_command_uses_attached_images(monkeypatch):
    sent = _install_message_spies(monkeypatch)
    captured = {}

    async def fake_message_extract(_segments):
        return "/paint watercolor", [b"image-bytes"], [], []

    async def fake_paint(prompt, reference_images):
        captured["prompt"] = prompt
        captured["reference_images"] = reference_images
        return b"edited-image"

    monkeypatch.setattr(playground, "EnvConfig", _env(), raising=False)
    monkeypatch.setattr(playground, "message_extract", fake_message_extract, raising=False)
    monkeypatch.setattr(playground, "paint", fake_paint, raising=False)
    monkeypatch.setattr(playground, "paint_rate_limiter", AllowLimiter(), raising=False)

    await _receive(_event("/paint watercolor"))

    assert captured == {"prompt": "watercolor", "reference_images": [b"image-bytes"]}
    assert sent == [("image", {"raw": b"edited-image"})]


@pytest.mark.asyncio
async def test_video_command_generates_from_text(monkeypatch):
    sent = _install_message_spies(monkeypatch)
    captured = {}

    async def fake_message_extract(_segments):
        return "/video make it move", [], [], []

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return types.SimpleNamespace(raw=b"video-bytes", url=None)

    monkeypatch.setattr(playground, "EnvConfig", _env(), raising=False)
    monkeypatch.setattr(playground, "message_extract", fake_message_extract, raising=False)
    monkeypatch.setattr(playground, "generate_video", fake_generate_video, raising=False)
    monkeypatch.setattr(playground, "video_rate_limiter", AllowLimiter(), raising=False)

    await _receive(_event("/video make it move"))

    assert captured == {"prompt": "make it move", "image": None, "video": None}
    assert sent == [("video", {"raw": b"video-bytes"})]


@pytest.mark.asyncio
async def test_video_command_prefers_video_input_over_image(monkeypatch):
    sent = _install_message_spies(monkeypatch)
    captured = {}

    async def fake_message_extract(_segments):
        return "/video extend", [b"image-bytes"], [], [b"old-video", b"latest-video"]

    async def fake_generate_video(prompt, *, image=None, video=None):
        captured["prompt"] = prompt
        captured["image"] = image
        captured["video"] = video
        return types.SimpleNamespace(raw=None, url="https://example.com/video.mp4")

    monkeypatch.setattr(playground, "EnvConfig", _env(), raising=False)
    monkeypatch.setattr(playground, "message_extract", fake_message_extract, raising=False)
    monkeypatch.setattr(playground, "generate_video", fake_generate_video, raising=False)
    monkeypatch.setattr(playground, "video_rate_limiter", AllowLimiter(), raising=False)

    await _receive(_event("/video extend"))

    assert captured == {"prompt": "extend", "image": None, "video": b"latest-video"}
    assert sent == [("video", {"url": "https://example.com/video.mp4"})]


@pytest.mark.asyncio
async def test_media_command_denies_when_whitelist_excludes_user_and_group(monkeypatch):
    sent = _install_message_spies(monkeypatch)

    async def fake_paint(_prompt, _reference_images):
        raise AssertionError("paint should not be called when permission denies")

    monkeypatch.setattr(playground, "EnvConfig", _env(PAINT_WHITELIST_MODE=True), raising=False)
    monkeypatch.setattr(playground, "paint", fake_paint, raising=False)

    await _receive(_event("/paint denied"))

    assert sent == [("text", "没有权限使用媒体生成功能")]


@pytest.mark.asyncio
async def test_paint_command_disabled_module_skips_service(monkeypatch):
    sent = _install_message_spies(monkeypatch)

    async def fake_paint(_prompt, _reference_images):
        raise AssertionError("paint should not be called while disabled")

    monkeypatch.setattr(playground, "EnvConfig", _env(PAINT_MODULE_ENABLED=False), raising=False)
    monkeypatch.setattr(playground, "paint", fake_paint, raising=False)

    await _receive(_event("/paint a cat"))

    assert sent == [("text", "绘画功能未启用")]


@pytest.mark.asyncio
async def test_video_command_rate_limit_skips_service(monkeypatch):
    sent = _install_message_spies(monkeypatch)

    async def fake_message_extract(_segments):
        return "/video make it move", [], [], []

    async def fake_generate_video(_prompt, *, image=None, video=None):
        raise AssertionError("generate_video should not be called while rate limited")

    monkeypatch.setattr(playground, "EnvConfig", _env(), raising=False)
    monkeypatch.setattr(playground, "message_extract", fake_message_extract, raising=False)
    monkeypatch.setattr(playground, "generate_video", fake_generate_video, raising=False)
    monkeypatch.setattr(playground, "video_rate_limiter", DenyLimiter(42), raising=False)

    await _receive(_event("/video make it move"))

    assert sent == [("text", "视频生成得太快了，42 秒后再试吧")]
