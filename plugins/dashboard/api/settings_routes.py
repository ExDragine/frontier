import os
import shutil
import time
import tomllib
from pathlib import Path
from typing import Any

import tomlkit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_auth

router = APIRouter()
AUTH_DEPENDENCY = Depends(require_auth)

TOML_PATH = Path("env.toml")
BACKUP_DIR = Path("configs/backups")

# 需要脱敏的段和字段
SENSITIVE_FIELDS = {
    "key": {
        "openai_api_key",
        "paint_api_key",
        "video_api_key",
        "google_api_key",
        "anthropic_api_key",
        "deepseek_api_key",
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
    if isinstance(original_value, dict) and isinstance(new_value, dict):
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


def _backup_config():
    """备份当前配置文件"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    backup_path = BACKUP_DIR / f"env.toml.{timestamp}.bak"
    shutil.copy2(TOML_PATH, backup_path)

    # 保留最近 10 个备份
    backups = sorted(BACKUP_DIR.glob("env.toml.*.bak"), key=lambda p: p.stat().st_mtime)
    while len(backups) > 10:
        backups.pop(0).unlink()

    return backup_path


def _reload_env_config():
    """热重载 EnvConfig — 委托给 configs.py 的统一入口。"""
    from utils.configs import EnvConfig

    with open(TOML_PATH, "rb") as f:
        config = tomllib.load(f)
    EnvConfig.reload(config)


@router.get("/")
async def get_settings(user: dict = AUTH_DEPENDENCY):
    """获取完整配置（敏感字段脱敏）"""
    config = _read_toml()
    return {"config": _sanitize_config(config)}


@router.get("/{section}")
async def get_section(section: str, user: dict = AUTH_DEPENDENCY):
    """获取单个配置段"""
    config = _read_toml()
    if section not in config:
        raise HTTPException(status_code=404, detail=f"配置段 '{section}' 不存在")

    result = dict(config[section])
    sensitive = SENSITIVE_FIELDS.get(section, set())
    for k, v in result.items():
        if k in sensitive and isinstance(v, str):
            result[k] = _mask_value(v)
    return {"section": section, "config": result}


class SectionUpdate(BaseModel):
    config: dict[str, Any]


@router.put("/{section}")
async def update_section(section: str, body: SectionUpdate, user: dict = AUTH_DEPENDENCY):
    """更新单个配置段"""
    with open(TOML_PATH, encoding="utf-8") as f:
        doc = tomlkit.load(f)

    if section not in doc:
        raise HTTPException(status_code=404, detail=f"配置段 '{section}' 不存在")

    # 备份
    backup_path = _backup_config()

    # 获取原始值以处理脱敏字段
    original = dict(doc[section])
    sensitive = SENSITIVE_FIELDS.get(section, set())

    new_values = body.config
    for k, v in new_values.items():
        if k in sensitive and _is_masked(v):
            # 脱敏值不做修改，保留原值
            continue
        doc[section][k] = _resolve_update_value(section, k, original.get(k), v)  # type: ignore

    # 原子写入：先写临时文件，再替换
    tmp_path = TOML_PATH.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            tomlkit.dump(doc, f)
        os.replace(tmp_path, TOML_PATH)
    except Exception as e:
        # 写入失败，恢复备份
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail=f"写入配置失败: {e}") from e

    # 热重载 EnvConfig
    try:
        _reload_env_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置已保存但重载失败: {e}") from e

    return {
        "message": f"配置段 '{section}' 已更新",
        "backup": str(backup_path),
    }
