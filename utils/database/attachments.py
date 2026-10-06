"""Attachment persistence: atomic file staging, indexing and cleanup."""

import hashlib
import logging
import os
import posixpath
import threading
import time
from contextlib import contextmanager, suppress

from sqlalchemy import Engine
from sqlmodel import Session, col, func, select

from utils.agents.runtime import conversation_workspace_key
from utils.media import ResolvedMedia, resolve_media

from .engine import _run_database
from .models import MessageAttachment
from .rows import _attachments_for_message, _find_message, _refresh_message_model_states

logger = logging.getLogger(__name__)

_ATTACHMENT_KIND_DIRECTORIES = {
    "image": "images",
    "audio": "audio",
    "video": "videos",
    "file": "files",
}
_ATTACHMENT_WRITE_LOCKS = tuple(threading.Lock() for _ in range(64))


@contextmanager
def _lock_attachment_paths(paths: list[str]):
    indexes = sorted(
        {
            int.from_bytes(hashlib.sha256(os.path.abspath(path).encode("utf-8")).digest()[:2], "big")
            % len(_ATTACHMENT_WRITE_LOCKS)
            for path in paths
        }
    )
    locks = [_ATTACHMENT_WRITE_LOCKS[index] for index in indexes]
    for lock in locks:
        lock.acquire()
    try:
        yield
    finally:
        for lock in reversed(locks):
            lock.release()


def _message_workspace_key(user_id: int, group_id: int | None) -> str:
    return conversation_workspace_key(user_id, group_id)


def _attachment_paths(user_id: int, group_id: int | None, *parts: str) -> tuple[str, str]:
    workspace_key = _message_workspace_key(user_id, group_id)
    physical_path = os.path.join("cache", "sandbox", "memory", workspace_key, *parts)
    virtual_path = posixpath.join("/memory", workspace_key, *parts)
    return physical_path, virtual_path


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _prune_empty_attachment_dirs(path: str) -> None:
    root = os.path.abspath(os.path.join(os.getcwd(), "cache", "sandbox", "memory"))
    current = os.path.abspath(os.path.dirname(path))
    while current.startswith(root) and current != root:
        try:
            os.rmdir(current)
        except OSError:
            break
        current = os.path.dirname(current)


class _PendingFileWrite:
    """Stage one attachment write and make replacement rollback-capable."""

    def __init__(self, target_path: str, data: bytes):
        self.target_path = target_path
        suffix = f"{os.getpid()}-{time.time_ns()}"
        self.temp_path = f"{target_path}.frontier-pending-{suffix}"
        self.backup_path: str | None = None
        self.installed = False
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            with open(self.temp_path, "xb") as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
        except Exception:
            self._remove(self.temp_path)
            raise

    @staticmethod
    def _remove(path: str | None) -> None:
        if path is None:
            return
        with suppress(FileNotFoundError):
            os.remove(path)

    def install(self) -> None:
        if os.path.exists(self.target_path):
            self.backup_path = f"{self.target_path}.frontier-backup-{os.getpid()}-{time.time_ns()}"
            os.replace(self.target_path, self.backup_path)
        try:
            os.replace(self.temp_path, self.target_path)
            self.installed = True
        except Exception:
            if self.backup_path is not None:
                os.replace(self.backup_path, self.target_path)
                self.backup_path = None
            raise

    def rollback(self) -> None:
        if self.backup_path is not None and os.path.exists(self.backup_path):
            os.replace(self.backup_path, self.target_path)
            self.backup_path = None
        elif self.installed:
            self._remove(self.target_path)
        self._remove(self.temp_path)

    def finish(self) -> None:
        for path in (self.backup_path, self.temp_path):
            try:
                self._remove(path)
            except OSError as exc:
                logger.warning("附件原子写入临时文件清理失败 %s: %s", path, exc)


class _MessageAttachmentManager:
    """通用附件索引：记录、查询和按 DB 清理文件。"""

    def __init__(self, engine):
        self.engine = engine

    async def insert_attachment(
        self,
        *,
        msg_time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        kind: str,
        physical_path: str,
        virtual_path: str,
        file_name: str,
        file_size: int | None,
        expires_at: int,
        source_type: str = "message",
        mime_type: str | None = None,
        sha256: str | None = None,
        metadata_json: str = "{}",
        message_id: int | None = None,
    ) -> MessageAttachment:
        def _do():
            workspace_key = _message_workspace_key(user_id, group_id)
            now_ms = int(time.time() * 1000)
            with Session(self.engine, expire_on_commit=False) as session:
                message = _find_message(
                    session, msg_time, message_id=message_id, scope=(user_id, group_id), msg_id=msg_id,
                )
                resolved_id = message.id if message is not None else message_id
                attachment = session.exec(
                    select(MessageAttachment).where(MessageAttachment.physical_path == physical_path).limit(1)
                ).first()
                affected_message_times = {msg_time}
                if attachment is None:
                    attachment = MessageAttachment(
                        msg_time=msg_time,
                        message_id=resolved_id,
                        msg_id=msg_id,
                        user_id=user_id,
                        group_id=group_id,
                        workspace_key=workspace_key,
                        kind=kind,
                        source_type=source_type,
                        file_name=file_name,
                        mime_type=mime_type,
                        file_size=file_size,
                        sha256=sha256,
                        physical_path=physical_path,
                        virtual_path=virtual_path,
                        created_at=now_ms,
                        expires_at=expires_at,
                        metadata_json=metadata_json,
                    )
                else:
                    affected_message_times.add(attachment.msg_time)
                    attachment.msg_time = msg_time
                    attachment.message_id = resolved_id
                    attachment.msg_id = msg_id
                    attachment.user_id = user_id
                    attachment.group_id = group_id
                    attachment.workspace_key = workspace_key
                    attachment.kind = kind
                    attachment.source_type = source_type
                    attachment.file_name = file_name
                    attachment.mime_type = mime_type
                    attachment.file_size = file_size
                    attachment.sha256 = sha256
                    attachment.virtual_path = virtual_path
                    attachment.expires_at = expires_at
                    attachment.metadata_json = metadata_json
                session.add(attachment)
                session.flush()
                _refresh_message_model_states(session, affected_message_times)
                session.commit()
                return attachment

        def _locked_do():
            with _lock_attachment_paths([physical_path]):
                return _do()

        return await _run_database(self.engine, _locked_do)

    async def insert_images(
        self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes],
        *, message_id: int | None = None,
    ) -> list[str]:
        attachments = await self.insert_media(
            msg_time=msg_time,
            msg_id=None,
            user_id=user_id,
            group_id=group_id,
            media=[resolve_media(image, "image") for image in images],
            message_id=message_id,
        )
        return [attachment.physical_path for attachment in attachments]

    async def insert_media(
        self,
        *,
        msg_time: int,
        msg_id: int | None,
        user_id: int,
        group_id: int | None,
        media: list[ResolvedMedia],
        source_type: str = "message",
        message_id: int | None = None,
    ) -> list[MessageAttachment]:
        """Persist downloaded media and create attachment rows in one DB operation."""

        def _do():
            from utils.configs import EnvConfig

            now_ms = int(time.time() * 1000)
            expires_ms = now_ms + EnvConfig.MEDIA_TTL_DAYS * 86400 * 1000
            workspace_key = _message_workspace_key(user_id, group_id)
            inserted: list[MessageAttachment] = []
            pending_writes: list[_PendingFileWrite] = []
            try:
                with Session(self.engine, expire_on_commit=False) as session:
                    message = _find_message(
                        session, msg_time, message_id=message_id, scope=(user_id, group_id), msg_id=msg_id,
                    )
                    resolved_id = message.id if message is not None else message_id
                    affected_message_times = {msg_time}
                    for index, item in enumerate(media):
                        stem = f"{msg_time}-m{resolved_id}" if resolved_id is not None else str(msg_time)
                        file_name = f"{stem}_{index}{item.extension}"
                        file_path, virtual_path = _attachment_paths(
                            user_id,
                            group_id,
                            _ATTACHMENT_KIND_DIRECTORIES[item.kind],
                            file_name,
                        )
                        full_path = os.path.join(os.getcwd(), file_path)
                        pending_writes.append(_PendingFileWrite(full_path, item.data))

                        attachment = session.exec(
                            select(MessageAttachment).where(MessageAttachment.physical_path == file_path).limit(1)
                        ).first()
                        if attachment is None:
                            attachment = MessageAttachment(
                                msg_time=msg_time,
                                message_id=resolved_id,
                                msg_id=msg_id,
                                user_id=user_id,
                                group_id=group_id,
                                workspace_key=workspace_key,
                                kind=item.kind,
                                source_type=source_type,
                                file_name=file_name,
                                mime_type=item.mime_type,
                                file_size=len(item.data),
                                sha256=_sha256_bytes(item.data),
                                physical_path=file_path,
                                virtual_path=virtual_path,
                                created_at=now_ms,
                                expires_at=expires_ms,
                            )
                        else:
                            affected_message_times.add(attachment.msg_time)
                            attachment.msg_time = msg_time
                            attachment.message_id = resolved_id
                            attachment.msg_id = msg_id
                            attachment.user_id = user_id
                            attachment.group_id = group_id
                            attachment.workspace_key = workspace_key
                            attachment.kind = item.kind
                            attachment.source_type = source_type
                            attachment.file_name = file_name
                            attachment.mime_type = item.mime_type
                            attachment.file_size = len(item.data)
                            attachment.sha256 = _sha256_bytes(item.data)
                            attachment.virtual_path = virtual_path
                            attachment.expires_at = expires_ms
                        session.add(attachment)
                        inserted.append(attachment)
                    session.flush()
                    _refresh_message_model_states(session, affected_message_times)
                    for pending_write in pending_writes:
                        pending_write.install()
                    session.commit()
            except Exception:
                for pending_write in reversed(pending_writes):
                    try:
                        pending_write.rollback()
                    except OSError as exc:
                        logger.warning("回滚未提交媒体文件失败 %s: %s", pending_write.target_path, exc)
                raise
            for pending_write in pending_writes:
                pending_write.finish()
            return inserted

        def _locked_do():
            target_paths = [
                _attachment_paths(
                    user_id,
                    group_id,
                    _ATTACHMENT_KIND_DIRECTORIES[item.kind],
                    f"{msg_time}_{index}{item.extension}",
                )[0]
                for index, item in enumerate(media)
            ]
            with _lock_attachment_paths(target_paths):
                return _do()

        return await _run_database(self.engine, _locked_do)

    async def select_by_msg_time(
        self, msg_time: int, *, message_id: int | None = None,
    ) -> list[MessageAttachment]:
        def _do():
            with Session(self.engine) as session:
                message = _find_message(session, msg_time, message_id=message_id)
                if message is not None:
                    return _attachments_for_message(session, message)
                statement = (
                    select(MessageAttachment)
                    .where(MessageAttachment.msg_time == msg_time)
                    .order_by(col(MessageAttachment.id))
                )
                if message_id is not None:
                    statement = statement.where(MessageAttachment.message_id == message_id)
                return session.exec(statement).all()

        return await _run_database(self.engine, _do)

    async def select_by_msg_times(
        self, msg_times: list[int], *, kind: str | None = None
    ) -> dict[int, list[MessageAttachment]]:
        def _do():
            attachments_by_time: dict[int, list[MessageAttachment]] = {}
            if not msg_times:
                return attachments_by_time
            with Session(self.engine) as session:
                statement = select(MessageAttachment).where(col(MessageAttachment.msg_time).in_(msg_times))
                if kind is not None:
                    statement = statement.where(MessageAttachment.kind == kind)
                statement = statement.order_by(col(MessageAttachment.msg_time), col(MessageAttachment.file_name))
                for attachment in session.exec(statement).all():
                    attachments_by_time.setdefault(attachment.msg_time, []).append(attachment)
            return attachments_by_time

        return await _run_database(self.engine, _do)

    @staticmethod
    def load_files(records: list[MessageAttachment]) -> tuple[list[bytes], int]:
        files: list[bytes] = []
        missing = 0
        for record in sorted(records, key=lambda item: item.file_name):
            full_path = os.path.join(os.getcwd(), record.physical_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    files.append(f.read())
            else:
                missing += 1
        return files, missing

    async def cleanup_expired_attachments(self, now_ms: int | None = None) -> int:
        def _do():
            cutoff = int(time.time() * 1000) if now_ms is None else now_ms
            cleaned = 0
            with Session(self.engine) as session:
                expired = session.exec(select(MessageAttachment).where(MessageAttachment.expires_at < cutoff)).all()
                affected_message_times = {record.msg_time for record in expired}
                expired_paths = {record.physical_path for record in expired}
                for record in expired:
                    session.delete(record)
                    cleaned += 1
                session.flush()
                for physical_path in expired_paths:
                    remaining_references = session.exec(
                        select(func.count())
                        .select_from(MessageAttachment)
                        .where(MessageAttachment.physical_path == physical_path)
                    ).one()
                    if remaining_references:
                        continue
                    full_path = os.path.join(os.getcwd(), physical_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        _prune_empty_attachment_dirs(full_path)
                _refresh_message_model_states(session, affected_message_times)
                session.commit()
            return cleaned

        return await _run_database(self.engine, _do)


class _MessageAttachmentFacadeMixin:
    """``MessageDatabase`` attachment API, delegated to the attachment manager."""

    engine: Engine
    _attachments: _MessageAttachmentManager

    async def insert_images(
        self, msg_time: int, user_id: int, group_id: int | None, images: list[bytes],
        *, message_id: int | None = None,
    ) -> list[str]:
        self._attachments.engine = self.engine
        return await self._attachments.insert_images(msg_time, user_id, group_id, images, message_id=message_id)

    async def insert_media(self, **kwargs) -> list[MessageAttachment]:
        self._attachments.engine = self.engine
        return await self._attachments.insert_media(**kwargs)

    async def insert_attachment(self, **kwargs) -> MessageAttachment:
        self._attachments.engine = self.engine
        return await self._attachments.insert_attachment(**kwargs)

    async def select_image_attachments_by_msg_time(
        self, msg_time: int, *, message_id: int | None = None,
    ) -> list[MessageAttachment]:
        attachments = await self.select_attachments_by_msg_time(msg_time, message_id=message_id)
        return [attachment for attachment in attachments if attachment.kind == "image"]

    async def select_attachments_by_msg_time(
        self, msg_time: int, *, message_id: int | None = None,
    ) -> list[MessageAttachment]:
        self._attachments.engine = self.engine
        return await self._attachments.select_by_msg_time(msg_time, message_id=message_id)

    def load_attachment_files(self, records: list[MessageAttachment]) -> tuple[list[bytes], int]:
        return self._attachments.load_files(records)

    async def cleanup_expired_attachments(self, now_ms: int | None = None) -> int:
        self._attachments.engine = self.engine
        return await self._attachments.cleanup_expired_attachments(now_ms=now_ms)
