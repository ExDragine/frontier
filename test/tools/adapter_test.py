# ruff: noqa: S101
import tempfile
import types
from pathlib import Path

import pytest

_MEDIA_TOOLS = ["send_image", "send_audio", "send_voice", "send_video"]


@pytest.mark.asyncio
async def test_send_image_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_image("https://example.com/a.png")
    assert text == "构建了一个图片消息，将在本轮结束后自动发送"
    assert artifact[0].type == "image"
    assert artifact[0].url == "https://example.com/a.png"


@pytest.mark.asyncio
async def test_send_image_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG")
        tmp = f.name
    try:
        _, artifact = await adapter.send_image(tmp)
        assert artifact[0].type == "image"
        assert str(artifact[0].path) == tmp
        assert artifact[0].url is None
    finally:
        Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_send_audio_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_audio("https://example.com/a.mp3")
    assert text == "构建了一个音频消息，将在本轮结束后自动发送"
    assert artifact[0].type == "audio"
    assert artifact[0].url == "https://example.com/a.mp3"


@pytest.mark.asyncio
async def test_send_audio_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    try:
        _, artifact = await adapter.send_audio(tmp)
        assert artifact[0].type == "audio"
        assert str(artifact[0].path) == tmp
    finally:
        Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_send_voice_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_voice("https://example.com/a.wav")
    assert text == "构建了一个语音消息，将在本轮结束后自动发送"
    assert artifact[0].type == "voice"
    assert artifact[0].url == "https://example.com/a.wav"


@pytest.mark.asyncio
async def test_send_voice_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        _, artifact = await adapter.send_voice(tmp)
        assert artifact[0].type == "voice"
        assert str(artifact[0].path) == tmp
    finally:
        Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_send_video_url(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_video("https://example.com/a.mp4")
    assert text == "构建了一个视频消息，将在本轮结束后自动发送"
    assert artifact[0].type == "video"
    assert artifact[0].url == "https://example.com/a.mp4"


@pytest.mark.asyncio
async def test_send_video_local(load_tool_module):
    adapter = load_tool_module("adapter")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        tmp = f.name
    try:
        _, artifact = await adapter.send_video(tmp)
        assert artifact[0].type == "video"
        assert str(artifact[0].path) == tmp
    finally:
        Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_send_emoji(load_tool_module):
    adapter = load_tool_module("adapter")
    text, artifact = await adapter.send_emoji("123")
    assert text == "构建了一个表情消息"
    assert artifact[0].type == "emoji"
    assert artifact[0].id == "123"


@pytest.mark.asyncio
async def test_send_file_url(load_tool_module):
    adapter = load_tool_module("adapter")
    calls = []

    class DummyBot:
        async def upload_private_file(self, **kwargs):
            calls.append(kwargs)
            return "private-file-id"

    adapter.get_bot = lambda: DummyBot()

    result = await adapter.send_file(
        "https://example.com/report.pdf",
        config={"configurable": {"user_id": "456"}},
    )

    assert result == "已发送私聊文件 report.pdf，file_id=private-file-id"
    assert calls == [
        {
            "user_id": 456,
            "url": "https://example.com/report.pdf",
            "file_name": "report.pdf",
        }
    ]


@pytest.mark.asyncio
async def test_send_file_local(load_tool_module, tmp_path):
    adapter = load_tool_module("adapter")
    local_file = tmp_path / "hello.txt"
    local_file.write_text("hello")
    calls = []

    class DummyBot:
        async def upload_private_file(self, **kwargs):
            calls.append(kwargs)
            return "private-file-id"

    adapter.get_bot = lambda: DummyBot()

    result = await adapter.send_file(
        "/hello.txt",
        config={
            "configurable": {
                "user_id": 456,
                "workspace_dir": str(tmp_path),
            }
        },
    )

    assert result == "已发送私聊文件 hello.txt，file_id=private-file-id"
    assert calls[0]["path"] == str(local_file)
    assert calls[0]["file_name"] == "hello.txt"


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", _MEDIA_TOOLS)
@pytest.mark.parametrize(
    "bad_source",
    [
        "not_a_url",
        "ftp://example.com/a.png",
        "//example.com/no-scheme",
        "\\\\example.com\\media.png",
        "https://[malformed-host",
        "data:image/png;base64,private-image-data",
        "bad\x00path",
        "",
    ],
)
async def test_invalid_media_source_returns_recoverable_result(load_tool_module, tool_name, bad_source):
    adapter = load_tool_module("adapter")
    text, artifact = await getattr(adapter, tool_name)(bad_source)

    assert artifact is None
    assert "媒体消息未加入回复" in text
    assert "无需再次发送" in text
    assert "private-image-data" not in text
    assert "malformed-host" not in text


@pytest.mark.asyncio
@pytest.mark.parametrize("source, valid", [
    ("https://example.com/media.png", True),
    ("https://[malformed-host", False),
    ("ftp://example.com/media.png", False),
    ("//example.com/media.png", False),
    ("\\\\example.com\\media.png", False),
])
async def test_remote_media_sources_do_not_probe_local_filesystem(load_tool_module, monkeypatch, source, valid):
    adapter = load_tool_module("adapter")

    def fail(*_args, **_kwargs):
        raise AssertionError("Remote sources must not be probed as local files")

    monkeypatch.setattr(adapter, "resolve_local_path", fail)
    monkeypatch.setattr(adapter, "resolve_virtual_path", fail)

    _, artifact = await adapter.send_image(source)

    assert (artifact is not None) == valid


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


def _ws_config(workspace_dir: str) -> dict:
    return {"configurable": {"workspace_dir": workspace_dir}}


@pytest.mark.asyncio
async def test_send_image_resolves_workspace_path(load_tool_module, tmp_path):
    adapter = load_tool_module("adapter")
    img = tmp_path / "photo.png"
    img.write_bytes(b"\x89PNG")

    _, artifact = await adapter.send_image("/photo.png", config=_ws_config(str(tmp_path)))

    assert artifact[0].type == "image"
    assert artifact[0].path == img


@pytest.mark.asyncio
async def test_send_file_resolves_workspace_path(load_tool_module, tmp_path):
    adapter = load_tool_module("adapter")
    f = tmp_path / "report.pdf"
    f.write_bytes(b"%PDF")
    calls = []

    class DummyBot:
        async def upload_group_file(self, **kwargs):
            calls.append(kwargs)
            return "group-file-id"

    adapter.get_bot = lambda: DummyBot()

    result = await adapter.send_file(
        "/report.pdf",
        "report.pdf",
        config={
            "configurable": {
                "group_id": 123,
                "workspace_dir": str(tmp_path),
            }
        },
    )

    assert result == "已发送群文件 report.pdf，file_id=group-file-id"
    assert calls == [
        {
            "group_id": 123,
            "path": str(f),
            "file_name": "report.pdf",
        }
    ]


@pytest.mark.asyncio
async def test_send_file_resolves_memory_virtual_path(load_tool_module, tmp_path):
    adapter = load_tool_module("adapter")
    workspace_dir = tmp_path / "workspaces" / "group-123"
    memory_dir = tmp_path / "memory" / "group-123"
    workspace_dir.mkdir(parents=True)
    memory_dir.mkdir(parents=True)
    attachment = memory_dir / "incoming.pdf"
    attachment.write_bytes(b"%PDF")
    calls = []

    class DummyBot:
        async def upload_group_file(self, **kwargs):
            calls.append(kwargs)
            return "memory-file-id"

    adapter.get_bot = lambda: DummyBot()
    result = await adapter.send_file(
        "/memory/group-123/incoming.pdf",
        config={
            "configurable": {
                "group_id": 123,
                "virtual_roots": {
                    "/": str(workspace_dir),
                    "/memory/group-123/": str(memory_dir),
                },
            }
        },
    )

    assert result == "已发送群文件 incoming.pdf，file_id=memory-file-id"
    assert calls[0]["path"] == str(attachment)


@pytest.mark.asyncio
async def test_send_file_reports_platform_upload_failure(load_tool_module, tmp_path):
    adapter = load_tool_module("adapter")
    attachment = tmp_path / "report.pdf"
    attachment.write_bytes(b"%PDF")

    class DummyBot:
        async def upload_private_file(self, **_kwargs):
            raise RuntimeError("upload rejected")

    adapter.get_bot = lambda: DummyBot()
    result = await adapter.send_file(
        "/report.pdf",
        config={
            "configurable": {
                "user_id": 456,
                "workspace_dir": str(tmp_path),
            }
        },
    )

    assert result.startswith("文件发送失败：平台上传未成功")


@pytest.mark.asyncio
async def test_send_image_reports_missing_workspace_file_without_raising(load_tool_module):
    adapter = load_tool_module("adapter")

    text, artifact = await adapter.send_image("/nope.png", config=_ws_config("/nonexistent"))

    assert artifact is None
    assert "路径不存在" in text


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", _MEDIA_TOOLS)
@pytest.mark.parametrize("source", ["/photo.png", "photo.png", "/memory/group-123/photo.png"])
async def test_media_tools_resolve_current_virtual_mounts(load_tool_module, tmp_path, tool_name, source):
    adapter = load_tool_module("adapter")
    workspace = tmp_path / "workspace"
    memory = tmp_path / "memory"
    workspace.mkdir()
    memory.mkdir()
    (workspace / "photo.png").write_bytes(b"workspace media")
    (memory / "photo.png").write_bytes(b"memory media")
    config = {"configurable": {
        "workspace_dir": str(workspace),
        "virtual_roots": {"/": str(workspace), "/memory/group-123/": str(memory)},
    }}

    text, artifact = await getattr(adapter, tool_name)(source, config=config)

    expected_root = memory if source.startswith("/memory/") else workspace
    assert artifact[0].path == expected_root / "photo.png"
    assert artifact[0].url is None
    assert "将在本轮结束后自动发送" in text


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", _MEDIA_TOOLS)
@pytest.mark.parametrize("source", [
    "/../outside.png",
    "/memory/group-123/../outside.png",
    "/memory/group-other/photo.png",
    "/skills/photo.png",
])
async def test_media_tools_reject_traversal_and_unmounted_paths(load_tool_module, tmp_path, tool_name, source):
    adapter = load_tool_module("adapter")
    workspace = tmp_path / "workspace"
    memory = tmp_path / "memory" / "group-123"
    workspace.mkdir()
    memory.mkdir(parents=True)
    (tmp_path / "outside.png").write_bytes(b"private")
    (memory.parent / "outside.png").write_bytes(b"private")
    for relative in ("memory/group-other", "skills"):
        folder = workspace / relative
        folder.mkdir(parents=True)
        (folder / "photo.png").write_bytes(b"private")
    config = {"configurable": {
        "virtual_roots": {"/": str(workspace), "/memory/group-123/": str(memory)},
    }}

    text, artifact = await getattr(adapter, tool_name)(source, config=config)

    assert artifact is None
    assert "挂载范围" in text
    assert source not in text


@pytest.mark.asyncio
async def test_explicit_empty_mounts_do_not_fall_back_to_host_paths(load_tool_module, tmp_path):
    adapter = load_tool_module("adapter")
    local_file = tmp_path / "private.png"
    local_file.write_bytes(b"private")

    _, artifact = await adapter.send_image(str(local_file), config={"configurable": {"virtual_roots": {}}})

    assert artifact is None


@pytest.mark.asyncio
async def test_media_artifact_construction_errors_are_not_swallowed(load_tool_module, monkeypatch):
    adapter = load_tool_module("adapter")

    def fail(**_kwargs):
        raise ValueError("unexpected artifact construction failure")

    monkeypatch.setattr(adapter.UniMessage, "image", fail)

    with pytest.raises(ValueError, match="unexpected artifact construction failure"):
        await adapter.send_image("https://example.com/photo.png")
