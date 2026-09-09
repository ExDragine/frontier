import asyncio
import os
import shutil
import tempfile
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import tomlkit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from utils.configs import CONFIG_PATH, parse_config

from ..auth import require_auth

router = APIRouter()
AUTH_DEPENDENCY = Depends(require_auth)

TOML_PATH = CONFIG_PATH
BACKUP_DIR = Path("configs/backups")
_settings_write_lock = asyncio.Lock()

# 需要脱敏的段和字段
SENSITIVE_FIELDS = {
    "key": {
        "nasa_api_key",
        "github_pat",
    },
    "dashboard": {"jwt_secret", "password"},
}


def _mask_value(value: str) -> str:
    """对敏感值进行脱敏"""
    if not value or len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def _read_toml() -> dict:
    """读取 env.toml 并返回原始 dict"""
    with open(TOML_PATH, "rb") as f:
        return tomllib.load(f)


def _sanitize_config(config: dict) -> dict:
    """对敏感字段进行脱敏"""
    result = {}
    for section, values in config.items():
        if isinstance(values, dict):
            result[section] = _sanitize_section(section, values)
        else:
            result[section] = values
    return result


def _sanitize_section(section: str, values: dict) -> dict:
    result = {}
    sensitive = SENSITIVE_FIELDS.get(section, set())
    for k, v in values.items():
        if isinstance(v, dict):
            result[k] = _sanitize_section(section, v)
        elif (k in sensitive or k == "api_key") and isinstance(v, str):
            result[k] = _mask_value(v)
        else:
            result[k] = v
    return result


def _is_masked(value: str) -> bool:
    """检查值是否是脱敏后的值"""
    return isinstance(value, str) and value.startswith("****")


def _is_sensitive_key(section: str, key: str) -> bool:
    return key in SENSITIVE_FIELDS.get(section, set()) or key == "api_key"


def _resolve_update_value(section: str, key: str, original_value, new_value):
    if _is_sensitive_key(section, key) and _is_masked(new_value):
        return original_value
    if isinstance(original_value, Mapping) and isinstance(new_value, Mapping):
        merged = dict(original_value)
        for child_key, child_value in new_value.items():
            merged[child_key] = _resolve_update_value(
                section,
                child_key,
                original_value.get(child_key),
                child_value,
            )
        return merged
    return new_value


def _table_values(value: Any, section: str) -> dict[str, Any]:
    unwrapped = value.unwrap()
    if not isinstance(unwrapped, dict):
        raise HTTPException(status_code=422, detail=f"配置段 '{section}' 必须是表")
    return unwrapped


def _backup_config():
    """备份当前配置文件"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.chmod(0o700)
    fd, name = tempfile.mkstemp(prefix="env.toml.", suffix=".bak", dir=BACKUP_DIR)
    backup_path = Path(name)
    try:
        with os.fdopen(fd, "wb") as backup, open(TOML_PATH, "rb") as source:
            shutil.copyfileobj(source, backup)
            backup.flush()
            os.fsync(backup.fileno())
    except BaseException:
        backup_path.unlink(missing_ok=True)
        raise

    # 保留最近 10 个备份
    backups = sorted(BACKUP_DIR.glob("env.toml.*.bak"), key=lambda p: p.stat().st_mtime_ns)
    while len(backups) > 10:
        backups.pop(0).unlink()

    return backup_path


def _reload_env_config(config: dict | None = None):
    """热重载 EnvConfig — 委托给 configs.py 的统一入口。"""
    from utils.configs import EnvConfig

    if config is None:
        with open(TOML_PATH, "rb") as f:
            config = tomllib.load(f)
    EnvConfig.reload(config)


@router.get("/")
async def get_settings(user: dict = AUTH_DEPENDENCY):
    """获取完整配置（敏感字段脱敏）"""
    config = await _read_settings()
    return {"config": _sanitize_config(config)}


async def _read_settings() -> dict:
    # Readers must not observe a published file whose runtime reload is still
    # pending, especially when activation subsequently rolls back.
    async with _settings_write_lock:
        return await asyncio.to_thread(_read_toml)


@router.get("/{section}")
async def get_section(section: str, user: dict = AUTH_DEPENDENCY):
    """获取单个配置段"""
    config = await _read_settings()
    if section not in config:
        raise HTTPException(status_code=404, detail=f"配置段 '{section}' 不存在")

    if not isinstance(config[section], dict):
        raise HTTPException(status_code=422, detail=f"配置段 '{section}' 必须是表")
    return {"section": section, "config": _sanitize_section(section, config[section])}


class SectionUpdate(BaseModel):
    config: dict[str, Any]


def _atomic_write(path: Path, content: bytes) -> None:
    """Publish a complete owner-readable file without sharing temporary names."""
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _changed_fields(before: Mapping, after: Mapping, prefix: str = "") -> list[str]:
    fields = []
    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key), after.get(key)
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(old, Mapping) and isinstance(new, Mapping):
            fields.extend(_changed_fields(old, new, name))
        elif old != new:
            fields.append(name)
    return fields


def _persist_section(section: str, new_values: dict) -> tuple[dict, dict, Path | None, list[str]]:
    """Read, validate, back up and publish under the caller's write lock."""
    with open(TOML_PATH, encoding="utf-8") as stream:
        doc = tomlkit.load(stream)
    if section not in doc:
        raise HTTPException(status_code=404, detail=f"配置段 '{section}' 不存在")
    old_config = doc.unwrap()
    original = _table_values(doc[section], section)
    for key, value in new_values.items():
        doc[section][key] = _resolve_update_value(section, key, original.get(key), value)  # type: ignore
    new_config = doc.unwrap()
    try:
        parse_config(new_config)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"配置校验失败: {exc}") from exc
    changed_fields = _changed_fields(old_config, new_config)
    if not changed_fields:
        return old_config, new_config, None, []
    try:
        backup_path = _backup_config()
        _atomic_write(TOML_PATH, tomlkit.dumps(doc).encode("utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"写入配置失败: {exc}") from exc
    return old_config, new_config, backup_path, changed_fields


def _restore_config(backup_path: Path) -> None:
    _atomic_write(TOML_PATH, backup_path.read_bytes())


async def _reload_or_restore(new_config: dict, old_config: dict, backup_path: Path) -> None:
    try:
        # Keep the synchronous runtime snapshot switch on the event-loop thread.
        _reload_env_config(new_config)
    except Exception as exc:
        try:
            await asyncio.to_thread(_restore_config, backup_path)
        except Exception as rollback_exc:
            raise HTTPException(
                status_code=500,
                detail=f"配置重载失败且恢复文件失败，请从备份恢复: {backup_path}",
            ) from rollback_exc
        rollback_error = None
        try:
            _reload_env_config(old_config)
        except Exception as restore_exc:
            rollback_error = restore_exc
        detail = f"配置重载失败，已恢复原配置: {exc}"
        if rollback_error is not None:
            detail += f"；恢复后运行时重载也失败: {rollback_error}"
        raise HTTPException(status_code=500, detail=detail) from exc


async def _update_section(section: str, new_values: dict) -> dict:
    from utils.configs import EnvConfig

    async with _settings_write_lock:
        old_config, new_config, backup_path, changed_fields = await asyncio.to_thread(
            _persist_section, section, new_values,
        )
        if backup_path is not None:
            await _reload_or_restore(new_config, old_config, backup_path)
        return {
            "message": f"配置段 '{section}' 已更新" if changed_fields else f"配置段 '{section}' 无变更",
            "backup": str(backup_path) if backup_path is not None else None,
            "changed_fields": changed_fields,
            "config_revision": EnvConfig.REVISION,
            "restart_required": False,
            "restart_required_fields": [],
            "activation": "next_request" if changed_fields else "unchanged",
        }


@router.put("/{section}")
async def update_section(section: str, body: SectionUpdate, user: dict = AUTH_DEPENDENCY):
    """Serialize writes and finish disk/runtime reconciliation even if a client leaves."""
    operation = asyncio.create_task(_update_section(section, body.config))
    try:
        return await asyncio.shield(operation)
    except asyncio.CancelledError:
        # to_thread cannot cancel an in-flight disk write. Keep the transaction
        # alive until its new or restored runtime snapshot matches the file.
        await asyncio.gather(operation, return_exceptions=True)
        raise
