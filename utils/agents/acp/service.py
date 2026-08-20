"""ACP client lifecycle and Frontier progress adaptation."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import hashlib
import json
import os
import shutil
import stat
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

from nonebot import logger

from utils.agents.progress import ProgressEvent, ProgressReporter, emit_progress

PermissionPolicy = Literal["deny", "allow_once", "allow_always"]
MediaKind = Literal["image", "audio"]


def _environment_value_fingerprint(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AcpUnavailableError(RuntimeError):
    """The optional ACP SDK or configured agent process is unavailable."""


class AcpConfigurationError(RuntimeError):
    """The ACP configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class AcpInputMedia:
    kind: MediaKind
    data: bytes
    mime_type: str


@dataclass(frozen=True, slots=True)
class AcpArtifact:
    kind: MediaKind
    data: bytes
    mime_type: str


@dataclass(frozen=True, slots=True)
class AcpRunResult:
    final_response: str
    stop_reason: str
    artifacts: tuple[AcpArtifact, ...] = ()


@dataclass(frozen=True, slots=True)
class AcpAgentConfig:
    command: str
    args: tuple[str, ...] = ()
    env: tuple[tuple[str, str], ...] = ()
    inherit_env: tuple[str, ...] = ()
    description: str | None = None
    expose_as_subagent: bool = False
    auth_method: str | None = None
    permission_policy: PermissionPolicy = "deny"
    timeout_seconds: float = 600.0

    @property
    def fingerprint(self) -> tuple[Any, ...]:
        return (
            self.command,
            self.args,
            tuple((name, _environment_value_fingerprint(value)) for name, value in self.env),
            tuple(
                (name, _environment_value_fingerprint(os.environ.get(name)))
                for name in self.inherit_env
            ),
            self.description,
            self.expose_as_subagent,
            self.auth_method,
            self.permission_policy,
            self.timeout_seconds,
        )

    @property
    def environment(self) -> dict[str, str]:
        inherited: dict[str, str] = {}
        for name in self.inherit_env:
            value = os.environ.get(name)
            if value is None:
                raise AcpConfigurationError(f"ACP Agent 要求继承的环境变量 {name} 未设置")
            inherited[name] = value
        inherited.update(self.env)
        return inherited


@dataclass(frozen=True, slots=True)
class AcpConfig:
    default_agent: str
    agents: Mapping[str, AcpAgentConfig]


@dataclass(slots=True)
class _CollectedMessage:
    message_id: str | None
    text_parts: list[str] = field(default_factory=list)
    artifacts: list[AcpArtifact] = field(default_factory=list)
    intermediate: bool = False

    @property
    def text(self) -> str:
        return "".join(self.text_parts).strip()


@dataclass(slots=True)
class _AcpRuntime:
    manager: Any
    connection: Any
    process: Any
    client: _FrontierAcpClient
    session_id: str
    capabilities: Any
    fingerprint: tuple[Any, ...]
    stderr_task: asyncio.Task[None] | None = None
    close_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    closed: bool = False


def _sdk() -> ModuleType:
    try:
        import acp
    except ImportError as exc:
        raise AcpUnavailableError("未安装 ACP Python SDK；请运行 `uv sync` 安装项目依赖") from exc
    return acp


def _validate_agent_name(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AcpConfigurationError(f"{field_name} 必须是非空字符串")
    name = value.strip()
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in name):
        raise AcpConfigurationError(f"{field_name} 只能包含字母、数字、点、下划线和连字符")
    return name


def _inherit_env_names(agent_name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str)
        and item
        and item.isascii()
        and (item[0].isalpha() or item[0] == "_")
        and all(char.isalnum() or char == "_" for char in item)
        for item in value
    ):
        raise AcpConfigurationError(
            f"agents.{agent_name}.inherit_env 必须是有效环境变量名组成的数组"
        )
    if len(set(value)) != len(value):
        raise AcpConfigurationError(f"agents.{agent_name}.inherit_env 不能包含重复项")
    return tuple(value)


def _agent_config(name: str, value: Any) -> AcpAgentConfig:  # noqa: C901
    if not isinstance(value, dict):
        raise AcpConfigurationError(f"agents.{name} 必须是对象")
    unknown = set(value) - {
        "command",
        "args",
        "env",
        "inherit_env",
        "description",
        "expose_as_subagent",
        "auth_method",
        "permission_policy",
        "timeout_seconds",
    }
    if unknown:
        raise AcpConfigurationError(f"agents.{name} 包含未知字段: {', '.join(sorted(unknown))}")

    command = value.get("command")
    if not isinstance(command, str) or not command.strip() or "\x00" in command:
        raise AcpConfigurationError(f"agents.{name}.command 必须是有效的非空字符串")

    args = value.get("args", [])
    if not isinstance(args, list) or not all(isinstance(item, str) and "\x00" not in item for item in args):
        raise AcpConfigurationError(f"agents.{name}.args 必须是字符串数组")

    env = value.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(key, str) and key and "\x00" not in key and isinstance(item, str) and "\x00" not in item
        for key, item in env.items()
    ):
        raise AcpConfigurationError(f"agents.{name}.env 必须是非空键和字符串值组成的对象")

    inherit_env = _inherit_env_names(name, value.get("inherit_env", []))
    overlap = set(env) & set(inherit_env)
    if overlap:
        raise AcpConfigurationError(
            f"agents.{name}.env 与 inherit_env 不能重复定义: {', '.join(sorted(overlap))}"
        )

    description = value.get("description")
    if description is not None and (
        not isinstance(description, str)
        or not description.strip()
        or len(description.strip()) > 500
    ):
        raise AcpConfigurationError(
            f"agents.{name}.description 必须是 1 到 500 字符的字符串或省略"
        )

    expose_as_subagent = value.get("expose_as_subagent", False)
    if not isinstance(expose_as_subagent, bool):
        raise AcpConfigurationError(f"agents.{name}.expose_as_subagent 必须是布尔值")

    auth_method = value.get("auth_method")
    if auth_method is not None and (not isinstance(auth_method, str) or not auth_method.strip()):
        raise AcpConfigurationError(f"agents.{name}.auth_method 必须是非空字符串或省略")

    permission_policy = value.get("permission_policy", "deny")
    if permission_policy not in {"deny", "allow_once", "allow_always"}:
        raise AcpConfigurationError(
            f"agents.{name}.permission_policy 必须是 deny、allow_once 或 allow_always"
        )

    timeout = value.get("timeout_seconds", 600)
    if isinstance(timeout, bool) or not isinstance(timeout, int | float) or not 1 <= float(timeout) <= 3600:
        raise AcpConfigurationError(f"agents.{name}.timeout_seconds 必须在 1 到 3600 秒之间")

    return AcpAgentConfig(
        command=command.strip(),
        args=tuple(args),
        env=tuple(sorted(env.items())),
        inherit_env=inherit_env,
        description=description.strip() if isinstance(description, str) else None,
        expose_as_subagent=expose_as_subagent,
        auth_method=auth_method.strip() if isinstance(auth_method, str) else None,
        permission_policy=permission_policy,
        timeout_seconds=float(timeout),
    )


def load_acp_config(path: str | Path = "acp.json") -> AcpConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise AcpConfigurationError("acp.json 不存在；请从 acp.json.example 复制并配置 ACP Agent")
    if os.name != "nt":
        mode = config_path.stat().st_mode
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            logger.warning(
                "acp.json 文件权限不安全 (%s)，建议仅允许 owner 写入",
                oct(mode & 0o777),
            )

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcpConfigurationError(f"无法读取 acp.json: {exc}") from exc
    if not isinstance(raw, dict):
        raise AcpConfigurationError("acp.json 根节点必须是对象")
    unknown = set(raw) - {"default", "agents"}
    if unknown:
        raise AcpConfigurationError(f"acp.json 包含未知字段: {', '.join(sorted(unknown))}")
    agents_raw = raw.get("agents")
    if not isinstance(agents_raw, dict) or not agents_raw:
        raise AcpConfigurationError("acp.json.agents 必须是非空对象")

    agents: dict[str, AcpAgentConfig] = {}
    for raw_name, value in agents_raw.items():
        name = _validate_agent_name(raw_name, field_name="ACP Agent 名称")
        agents[name] = _agent_config(name, value)

    default = _validate_agent_name(raw.get("default"), field_name="acp.json.default")
    if default not in agents:
        raise AcpConfigurationError(f"默认 ACP Agent {default!r} 未在 agents 中定义")
    return AcpConfig(default_agent=default, agents=agents)


def _update_kind(update: Any) -> str:
    return str(getattr(update, "session_update", "") or "")


def _content_kind(content: Any) -> str:
    return str(getattr(content, "type", "") or "")


def _safe_title(value: Any, *, limit: int = 80) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return "工具"
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


class _FrontierAcpClient:
    """Minimal ACP Client implementation with no advertised host fs/terminal access."""

    def __init__(self, sdk: ModuleType, permission_policy: PermissionPolicy) -> None:
        self._sdk = sdk
        self._permission_policy = permission_policy
        self._reporter: ProgressReporter | None = None
        self._messages: list[_CollectedMessage] = []
        self._thought_reported = False
        self._tool_titles: dict[str, str] = {}
        self._start_new_message = False
        self.active = False

    def begin_turn(self, reporter: ProgressReporter | None) -> None:
        self._reporter = reporter
        self._messages = []
        self._thought_reported = False
        self._tool_titles = {}
        self._start_new_message = False
        self.active = True

    def finish_turn(self) -> tuple[str, tuple[AcpArtifact, ...]]:
        self.active = False
        self._reporter = None
        visible = [message for message in self._messages if not message.intermediate]
        if not visible:
            visible = self._messages
        text = "\n\n".join(part for message in visible if (part := message.text))
        artifacts = tuple(artifact for message in visible for artifact in message.artifacts)
        return text, artifacts

    def _message(self, message_id: str | None) -> _CollectedMessage:
        if (
            self._messages
            and not self._start_new_message
            and (message_id is None or self._messages[-1].message_id == message_id)
        ):
            return self._messages[-1]
        message = _CollectedMessage(message_id=message_id)
        self._messages.append(message)
        self._start_new_message = False
        return message

    async def request_permission(
        self,
        session_id: str,
        tool_call: Any,
        options: list[Any],
        **kwargs: Any,
    ) -> Any:
        del session_id, tool_call, kwargs
        if self._permission_policy != "deny":
            preferred = "allow_always" if self._permission_policy == "allow_always" else "allow_once"
            option = next((item for item in options if getattr(item, "kind", None) == preferred), None)
            if option is None and preferred == "allow_always":
                option = next((item for item in options if getattr(item, "kind", None) == "allow_once"), None)
            if option is not None:
                return self._sdk.RequestPermissionResponse(
                    outcome=self._sdk.schema.AllowedOutcome(
                        outcome="selected",
                        option_id=option.option_id,
                    )
                )
        return self._sdk.RequestPermissionResponse(
            outcome=self._sdk.schema.DeniedOutcome(outcome="cancelled")
        )

    def _collect_agent_message(self, update: Any) -> None:
        content = getattr(update, "content", None)
        message = self._message(getattr(update, "message_id", None))
        content_kind = _content_kind(content)
        if content_kind == "text":
            message.text_parts.append(str(getattr(content, "text", "") or ""))
            return
        if content_kind in {"image", "audio"}:
            try:
                data = base64.b64decode(str(getattr(content, "data", "") or ""), validate=True)
            except (ValueError, TypeError):
                logger.warning("ACP Agent 返回了无效的 %s base64 内容，已忽略", content_kind)
                return
            if data:
                message.artifacts.append(
                    AcpArtifact(
                        kind=content_kind,
                        data=data,
                        mime_type=str(getattr(content, "mime_type", "") or "application/octet-stream"),
                    )
                )
            return
        if content_kind == "resource_link":
            uri = str(getattr(content, "uri", "") or "")
            if uri:
                message.text_parts.append(f"\n{uri}\n")
            return
        if content_kind == "resource":
            resource = getattr(content, "resource", None)
            embedded_text = getattr(resource, "text", None)
            if isinstance(embedded_text, str):
                message.text_parts.append(embedded_text)

    async def _handle_tool_start(self, update: Any) -> None:
        if self._messages and not self._messages[-1].intermediate:
            current = self._messages[-1]
            current.intermediate = True
            if current.text:
                await emit_progress(
                    self._reporter,
                    ProgressEvent(type="assistant_preamble", message=current.text),
                )
        self._start_new_message = True
        tool_id = str(getattr(update, "tool_call_id", "") or "")
        title = _safe_title(getattr(update, "title", None))
        if tool_id:
            self._tool_titles[tool_id] = title
        await emit_progress(
            self._reporter,
            ProgressEvent(type="tool_call", message=f"ACP Agent 正在执行：{title}", detail={"tool_call_id": tool_id}),
        )

    async def _handle_tool_progress(self, update: Any) -> None:
        status = str(getattr(update, "status", "") or "")
        if status not in {"completed", "failed"}:
            return
        tool_id = str(getattr(update, "tool_call_id", "") or "")
        title = _safe_title(getattr(update, "title", None) or self._tool_titles.get(tool_id))
        await emit_progress(
            self._reporter,
            ProgressEvent(
                type="tool_result",
                message=f"ACP Agent {title}{'执行失败' if status == 'failed' else '已完成'}",
                detail={"tool_call_id": tool_id, "success": status == "completed"},
            ),
        )

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        del session_id, kwargs
        kind = _update_kind(update)
        if kind == "agent_thought_chunk":
            if not self._thought_reported:
                self._thought_reported = True
                await emit_progress(
                    self._reporter,
                    ProgressEvent(type="thinking", message="ACP Agent 正在思考…"),
                )
            return

        if kind == "agent_message_chunk":
            self._collect_agent_message(update)
            return

        if kind == "tool_call":
            await self._handle_tool_start(update)
            return

        if kind == "tool_call_update":
            await self._handle_tool_progress(update)
            return

        if kind in {"plan", "plan_update", "plan_removed"}:
            await emit_progress(
                self._reporter,
                ProgressEvent(type="thinking", message="ACP Agent 已更新执行计划…"),
            )

    async def write_text_file(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("fs/write_text_file")

    async def read_text_file(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("fs/read_text_file")

    async def create_terminal(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("terminal/create")

    async def terminal_output(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("terminal/output")

    async def release_terminal(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("terminal/release")

    async def wait_for_terminal_exit(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("terminal/wait_for_exit")

    async def kill_terminal(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self._sdk.RequestError.method_not_found("terminal/kill")

    async def create_elicitation(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._sdk.schema.DeclineElicitationResponse(action="decline")

    async def complete_elicitation(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    async def ext_method(self, method: str, _params: dict[str, Any]) -> dict[str, Any]:
        raise self._sdk.RequestError.method_not_found(method)

    async def ext_notification(self, method: str, _params: dict[str, Any]) -> None:
        raise self._sdk.RequestError.method_not_found(method)

    def on_connect(self, _conn: Any) -> None:
        return None


async def _drain_stderr(reader: asyncio.StreamReader | None) -> None:
    if reader is None:
        return
    recent: deque[bytes] = deque(maxlen=20)
    try:
        while line := await reader.readline():
            recent.append(line)
    except (OSError, RuntimeError):
        return


class AcpAgentService:
    """Own one ACP Agent process and session per agent/workspace pair."""

    def __init__(
        self,
        *,
        root_dir: str | Path | None = None,
        config_path: str | Path = "acp.json",
        sdk_loader: Callable[[], ModuleType] | None = None,
    ) -> None:
        self._root_dir = Path(root_dir).resolve() if root_dir is not None else None
        self._config_path = Path(config_path)
        self._sdk_loader = sdk_loader or _sdk
        self._runtimes: dict[tuple[str, str], _AcpRuntime] = {}
        self._scope_locks: dict[str, asyncio.Lock] = {}
        self._active_scopes: dict[str, int] = {}
        self._registry_lock = asyncio.Lock()

    @staticmethod
    def _scope_id(workspace_key: str) -> str:
        return hashlib.sha256(workspace_key.encode("utf-8")).hexdigest()[:24]

    def _root(self) -> Path:
        return self._root_dir or (Path.cwd() / "cache" / "acp")

    def available_agents(self) -> tuple[str, tuple[str, ...]]:
        config = load_acp_config(self._config_path)
        return config.default_agent, tuple(sorted(config.agents))

    def subagent_configs(self) -> tuple[tuple[str, AcpAgentConfig], ...]:
        """Return ACP agents explicitly opted into Deep Agents delegation."""
        config = load_acp_config(self._config_path)
        return tuple(
            (name, agent_config)
            for name, agent_config in sorted(config.agents.items())
            if agent_config.expose_as_subagent
        )

    def _resolve_config(self, agent_name: str | None) -> tuple[str, AcpAgentConfig]:
        config = load_acp_config(self._config_path)
        name = agent_name or config.default_agent
        if name not in config.agents:
            raise AcpConfigurationError(f"未配置 ACP Agent {name!r}")
        return name, config.agents[name]

    async def _launch_runtime(
        self,
        *,
        scope_id: str,
        config: AcpAgentConfig,
    ) -> _AcpRuntime:
        sdk = self._sdk_loader()
        workspace = (self._root() / "workspaces" / scope_id).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        client = _FrontierAcpClient(sdk, config.permission_policy)
        manager = sdk.spawn_agent_process(
            client,
            config.command,
            *config.args,
            env=config.environment,
            cwd=workspace,
        )
        try:
            connection, process = await manager.__aenter__()
            initialize = await asyncio.wait_for(
                connection.initialize(
                    protocol_version=sdk.PROTOCOL_VERSION,
                    client_capabilities=sdk.schema.ClientCapabilities(
                        fs=sdk.schema.FileSystemCapabilities(
                            read_text_file=False,
                            write_text_file=False,
                        ),
                        terminal=False,
                    ),
                    client_info=sdk.schema.Implementation(
                        name="frontier",
                        title="Frontier QQ Bot",
                        version="0.1.3",
                    ),
                ),
                timeout=min(config.timeout_seconds, 30),
            )
            if initialize.protocol_version != sdk.PROTOCOL_VERSION:
                raise AcpUnavailableError(
                    f"ACP 协议版本不兼容：客户端 v{sdk.PROTOCOL_VERSION}，Agent v{initialize.protocol_version}"
                )
            if config.auth_method:
                auth_methods = getattr(initialize, "auth_methods", None) or []
                available_auth_methods = {
                    str(getattr(method, "id", "") or "") for method in auth_methods
                }
                if config.auth_method not in available_auth_methods:
                    raise AcpConfigurationError(
                        f"ACP Agent 未提供认证方式 {config.auth_method!r}"
                    )
                await asyncio.wait_for(
                    connection.authenticate(method_id=config.auth_method),
                    timeout=min(config.timeout_seconds, 30),
                )
            session = await asyncio.wait_for(
                connection.new_session(cwd=str(workspace), mcp_servers=[]),
                timeout=min(config.timeout_seconds, 30),
            )
        except BaseException as exc:
            with contextlib.suppress(Exception):
                await manager.__aexit__(type(exc), exc, exc.__traceback__)
            if isinstance(exc, FileNotFoundError):
                raise AcpUnavailableError(f"找不到 ACP Agent 命令：{config.command}") from exc
            raise
        stderr_task = asyncio.create_task(_drain_stderr(getattr(process, "stderr", None)))
        return _AcpRuntime(
            manager=manager,
            connection=connection,
            process=process,
            client=client,
            session_id=session.session_id,
            capabilities=initialize.agent_capabilities,
            fingerprint=config.fingerprint,
            stderr_task=stderr_task,
        )

    async def _close_runtime(self, runtime: _AcpRuntime) -> None:
        async with runtime.close_lock:
            if runtime.closed:
                return
            runtime.closed = True
            if runtime.stderr_task is not None:
                runtime.stderr_task.cancel()
            with contextlib.suppress(Exception):
                await runtime.manager.__aexit__(None, None, None)
            if runtime.stderr_task is not None:
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await runtime.stderr_task

    async def _runtime(
        self,
        *,
        agent_name: str,
        scope_id: str,
        config: AcpAgentConfig,
    ) -> _AcpRuntime:
        key = (agent_name, scope_id)
        stale: _AcpRuntime | None = None
        async with self._registry_lock:
            runtime = self._runtimes.get(key)
            if runtime is not None and runtime.fingerprint == config.fingerprint:
                return runtime
            if runtime is not None:
                stale = self._runtimes.pop(key)
            if stale is not None:
                await self._close_runtime(stale)
            runtime = await self._launch_runtime(scope_id=scope_id, config=config)
            self._runtimes[key] = runtime
            return runtime

    @staticmethod
    def _prompt_capability(capabilities: Any, name: str) -> bool:
        prompt_capabilities = getattr(capabilities, "prompt_capabilities", None)
        return bool(getattr(prompt_capabilities, name, False))

    def _prompt_blocks(
        self,
        sdk: ModuleType,
        runtime: _AcpRuntime,
        prompt: str,
        media: tuple[AcpInputMedia, ...],
    ) -> list[Any]:
        omitted: dict[str, int] = {"image": 0, "audio": 0}
        blocks: list[Any] = []
        for item in media:
            if not self._prompt_capability(runtime.capabilities, item.kind):
                omitted[item.kind] += 1
                continue
            encoded = base64.b64encode(item.data).decode("ascii")
            if item.kind == "image":
                blocks.append(sdk.image_block(encoded, item.mime_type))
            else:
                blocks.append(sdk.audio_block(encoded, item.mime_type))
        notices = []
        if omitted["image"]:
            notices.append(f"{omitted['image']} 张图片")
        if omitted["audio"]:
            notices.append(f"{omitted['audio']} 段音频")
        if notices:
            prompt = f"{prompt}\n\n[ACP Agent 不支持相应输入，已省略：{', '.join(notices)}]"
        return [sdk.text_block(prompt), *blocks]

    async def _run_in_scope(
        self,
        prompt: str,
        *,
        name: str,
        config: AcpAgentConfig,
        scope_id: str,
        media: tuple[AcpInputMedia, ...] = (),
        progress_reporter: ProgressReporter | None = None,
    ) -> AcpRunResult:
        scope_lock = self._scope_locks.setdefault(scope_id, asyncio.Lock())
        discard = False
        runtime: _AcpRuntime | None = None
        try:
            async with scope_lock:
                runtime = await self._runtime(agent_name=name, scope_id=scope_id, config=config)
                sdk = self._sdk_loader()
                runtime.client.begin_turn(progress_reporter)
                try:
                    response = await asyncio.wait_for(
                        runtime.connection.prompt(
                            session_id=runtime.session_id,
                            prompt=self._prompt_blocks(sdk, runtime, prompt, media),
                        ),
                        timeout=config.timeout_seconds,
                    )
                except TimeoutError as exc:
                    discard = True
                    with contextlib.suppress(Exception):
                        await runtime.connection.cancel(session_id=runtime.session_id)
                    raise TimeoutError(f"ACP Agent 执行超过 {config.timeout_seconds:g} 秒") from exc
                except asyncio.CancelledError:
                    discard = True
                    with contextlib.suppress(Exception):
                        await runtime.connection.cancel(session_id=runtime.session_id)
                    raise
                except Exception:
                    discard = True
                    raise
                finally:
                    text, artifacts = runtime.client.finish_turn()
        except BaseException:
            if discard and runtime is not None:
                key = (name, scope_id)
                async with self._registry_lock:
                    if self._runtimes.get(key) is runtime:
                        self._runtimes.pop(key, None)
                await self._close_runtime(runtime)
            raise
        return AcpRunResult(
            final_response=text,
            stop_reason=str(response.stop_reason),
            artifacts=artifacts,
        )

    async def run(
        self,
        prompt: str,
        *,
        workspace_key: str,
        agent_name: str | None = None,
        media: tuple[AcpInputMedia, ...] = (),
        progress_reporter: ProgressReporter | None = None,
    ) -> AcpRunResult:
        name, config = self._resolve_config(agent_name)
        scope_id = self._scope_id(workspace_key)
        async with self._registry_lock:
            self._active_scopes[scope_id] = self._active_scopes.get(scope_id, 0) + 1
        try:
            return await self._run_in_scope(
                prompt,
                name=name,
                config=config,
                scope_id=scope_id,
                media=media,
                progress_reporter=progress_reporter,
            )
        finally:
            async with self._registry_lock:
                remaining = self._active_scopes.get(scope_id, 1) - 1
                if remaining > 0:
                    self._active_scopes[scope_id] = remaining
                else:
                    self._active_scopes.pop(scope_id, None)

    async def cancel(self, *, workspace_key: str, agent_name: str | None = None) -> int:
        scope_id = self._scope_id(workspace_key)
        names = [agent_name] if agent_name else None
        async with self._registry_lock:
            runtimes = [
                runtime
                for (name, runtime_scope), runtime in self._runtimes.items()
                if runtime_scope == scope_id and (names is None or name in names) and runtime.client.active
            ]
        for runtime in runtimes:
            with contextlib.suppress(Exception):
                await runtime.connection.cancel(session_id=runtime.session_id)
        return len(runtimes)

    async def reset(self, *, workspace_key: str, agent_name: str | None = None) -> int:
        scope_id = self._scope_id(workspace_key)
        async with self._registry_lock:
            keys = [
                key
                for key in self._runtimes
                if key[1] == scope_id and (agent_name is None or key[0] == agent_name)
            ]
            runtimes = [self._runtimes.pop(key) for key in keys]
        if runtimes:
            await asyncio.gather(*(self._close_runtime(runtime) for runtime in runtimes), return_exceptions=True)
        return len(runtimes)

    @staticmethod
    def _delete_inactive_workspaces(root: Path, protected_scopes: set[str]) -> int:
        workspaces = root / "workspaces"
        if not workspaces.is_dir():
            return 0
        removed = 0
        for path in workspaces.iterdir():
            if path.name in protected_scopes:
                continue
            try:
                if path.is_symlink() or path.is_file():
                    path.unlink(missing_ok=True)
                else:
                    shutil.rmtree(path)
                removed += 1
            except OSError as exc:
                logger.warning("清理 ACP workspace 失败 %s: %s", path, exc)
        return removed

    async def cleanup_cache(self) -> int:
        """Close inactive ACP processes and delete their isolated workspaces."""
        async with self._registry_lock:
            protected_scopes = set(self._active_scopes)
            stale = [
                self._runtimes.pop(key)
                for key in list(self._runtimes)
                if key[1] not in protected_scopes
            ]
            if stale:
                await asyncio.gather(*(self._close_runtime(runtime) for runtime in stale), return_exceptions=True)
            return await asyncio.to_thread(
                self._delete_inactive_workspaces,
                self._root(),
                protected_scopes,
            )

    async def close(self) -> None:
        async with self._registry_lock:
            runtimes = list(self._runtimes.values())
            self._runtimes.clear()
        if runtimes:
            await asyncio.gather(*(self._close_runtime(runtime) for runtime in runtimes), return_exceptions=True)


acp_service = AcpAgentService()
