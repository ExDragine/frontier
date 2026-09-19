"""QQ Agent attachments handling."""

import asyncio
import hashlib
import os
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nonebot import logger

from utils.http_client import get_http_client
from utils.media import detect_mime_type

httpx_client = get_http_client("message")

FILE_URL_FIELDS = ("temp_url", "url", "download_url", "download_uri")


@dataclass(frozen=True, slots=True)
class MessageFileItem:
    file_id: str | None
    file_name: str
    file_size: int
    file_hash: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class StagedMessageFile:
    file_name: str
    file_size: int
    virtual_path: str
    local_path: Path
    mime_type: str = "application/octet-stream"
    sha256: str | None = None


def _first_file_url(data: dict) -> str | None:
    for field in FILE_URL_FIELDS:
        value = data.get(field)
        if value:
            return str(value)
    return None


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except TypeError, ValueError:
        return 0


def extract_message_files(messages: list[dict]) -> list[MessageFileItem]:
    files: list[MessageFileItem] = []
    for message in messages:
        if message.get("type") != "file":
            continue
        msg_data = message.get("data", {})
        file_hash = msg_data.get("file_hash")
        files.append(
            MessageFileItem(
                file_id=str(file_id) if (file_id := msg_data.get("file_id")) else None,
                file_name=str(msg_data.get("file_name") or "file"),
                file_size=_int_or_zero(msg_data.get("file_size")),
                file_hash=str(file_hash) if file_hash is not None else None,
                url=_first_file_url(msg_data),
            )
        )
    return files


async def _message_file_download_url(
    bot,
    file_item: MessageFileItem,
    *,
    user_id: str | int,
    group_id: int | None,
    is_self_send: bool = False,
) -> str | None:
    if file_item.url:
        return file_item.url
    if not file_item.file_id:
        return None
    try:
        if group_id is not None:
            return await bot.get_group_file_download_url(group_id=int(group_id), file_id=file_item.file_id)
        if file_item.file_hash is None:
            logger.warning(f"私聊文件缺少 file_hash 字段，无法获取下载链接: {file_item.file_name}")
            return None
        return await bot.get_private_file_download_url(
            user_id=int(user_id),
            file_id=file_item.file_id,
            file_hash=file_item.file_hash,
            is_self_send=is_self_send,
        )
    except Exception as exc:
        logger.warning(f"获取文件下载链接失败 {file_item.file_name}: {type(exc).__name__}: {exc}")
        return None


async def _download_file_bytes(url: str, file_name: str) -> bytes | None:
    try:
        response = await httpx_client.get(url)
        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            raise_for_status()
        return response.content
    except Exception as exc:
        logger.warning(f"下载文件失败 {file_name}: {type(exc).__name__}: {exc}")
        return None


def _safe_attachment_file_name(file_name: str) -> str:
    safe_name = Path(str(file_name).replace("\\", "/")).name.strip()
    return safe_name or "file"


def _reserve_attachment_path(directory: Path, file_name: str) -> Path:
    """Atomically reserve a fresh path before another download can select it."""
    original = Path(file_name)
    stem = original.stem or "file"
    suffix = original.suffix
    candidate = directory / file_name
    counter = 2
    while True:
        try:
            candidate.open("xb").close()
            return candidate
        except FileExistsError:
            candidate = directory / f"{stem}-{counter}{suffix}"
            counter += 1


def cleanup_staged_message_files(staged_files: list[StagedMessageFile]) -> None:
    """Remove files that did not reach a TTL-managed attachment row."""
    for staged_file in staged_files:
        path = Path(staged_file.local_path)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("清理未索引消息文件失败 {}: {}", path, exc)
            continue
        with suppress(OSError):
            path.parent.rmdir()


def _write_staged_file(target_path: Path, data: bytes) -> None:
    temp_path = target_path.with_name(f".{target_path.name}.frontier-pending-{os.getpid()}-{time.time_ns()}")
    try:
        with temp_path.open("xb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, target_path)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("清理消息文件临时写入失败 {}: {}", temp_path, exc)


async def _complete_staged_write(target_path: Path, data: bytes) -> None:
    # Cancellation cannot stop a worker thread. Let it finish before caller cleanup
    # so the thread cannot recreate an unindexed file after it was removed.
    write = asyncio.create_task(asyncio.to_thread(_write_staged_file, target_path, data))
    try:
        await asyncio.shield(write)
    except asyncio.CancelledError:
        with suppress(Exception):
            await write
        raise


async def stage_message_files(
    bot,
    file_items: list[MessageFileItem],
    *,
    memory_dir: str | Path,
    workspace_key: str,
    message_time: int | None = None,
    message_id: int | None = None,
    user_id: str | int,
    group_id: int | None,
    is_self_send: bool = False,
) -> list[StagedMessageFile]:
    """Download incoming file segments into the agent memory files directory."""
    if not file_items:
        return []

    memory_path = Path(memory_dir)
    files_dir = memory_path / "files"
    if message_id is not None:
        prefix = f"{int(message_time)}-" if message_time is not None else ""
        files_dir /= f"{prefix}m{int(message_id)}"
    elif message_time is not None:
        files_dir /= str(int(message_time))
    files_dir.mkdir(parents=True, exist_ok=True)
    staged_files: list[StagedMessageFile] = []

    try:
        for file_item in file_items:
            url = await _message_file_download_url(
                bot, file_item, user_id=user_id, group_id=group_id, is_self_send=is_self_send,
            )
            if not url:
                logger.warning(f"文件缺少可下载链接，无法注入工作区: {file_item.file_name}")
                continue
            file_bytes = await _download_file_bytes(url, file_item.file_name)
            if file_bytes is None:
                continue

            safe_name = _safe_attachment_file_name(file_item.file_name)
            target_path = _reserve_attachment_path(files_dir, safe_name)
            virtual_path = f"/memory/{workspace_key}/{target_path.relative_to(memory_path).as_posix()}"
            staged_files.append(
                StagedMessageFile(
                    file_name=target_path.name,
                    file_size=len(file_bytes),
                    virtual_path=virtual_path,
                    local_path=target_path,
                    mime_type=detect_mime_type(file_bytes, kind="file", file_name=target_path.name),
                    sha256=hashlib.sha256(file_bytes).hexdigest(),
                )
            )
            await _complete_staged_write(target_path, file_bytes)
    except BaseException:
        cleanup_staged_message_files(staged_files)
        raise

    return staged_files

