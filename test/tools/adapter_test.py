# ruff: noqa: S101
import tempfile
import types
from pathlib import Path

import pytest

# ── 图片 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_image_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_image("https://example.com/a.png")
    assert text == "构建了一个图片消息"
    assert artifact.content["type"] == "image"
    assert artifact.content["url"] == "https://example.com/a.png"


@pytest.mark.asyncio
async def test_send_image_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG")
        tmp = f.name
    try:
        _, artifact = await adapter.send_image(tmp)
        assert artifact.content["type"] == "image"
        assert artifact.content["path"] == tmp
        assert artifact.content["url"] is None
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── 音频 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_audio_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_audio("https://example.com/a.mp3")
    assert text == "构建了一个音频消息"
    assert artifact.content["type"] == "audio"
    assert artifact.content["url"] == "https://example.com/a.mp3"


@pytest.mark.asyncio
async def test_send_audio_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    try:
        _, artifact = await adapter.send_audio(tmp)
        assert artifact.content["type"] == "audio"
        assert artifact.content["path"] == tmp
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── 语音 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_voice_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_voice("https://example.com/a.wav")
    assert text == "构建了一个语音消息"
    assert artifact.content["type"] == "voice"
    assert artifact.content["url"] == "https://example.com/a.wav"


@pytest.mark.asyncio
async def test_send_voice_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        _, artifact = await adapter.send_voice(tmp)
        assert artifact.content["type"] == "voice"
        assert artifact.content["path"] == tmp
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── 视频 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_video_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_video("https://example.com/a.mp4")
    assert text == "构建了一个视频消息"
    assert artifact.content["type"] == "video"
    assert artifact.content["url"] == "https://example.com/a.mp4"


@pytest.mark.asyncio
async def test_send_video_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        tmp = f.name
    try:
        _, artifact = await adapter.send_video(tmp)
        assert artifact.content["type"] == "video"
        assert artifact.content["path"] == tmp
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── 表情 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_emoji(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_emoji("123")
    assert text == "构建了一个表情消息"
    assert artifact.content["type"] == "emoji"
    assert artifact.content["id"] == "123"


# ── 文件 ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_file_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_file("https://example.com/report.pdf", "report.pdf")
    assert text == "构建了一个文件消息：report.pdf"
    assert artifact.content["type"] == "file"
    assert artifact.content["url"] == "https://example.com/report.pdf"
    assert artifact.content["name"] == "report.pdf"


@pytest.mark.asyncio
async def test_send_file_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"hello")
        tmp = f.name
    try:
        text, artifact = await adapter.send_file(tmp, "hello.txt")
        assert text == "构建了一个文件消息：hello.txt"
        assert artifact.content["type"] == "file"
        assert artifact.content["path"] == tmp
        assert artifact.content["name"] == "hello.txt"
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── URL 格式校验 ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_source",
    [
        "not_a_url",
        "ftp://example.com/a.png",
        "//example.com/no-scheme",
        "",
    ],
)
async def test_invalid_url_rejected(load_tool_module, bad_source):
    adapter = load_tool_module("adapter")
    with pytest.raises(ValueError, match="无效的 URL"):
        await adapter.send_image(bad_source)


@pytest.mark.asyncio
async def test_send_at(load_tool_module):
    adapter = load_tool_module("adapter")
    calls = []

    class DummyBot:
        async def send_group_message(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(message_seq=9)

    adapter.get_bot = lambda: DummyBot()

    result = await adapter.send_at("12345", config={"configurable": {"group_id": 67890}})

    assert result == "已在群 67890 @ 12345，message_seq=9"
    assert len(calls) == 1
    assert calls[0]["group_id"] == 67890
    assert calls[0]["message"][0].type == "mention"
    assert calls[0]["message"][0].data == {"user_id": 12345}


@pytest.mark.asyncio
async def test_send_at_all(load_tool_module):
    adapter = load_tool_module("adapter")
    calls = []

    class DummyBot:
        async def send_group_message(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(message_seq=11)

    adapter.get_bot = lambda: DummyBot()

    result = await adapter.send_at_all(config={"configurable": {"group_id": 67890}})

    assert result == "已在群 67890 @全体成员，message_seq=11"
    assert len(calls) == 1
    assert calls[0]["group_id"] == 67890
    assert calls[0]["message"][0].type == "mention_all"


@pytest.mark.asyncio
async def test_send_text_with_at(load_tool_module):
    adapter = load_tool_module("adapter")
    calls = []

    class DummyBot:
        async def send_group_message(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(message_seq=10)

    adapter.get_bot = lambda: DummyBot()

    result = await adapter.send_text_with_at("12345", "你好", config={"configurable": {"group_id": 67890}})

    assert result == "已在群 67890 @ 12345 并发送消息，message_seq=10"
    assert len(calls) == 1
    assert calls[0]["group_id"] == 67890
    assert [segment.type for segment in calls[0]["message"]] == ["mention", "text"]
    assert calls[0]["message"][0].data == {"user_id": 12345}
    assert calls[0]["message"][1].data == {"text": " 你好"}
