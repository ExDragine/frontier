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

TOML_PATH = Path("env.toml")
BACKUP_DIR = Path("configs/backups")

# 需要脱敏的段和字段
SENSITIVE_FIELDS = {
    "key": {"openai_api_key", "nasa_api_key", "github_pat"},
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


def _read_tomlkit() -> tomlkit.TOMLDocument:
    """使用 tomlkit 读取以保留注释和格式"""
    with open(TOML_PATH, "r", encoding="utf-8") as f:
        return tomlkit.load(f)


def _sanitize_config(config: dict) -> dict:
    """对敏感字段进行脱敏"""
    result = {}
    for section, values in config.items():
        if isinstance(values, dict):
            result[section] = {}
            sensitive = SENSITIVE_FIELDS.get(section, set())
            for k, v in values.items():
                if k in sensitive and isinstance(v, str):
                    result[section][k] = _mask_value(v)
                else:
                    result[section][k] = v
        else:
            result[section] = values
    return result


def _is_masked(value: str) -> bool:
    """检查值是否是脱敏后的值"""
    return isinstance(value, str) and value.startswith("****")


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
    """热重载 EnvConfig"""
    from utils.configs import EnvConfig

    with open(TOML_PATH, "rb") as f:
        config = tomllib.load(f)

    info = config.get("information", {})
    ep = config.get("endpoint", {})
    key = config.get("key", {})
    fn = config.get("function", {})
    msg = config.get("message", {})
    db = config.get("database", {})
    dbg = config.get("debug", {})
    mem = config.get("memory", {})
    dash = config.get("dashboard", {})

    EnvConfig.BOT_NAME = info.get("name", EnvConfig.BOT_NAME)
    EnvConfig.OPENAI_BASE_URL = ep.get("openai_base_url", EnvConfig.OPENAI_BASE_URL)
    EnvConfig.BASIC_MODEL = ep.get("basic_model", EnvConfig.BASIC_MODEL)
    EnvConfig.ADVAN_MODEL = ep.get("advan_model", EnvConfig.ADVAN_MODEL)
    EnvConfig.PAINT_MODEL = ep.get("paint_model", EnvConfig.PAINT_MODEL)

    from pydantic import SecretStr

    EnvConfig.OPENAI_API_KEY = SecretStr(key.get("openai_api_key", ""))
    EnvConfig.NASA_API_KEY = SecretStr(key.get("nasa_api_key", ""))
    EnvConfig.GITHUB_PAT = SecretStr(key.get("github_pat", ""))

    EnvConfig.AGENT_MODULE_ENABLED = fn.get("agent_module_enabled", EnvConfig.AGENT_MODULE_ENABLED)
    EnvConfig.PAINT_MODULE_ENABLED = fn.get("paint_module_enabled", EnvConfig.PAINT_MODULE_ENABLED)
    EnvConfig.AGENT_CAPABILITY = fn.get("agent_capability", EnvConfig.AGENT_CAPABILITY)
    EnvConfig.AGENT_WITHELIST_MODE = fn.get("agent_whitelist_mode", EnvConfig.AGENT_WITHELIST_MODE)
    EnvConfig.AGENT_WITHELIST_PERSON_LIST = fn.get("agent_whitelist_person_list", EnvConfig.AGENT_WITHELIST_PERSON_LIST)
    EnvConfig.AGENT_WITHELIST_GROUP_LIST = fn.get("agent_whitelist_group_list", EnvConfig.AGENT_WITHELIST_GROUP_LIST)
    EnvConfig.AGENT_BLACKLIST_PERSON_LIST = fn.get("agent_blacklist_person_list", EnvConfig.AGENT_BLACKLIST_PERSON_LIST)
    EnvConfig.AGENT_BLACKLIST_GROUP_LIST = fn.get("agent_blacklist_group_list", EnvConfig.AGENT_BLACKLIST_GROUP_LIST)
    EnvConfig.PAINT_WITHELIST_MODE = fn.get("paint_whitelist_mode", EnvConfig.PAINT_WITHELIST_MODE)
    EnvConfig.PAINT_WITHELIST_PERSON_LIST = fn.get("paint_whitelist_person_list", EnvConfig.PAINT_WITHELIST_PERSON_LIST)
    EnvConfig.PAINT_WITHELIST_GROUP_LIST = fn.get("paint_whitelist_group_list", EnvConfig.PAINT_WITHELIST_GROUP_LIST)
    EnvConfig.PAINT_BLACKLIST_PERSON_LIST = fn.get("paint_blacklist_person_list", EnvConfig.PAINT_BLACKLIST_PERSON_LIST)
    EnvConfig.PAINT_BLACKLIST_GROUP_LIST = fn.get("paint_blacklist_group_list", EnvConfig.PAINT_BLACKLIST_GROUP_LIST)
    EnvConfig.AGENT_DEBUG_MODE = dbg.get("agent_debug_mode", EnvConfig.AGENT_DEBUG_MODE)

    EnvConfig.TEST_GROUP_ID = msg.get("test_group_id", EnvConfig.TEST_GROUP_ID)
    EnvConfig.ANNOUNCE_GROUP_ID = msg.get("announce_group_id", EnvConfig.TEST_GROUP_ID)
    EnvConfig.RAW_MESSAGE_GROUP_ID = msg.get("raw_message_group_id", EnvConfig.RAW_MESSAGE_GROUP_ID)
    EnvConfig.APOD_GROUP_ID = msg.get("apod_group_id", EnvConfig.TEST_GROUP_ID)
    EnvConfig.EARTH_NOW_GROUP_ID = msg.get("earth_now_group_id", EnvConfig.TEST_GROUP_ID)
    EnvConfig.NEWS_SUMMARY_GROUP_ID = msg.get("news_summary_group_id", EnvConfig.TEST_GROUP_ID)
    EnvConfig.EARTHQUAKE_GROUP_ID = msg.get("earthquake_group_id", EnvConfig.TEST_GROUP_ID)

    EnvConfig.QUERY_MESSAGE_NUMBERS = db.get("query_message_numbers", EnvConfig.QUERY_MESSAGE_NUMBERS)

    EnvConfig.MEMORY_ENABLED = mem.get("enabled", True)
    EnvConfig.MEMORY_SCHEMA_VERSION = str(mem.get("schema_version", "v2"))

    EnvConfig.DASHBOARD_PASSWORD = dash.get("password", "admin")
    EnvConfig.DASHBOARD_JWT_SECRET = dash.get("jwt_secret", "frontier-dashboard-default-secret")
    EnvConfig.DASHBOARD_JWT_EXPIRE_HOURS = int(dash.get("jwt_expire_hours", 24))


@router.get("/")
async def get_settings(user: dict = Depends(require_auth)):
    """获取完整配置（敏感字段脱敏）"""
    config = _read_toml()
    return {"config": _sanitize_config(config)}


@router.get("/{section}")
async def get_section(section: str, user: dict = Depends(require_auth)):
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
async def update_section(section: str, body: SectionUpdate, user: dict = Depends(require_auth)):
    """更新单个配置段"""
    doc = _read_tomlkit()

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
        doc[section][k] = v  # type: ignore

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
        raise HTTPException(status_code=500, detail=f"写入配置失败: {e}")

    # 热重载 EnvConfig
    try:
        _reload_env_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置已保存但重载失败: {e}")

    return {
        "message": f"配置段 '{section}' 已更新",
        "backup": str(backup_path),
    }
