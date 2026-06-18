# ruff: noqa: S101
import types

import pytest


class DummyMilkyBot:
    def __init__(self):
        self.calls = []

    async def upload_private_file(self, **kwargs):
        self.calls.append(("upload_private_file", kwargs))
        return "private-file-id"

    async def upload_group_file(self, **kwargs):
        self.calls.append(("upload_group_file", kwargs))
        return "group-file-id"

    async def get_private_file_download_url(self, **kwargs):
        self.calls.append(("get_private_file_download_url", kwargs))
        return "https://example.com/private-file"

    async def get_group_file_download_url(self, **kwargs):
        self.calls.append(("get_group_file_download_url", kwargs))
        return "https://example.com/group-file"

    async def get_group_files(self, **kwargs):
        self.calls.append(("get_group_files", kwargs))
        return types.SimpleNamespace(
            files=[
                types.SimpleNamespace(
                    file_id="file-1",
                    file_name="report.pdf",
                    file_size=100,
                    parent_folder_id="/",
                    uploader_id=456,
                )
            ],
            folders=[types.SimpleNamespace(folder_id="folder-1", folder_name="资料", file_count=1)],
        )

    async def move_group_file(self, **kwargs):
        self.calls.append(("move_group_file", kwargs))

    async def rename_group_file(self, **kwargs):
        self.calls.append(("rename_group_file", kwargs))

    async def delete_group_file(self, **kwargs):
        self.calls.append(("delete_group_file", kwargs))

    async def create_group_folder(self, **kwargs):
        self.calls.append(("create_group_folder", kwargs))
        return "folder-new"

    async def rename_group_folder(self, **kwargs):
        self.calls.append(("rename_group_folder", kwargs))

    async def delete_group_folder(self, **kwargs):
        self.calls.append(("delete_group_folder", kwargs))


def _install_dummy_bot(monkeypatch, module):
    bot = DummyMilkyBot()
    monkeypatch.setattr(module, "get_bot", lambda: bot)
    return bot


def _config(group_id=123, user_id="456", workspace_dir=None):
    cfg = {"configurable": {"group_id": group_id, "user_id": user_id}}
    if workspace_dir is not None:
        cfg["configurable"]["workspace_dir"] = workspace_dir
    return cfg


@pytest.mark.asyncio
async def test_file_upload_and_download_tools_call_milky(load_tool_module, monkeypatch, tmp_path):
    milky_file = load_tool_module("milky_file")
    bot = _install_dummy_bot(monkeypatch, milky_file)
    local_file = tmp_path / "report.pdf"
    local_file.write_bytes(b"pdf")

    private_file = await milky_file.upload_private_file(
        file_uri=f"file://{local_file}",
        file_name="report.pdf",
        config=_config(),
    )
    group_file = await milky_file.upload_group_file(
        file_uri="https://example.com/report.pdf",
        file_name="report.pdf",
        parent_folder_id="/docs",
        config=_config(),
    )
    private_url = await milky_file.get_private_file_download_url(user_id=456, file_id="p1", file_hash="hash")
    group_url = await milky_file.get_group_file_download_url(file_id="g1", config=_config())

    assert private_file == "已上传私聊文件 report.pdf，file_id=private-file-id"
    assert group_file == "已上传群 123 文件 report.pdf，file_id=group-file-id"
    assert private_url == "https://example.com/private-file"
    assert group_url == "https://example.com/group-file"
    assert bot.calls == [
        ("upload_private_file", {"user_id": 456, "path": str(local_file), "file_name": "report.pdf"}),
        (
            "upload_group_file",
            {
                "group_id": 123,
                "url": "https://example.com/report.pdf",
                "file_name": "report.pdf",
                "parent_folder_id": "/docs",
            },
        ),
        ("get_private_file_download_url", {"user_id": 456, "file_id": "p1", "file_hash": "hash"}),
        ("get_group_file_download_url", {"group_id": 123, "file_id": "g1"}),
    ]


@pytest.mark.asyncio
async def test_group_file_management_tools_call_milky(load_tool_module, monkeypatch):
    milky_file = load_tool_module("milky_file")
    bot = _install_dummy_bot(monkeypatch, milky_file)

    files = await milky_file.get_group_files(parent_folder_id="/", config=_config())
    moved = await milky_file.move_group_file(
        file_id="file-1",
        parent_folder_id="/",
        target_folder_id="/docs",
        config=_config(),
    )
    renamed_file = await milky_file.rename_group_file(
        file_id="file-1",
        new_file_name="new.pdf",
        config=_config(),
    )
    deleted_file = await milky_file.delete_group_file(file_id="file-1", config=_config())
    created_folder = await milky_file.create_group_folder(folder_name="资料", config=_config())
    renamed_folder = await milky_file.rename_group_folder(
        folder_id="folder-1",
        new_folder_name="新资料",
        config=_config(),
    )
    deleted_folder = await milky_file.delete_group_folder(folder_id="folder-1", config=_config())

    assert "群 123 文件" in files
    assert "report.pdf" in files
    assert moved == "已将群 123 文件 file-1 从 / 移动到 /docs"
    assert renamed_file == "已将群 123 文件 file-1 重命名为：new.pdf"
    assert deleted_file == "已删除群 123 文件 file-1"
    assert created_folder == "已在群 123 创建文件夹 资料，folder_id=folder-new"
    assert renamed_folder == "已将群 123 文件夹 folder-1 重命名为：新资料"
    assert deleted_folder == "已删除群 123 文件夹 folder-1"
    assert bot.calls == [
        ("get_group_files", {"group_id": 123, "parent_folder_id": "/"}),
        (
            "move_group_file",
            {"group_id": 123, "file_id": "file-1", "parent_folder_id": "/", "target_folder_id": "/docs"},
        ),
        (
            "rename_group_file",
            {"group_id": 123, "file_id": "file-1", "parent_folder_id": "/", "new_file_name": "new.pdf"},
        ),
        ("delete_group_file", {"group_id": 123, "file_id": "file-1"}),
        ("create_group_folder", {"group_id": 123, "folder_name": "资料"}),
        ("rename_group_folder", {"group_id": 123, "folder_id": "folder-1", "new_folder_name": "新资料"}),
        ("delete_group_folder", {"group_id": 123, "folder_id": "folder-1"}),
    ]


# ── 沙箱 workspace 路径解析 ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_private_file_resolves_workspace_path(load_tool_module, monkeypatch, tmp_path):
    milky_file = load_tool_module("milky_file")
    _install_dummy_bot(monkeypatch, milky_file)

    (tmp_path / "report.pdf").write_bytes(b"pdf")

    result = await milky_file.upload_private_file(
        file_uri="/report.pdf",
        file_name="report.pdf",
        config=_config(workspace_dir=str(tmp_path)),
    )

    assert result == "已上传私聊文件 report.pdf，file_id=private-file-id"


@pytest.mark.asyncio
async def test_upload_group_file_resolves_workspace_path(load_tool_module, monkeypatch, tmp_path):
    milky_file = load_tool_module("milky_file")
    bot = _install_dummy_bot(monkeypatch, milky_file)

    sandbox_file = tmp_path / "data.csv"
    sandbox_file.write_bytes(b"a,b,c")

    result = await milky_file.upload_group_file(
        file_uri="/data.csv",
        config=_config(workspace_dir=str(tmp_path)),
    )

    assert result == "已上传群 123 文件 data.csv，file_id=group-file-id"
    upload_call = next(c for name, c in bot.calls if name == "upload_group_file")
    assert upload_call["path"] == str(sandbox_file)
    assert upload_call["file_name"] == "data.csv"


@pytest.mark.asyncio
async def test_upload_group_file_extracts_file_name_from_workspace_path(load_tool_module, monkeypatch, tmp_path):
    milky_file = load_tool_module("milky_file")
    bot = _install_dummy_bot(monkeypatch, milky_file)

    (tmp_path / "archive.zip").write_bytes(b"zip")

    result = await milky_file.upload_group_file(
        file_uri="/archive.zip",
        config=_config(workspace_dir=str(tmp_path)),
    )

    assert result == "已上传群 123 文件 archive.zip，file_id=group-file-id"
    upload_call = next(c for name, c in bot.calls if name == "upload_group_file")
    assert upload_call["path"] == str(tmp_path / "archive.zip")
    assert upload_call["file_name"] == "archive.zip"
