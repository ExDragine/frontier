import asyncio
import json
import logging
import os
import stat
import time
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


tools_description = None

_mcp_tools = None
_server_tools: dict[str, list] = {}
_server_failures: dict[str, int] = {}
_retry_at: dict[str, float] = {}


def _error_summary(exc: BaseException) -> str:
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return f"{type(exc).__name__}: {exc}"


async def _load_mcp_tools() -> list:
    global tools_description
    if tools_description is None:
        tools_description = _load_and_validate()

    async def load_server(name: str) -> None:
        entry = tools_description[name]
        timeout = float(entry.get("startup_timeout_seconds", _MCP_STARTUP_TIMEOUT_SECONDS))
        try:
            adapter = build_mcp_adapter(entry)
            discovered = await asyncio.wait_for(
                adapter.list_tools(),
                timeout=timeout,
            )
            _server_tools[name] = discovered
            _server_failures.pop(name, None)
            _retry_at.pop(name, None)
            return
        except TimeoutError:
            logger.error(
                "HTTP MCP 服务 '%s' 工具发现超时（%.0fs），将退避重试。"
                "请检查端点连接与认证配置；"
                "如网络确实较慢，可为该服务设置 startup_timeout_seconds。",
                name,
                timeout,
            )
        except Exception as exc:
            logger.error("MCP 服务 '%s' 加载失败，已跳过: %s", name, _error_summary(exc))

        failures = min(_server_failures.get(name, 0) + 1, 5)
        _server_failures[name] = failures
        _retry_at[name] = time.monotonic() + min(30 * 2 ** (failures - 1), 300)

    await asyncio.gather(*(
        load_server(name) for name in tools_description
        if name not in _server_tools and time.monotonic() >= _retry_at.get(name, 0)
    ))
    combined = [tool for name in tools_description for tool in _server_tools.get(name, [])]
    if _mcp_tools is not None and len(combined) == len(_mcp_tools) and all(
        left is right for left, right in zip(combined, _mcp_tools, strict=True)
    ):
        return _mcp_tools
    return combined


async def mcp_get_tools_async():
    """Cache healthy servers; retry failed discovery with a 30–300 second backoff."""
    from utils.agents.runtime import run_serialized

    async def load():
        global _mcp_tools
        _mcp_tools = await _load_mcp_tools()
        return _mcp_tools

    return await run_serialized("mcp-discovery", load)


def mcp_get_tools():
    """在同步启动阶段加载 MCP 工具；单个服务失败时跳过该服务。"""
    global _mcp_tools
    if _mcp_tools is not None:
        return _mcp_tools

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError("MCP tools are not initialized; await agent_tools.initialize() first")
    _mcp_tools = asyncio.run(mcp_get_tools_async())
    return _mcp_tools
