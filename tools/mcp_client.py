import asyncio
import json
import logging
import os
import stat
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from utils.mcp import build_mcp_adapter

logger = logging.getLogger(__name__)

_MCP_STARTUP_TIMEOUT_SECONDS = 30
_MCP_MAX_STARTUP_TIMEOUT_SECONDS = 300

_MCP_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "headers": {"type": "object", "additionalProperties": {"type": "string"}},
            "url": {"type": "string", "minLength": 1},
            "transport": {"type": "string", "enum": ["streamable_http", "http"]},
            "startup_timeout_seconds": {
                "type": "number",
                "minimum": 5,
                "maximum": _MCP_MAX_STARTUP_TIMEOUT_SECONDS,
            },
        },
        "required": ["url"],
        "additionalProperties": False,
    },
}


def _validate_mcp_config(description: dict) -> None:
    """仅接受 HTTP(S) Streamable HTTP 端点，不支持启动本地进程。"""
    import jsonschema

    try:
        jsonschema.validate(description, _MCP_JSON_SCHEMA)
    except jsonschema.ValidationError as exc:
        # ValidationError's full text includes the config instance and credentials.
        location = ".".join(str(part) for part in exc.absolute_path) or "root"
        raise ValueError(f"MCP 配置字段无效: {location} ({exc.validator})") from None

    for name, entry in description.items():
        try:
            parsed = urlsplit(entry["url"])
            valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
            _ = parsed.port  # Reject malformed ports without logging the URL.
            valid = valid and not any(char.isspace() for char in entry["url"])
        except ValueError:
            valid = False
        if not valid:
            raise ValueError(f"MCP server '{name}': url 必须是有效的 HTTP(S) 地址") from None


def _check_mcp_json_file_permissions(path: str) -> None:
    """确保 mcp.json 文件权限安全（仅 owner 可写）。

    Windows 下 os.stat().st_mode 不反映 Unix 权限语义，跳过检查。
    """
    if os.name == "nt":
        return

    try:
        mode = os.stat(path).st_mode
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            logger.warning(
                "⚠️  mcp.json 文件权限不安全 (%s)，建议设为 0600 或 0644（仅 owner 可写）",
                oct(mode & 0o777),
            )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"mcp.json 文件不存在: {path}") from exc
    except OSError as exc:
        raise OSError(f"无法读取 mcp.json: {exc}") from exc


def _load_and_validate(config_path: str = "mcp.json") -> dict:
    """加载并校验 mcp.json，安全异常时直接终止启动。"""
    _check_mcp_json_file_permissions(config_path)

    with open(config_path, encoding="utf-8") as f:
        description: dict = json.load(f)

    try:
        _validate_mcp_config(description)
    except ValueError as exc:
        # 安全校验失败 — 这是配置错误，不应静默跳过
        raise RuntimeError(f"MCP 配置安全校验失败: {exc}") from exc

    logger.info("MCP 配置校验通过: %d 个服务", len(description))
    return description


@dataclass
class _Server:
    config: dict
    tools: list | None = None
    retry_at: float = 0


_servers: dict[str, _Server] | None = None
_RETRY_SECONDS = 60


def _error_summary(exc: BaseException) -> str:
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    # Remote exception text can include the authenticated URL or headers.
    status = getattr(getattr(exc, "response", None), "status_code", None)
    return f"{type(exc).__name__} (HTTP {status})" if status is not None else type(exc).__name__


async def _discover(name: str, server: _Server) -> None:
    if server.tools is not None or time.monotonic() < server.retry_at:
        return
    try:
        async with asyncio.timeout(server.config.get("startup_timeout_seconds", _MCP_STARTUP_TIMEOUT_SECONDS)):
            server.tools = await build_mcp_adapter(server.config).list_tools()
        logger.info("MCP 服务 '%s' 已加载 %d 个工具", name, len(server.tools))
    except Exception as exc:
        server.retry_at = time.monotonic() + _RETRY_SECONDS
        logger.warning("MCP 服务 '%s' 发现失败: %s；%ds 后可重试", name, _error_summary(exc), _RETRY_SECONDS)


async def mcp_get_tools_async() -> list:
    """The only discovery entry point; successful servers are cached until restart."""
    from utils.agents.runtime import run_serialized

    async def load():
        global _servers
        if _servers is None:
            _servers = {name: _Server(entry) for name, entry in _load_and_validate().items()}
        await asyncio.gather(*(_discover(name, server) for name, server in _servers.items()))
        return [tool for server in _servers.values() for tool in server.tools or []]

    return await run_serialized("mcp-discovery", load)
