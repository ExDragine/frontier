import asyncio
import json
import logging
import os
import re
import stat

from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

# ── 安全白名单 ────────────────────────────────────────────────────────────────
# 仅允许以下命令作为 MCP 服务器入口
_ALLOWED_COMMANDS = frozenset({"npx", "uvx", "python", "python3", "node"})
_MCP_STARTUP_TIMEOUT_SECONDS = 30

# 参数中禁止包含这些 shell 危险模式
_FORBIDDEN_ARG_PATTERNS = (
    re.compile(r"[;&|`$(){}!#~<>\\]", re.ASCII),
    re.compile(r"\b(?:curl|wget|nc|bash|sh|zsh|perl|ruby)\b"),
    re.compile(r"/bin/"),
)

_MCP_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "minLength": 1},
            "args": {"type": "array", "items": {"type": "string"}},
            "env": {"type": "object"},
            "url": {"type": "string", "format": "uri"},
            "transport": {"type": "string", "enum": ["stdio", "sse", "streamable_http", "http"]},
        },
        "required": ["transport"],
        "additionalProperties": False,
    },
}


def _validate_mcp_config(description: dict) -> None:
    """验证 mcp.json 结构和安全性，拒绝可疑配置。"""
    import jsonschema

    jsonschema.validate(description, _MCP_JSON_SCHEMA)

    for name, entry in description.items():
        command = entry.get("command", "")
        args = entry.get("args", [])

        # HTTP-based MCP servers use url instead of command — skip cmd validation
        if not command:
            if not entry.get("url"):
                raise ValueError(f"MCP server '{name}': 必须提供 'command' (stdio/sse) 或 'url' (http)")
            continue

        if command not in _ALLOWED_COMMANDS:
            raise ValueError(
                f"MCP server '{name}': 不允许的命令 '{command}'。仅允许: {', '.join(sorted(_ALLOWED_COMMANDS))}"
            )

        for idx, arg in enumerate(args):
            for pattern in _FORBIDDEN_ARG_PATTERNS:
                if pattern.search(arg):
                    raise ValueError(f"MCP server '{name}': 参数 '{arg}' (位置 {idx}) 包含禁止的 shell 模式。")


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


tools_description = _load_and_validate()
client = MultiServerMCPClient(tools_description)

_mcp_tools = None


def _error_summary(exc: BaseException) -> str:
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return f"{type(exc).__name__}: {exc}"


async def _load_mcp_tools() -> list:
    async def load_server(name: str) -> list:
        try:
            return await asyncio.wait_for(
                client.get_tools(server_name=name),
                timeout=_MCP_STARTUP_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.error("MCP 服务 '%s' 加载失败，已跳过: %s", name, _error_summary(exc))
            return []

    batches = await asyncio.gather(*(load_server(name) for name in tools_description))
    return [tool for batch in batches for tool in batch]


def mcp_get_tools():
    """在同步启动阶段加载 MCP 工具；单个服务失败时跳过该服务。"""
    global _mcp_tools
    if _mcp_tools is not None:
        return _mcp_tools

    _mcp_tools = asyncio.run(_load_mcp_tools())
    return _mcp_tools
