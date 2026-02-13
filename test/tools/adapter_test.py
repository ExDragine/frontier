# ruff: noqa: S101

import pytest


@pytest.mark.asyncio
async def test_send_image(load_tool_module):
    adapter = load_tool_module("adapter")

    text, artifact = await adapter.send_image("https://example.com/a.png")

    assert text == "构建了一个图片消息"
    assert artifact.content["type"] == "image"
    assert artifact.content["url"] == "https://example.com/a.png"


@pytest.mark.asyncio
async def test_send_audio(load_tool_module):
    adapter = load_tool_module("adapter")

    text, artifact = await adapter.send_audio("https://example.com/a.mp3")

    assert text == "构建了一个音频消息"
    assert artifact.content["type"] == "audio"
    assert artifact.content["url"] == "https://example.com/a.mp3"


@pytest.mark.asyncio
async def test_send_video(load_tool_module):
    adapter = load_tool_module("adapter")

    text, artifact = await adapter.send_video("https://example.com/a.mp4")

    assert text == "构建了一个视频消息"
    assert artifact.content["type"] == "video"
    assert artifact.content["url"] == "https://example.com/a.mp4"


@pytest.mark.asyncio
async def test_send_emoji(load_tool_module):
    adapter = load_tool_module("adapter")

    text, artifact = await adapter.send_emoji("123")

    assert text == "构建了一个表情消息"
    assert artifact.content["type"] == "emoji"
    assert artifact.content["id"] == "123"
