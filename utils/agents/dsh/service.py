"""Lifecycle and async bridge for the synchronous DeepSeek Harness SDK."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nonebot import logger

from utils.agents.progress import ProgressEvent, ProgressReporter, emit_progress
from utils.configs import EnvConfig, get_provider_profile

DSH_RUNTIME_PROVIDER = "deepseek-official"
DSH_SYSTEM_PROMPT = (
    "You are an experimental coding agent running in a dedicated Frontier workspace. "
    "Work only inside the current working directory. Never inspect parent directories, "
    "absolute paths outside the workspace, process metadata, credentials, or unrelated host files. "
    "Use the available tools to complete the user's task and report the result concisely."
)


class DshUnavailableError(RuntimeError):
    """The optional SDK or its platform runtime is unavailable."""


class DshConfigurationError(RuntimeError):
    """The experimental agent configuration cannot launch a runtime."""


@dataclass(frozen=True, slots=True)
class _LaunchSettings:
    model: str
    source_provider: str
    max_tokens: int
    base_url: str | None
    api_key: str
    timeout_seconds: float

    @property
    def fingerprint(self) -> tuple[str, str, int, str | None, str, float]:
        return (
            self.model,
            self.source_provider,
            self.max_tokens,
            self.base_url,
            self.api_key,
            self.timeout_seconds,
        )


@dataclass(slots=True)
class _WorkspaceRuntime:
    harness: Any
    fingerprint: tuple[str, str, int, str | None, str, float]
    session_namespace: str = field(default_factory=lambda: uuid.uuid4().hex)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


HarnessFactory = Callable[..., Any]


def _default_harness_factory(**kwargs: Any) -> Any:
    try:
        from deepseek_harness import DeepSeekHarness
    except ImportError as exc:
        raise DshUnavailableError(
            "未安装 deepseek-harness-sdk；请使用 `uv sync --extra dsh` 安装实验依赖"
        ) from exc
    try:
        return DeepSeekHarness(**kwargs)
    except (ImportError, FileNotFoundError) as exc:
        raise DshUnavailableError(f"当前平台缺少可用的 DeepSeek Harness runtime: {exc}") from exc


def _notification_parts(notification: Any) -> tuple[str, dict[str, Any]]:
    method = getattr(notification, "method", "")
    payload = getattr(notification, "payload", {})
    if isinstance(notification, dict):
        method = notification.get("method", method)
        payload = notification.get("payload", notification.get("params", payload))
    return str(method or ""), payload if isinstance(payload, dict) else {}


def notification_to_progress(notification: Any) -> ProgressEvent | None:
    """Translate stable DSH notification/event names into Frontier progress events."""
    method, payload = _notification_parts(notification)
    if method == "subagent.started":
        child = str(payload.get("childSessionId") or "subagent")
        return ProgressEvent(type="subagent_start", message=f"DSH 子代理 {child} 已启动", detail=payload)
    if method == "subagent.finished":
        child = str(payload.get("childSessionId") or "subagent")
        status = str(payload.get("status") or payload.get("stopReason") or "completed")
        return ProgressEvent(
            type="subagent_done",
            message=f"DSH 子代理 {child} {'已完成' if status in {'ok', 'completed'} else '已结束'}",
            detail=payload,
        )
    if method != "session.event":
        return None

    event = payload.get("event")
    if not isinstance(event, dict):
        return None
    event_type = event.get("type")
    data = event.get("data")
    data = data if isinstance(data, dict) else {}
    if event_type == "turn/start":
        return ProgressEvent(type="thinking", message="DSH 正在思考…", detail=data)
    if event_type == "tool/call":
        name = str(data.get("name") or "tool")
        return ProgressEvent(type="tool_call", message=f"DSH 正在调用 {name}", detail={"tool_name": name, **data})
    if event_type == "tool/result":
        name = str(data.get("name") or data.get("callId") or "tool")
        failed = bool(data.get("isError"))
        return ProgressEvent(
            type="tool_result",
            message=f"DSH {name} {'执行失败' if failed else '已完成'}",
            detail={"tool_name": name, "success": not failed, **data},
        )
    return None


class DshAgentService:
    """Own one lazily started DSH runtime per isolated Frontier workspace."""

    def __init__(
        self,
        *,
        root_dir: str | Path | None = None,
        harness_factory: HarnessFactory | None = None,
        cordis_path: str | Path | None = None,
    ) -> None:
        self._root_dir = Path(root_dir).resolve() if root_dir is not None else None
        self._harness_factory = harness_factory or _default_harness_factory
        self._cordis_path = Path(cordis_path).resolve() if cordis_path is not None else Path(__file__).with_name("cordis.yml")
        self._runtimes: dict[str, _WorkspaceRuntime] = {}
        self._active_scopes: dict[str, int] = {}
        self._registry_lock = asyncio.Lock()

    @staticmethod
    def _scope_id(workspace_key: str) -> str:
        return hashlib.sha256(workspace_key.encode("utf-8")).hexdigest()[:24]

    def _root(self) -> Path:
        return self._root_dir or (Path.cwd() / "cache" / "dsh")

    @staticmethod
    def _settings() -> _LaunchSettings:
        source_provider = str(EnvConfig.DSH_MODEL_PROVIDER).strip()
        model = str(EnvConfig.DSH_MODEL).strip()
        if not source_provider:
            raise DshConfigurationError("dsh.provider 不能为空")
        if not model:
            raise DshConfigurationError("dsh.model 不能为空")
        try:
            profile = get_provider_profile(source_provider)
        except ValueError as exc:
            raise DshConfigurationError(str(exc)) from exc
        api_key = str(profile.get("api_key") or "").strip()
        if not api_key:
            raise DshConfigurationError(f"providers.{source_provider}.api_key 未配置")
        base_url = str(profile.get("base_url") or "").strip() or None
        return _LaunchSettings(
            model=model,
            source_provider=source_provider,
            max_tokens=int(EnvConfig.DSH_MAX_TOKENS),
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=float(EnvConfig.AGENT_JOB_TIMEOUT_SECONDS),
        )

    def _new_harness(self, scope_id: str, settings: _LaunchSettings) -> Any:
        workspace = self._root() / "workspaces" / scope_id
        sessions = self._root() / "sessions" / scope_id
        workspace.mkdir(parents=True, exist_ok=True)
        sessions.mkdir(parents=True, exist_ok=True)
        return self._harness_factory(
            provider=DSH_RUNTIME_PROVIDER,
            model=settings.model,
            max_tokens=settings.max_tokens,
            cwd=str(workspace),
            session_root=str(sessions),
            cordis=str(self._cordis_path),
            base_url=settings.base_url,
            api_key=settings.api_key,
            request_timeout_seconds=settings.timeout_seconds,
            env={"DSH_SYSTEM_PROMPT": DSH_SYSTEM_PROMPT, "DSH_MODEL": settings.model},
        )

    async def _runtime(self, workspace_key: str, settings: _LaunchSettings) -> _WorkspaceRuntime:
        scope_id = self._scope_id(workspace_key)
        while True:
            stale: _WorkspaceRuntime | None = None
            async with self._registry_lock:
                runtime = self._runtimes.get(scope_id)
                if runtime is not None and runtime.fingerprint == settings.fingerprint:
                    return runtime
                if runtime is not None:
                    stale = self._runtimes.pop(scope_id)
                else:
                    runtime = _WorkspaceRuntime(
                        harness=self._new_harness(scope_id, settings),
                        fingerprint=settings.fingerprint,
                    )
                    self._runtimes[scope_id] = runtime
                    return runtime
            if stale is not None:
                async with stale.lock:
                    await asyncio.to_thread(stale.harness.close)

    async def run(
        self,
        prompt: str,
        *,
        workspace_key: str,
        session_id: str,
        progress_reporter: ProgressReporter | None = None,
    ) -> Any:
        scope_id = self._scope_id(workspace_key)
        async with self._registry_lock:
            self._active_scopes[scope_id] = self._active_scopes.get(scope_id, 0) + 1

        try:
            settings = self._settings()
            runtime = await self._runtime(workspace_key, settings)
            return await self._run_runtime(
                runtime,
                prompt,
                session_id=session_id,
                settings=settings,
                progress_reporter=progress_reporter,
                scope_id=scope_id,
            )
        finally:
            async with self._registry_lock:
                remaining = self._active_scopes.get(scope_id, 1) - 1
                if remaining > 0:
                    self._active_scopes[scope_id] = remaining
                else:
                    self._active_scopes.pop(scope_id, None)

    async def _run_runtime(
        self,
        runtime: _WorkspaceRuntime,
        prompt: str,
        *,
        session_id: str,
        settings: _LaunchSettings,
        progress_reporter: ProgressReporter | None,
        scope_id: str,
    ) -> Any:
        loop = asyncio.get_running_loop()
        progress_futures: list[Any] = []
        runtime_session_id = f"{session_id}-{runtime.session_namespace}"

        def on_notification(notification: Any) -> None:
            event = notification_to_progress(notification)
            if event is not None:
                progress_futures.append(asyncio.run_coroutine_threadsafe(emit_progress(progress_reporter, event), loop))

        discard_runtime = False
        try:
            async with runtime.lock:
                run_task = asyncio.create_task(
                    asyncio.to_thread(
                        runtime.harness.run,
                        prompt,
                        session_id=runtime_session_id,
                        on_notification=on_notification,
                    )
                )
                done, _pending = await asyncio.wait({run_task}, timeout=settings.timeout_seconds)
                if not done:
                    logger.warning("DSH 执行超时，正在关闭 workspace runtime")
                    discard_runtime = True
                    await asyncio.to_thread(runtime.harness.close)
                    run_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await run_task
                    raise TimeoutError(f"DSH 执行超过 {settings.timeout_seconds:g} 秒")
                try:
                    return run_task.result()
                except (ImportError, FileNotFoundError) as exc:
                    discard_runtime = True
                    await asyncio.to_thread(runtime.harness.close)
                    raise DshUnavailableError(f"当前平台缺少可用的 DeepSeek Harness runtime: {exc}") from exc
                except Exception:
                    discard_runtime = True
                    await asyncio.to_thread(runtime.harness.close)
                    raise
                finally:
                    if progress_futures:
                        await asyncio.gather(
                            *(asyncio.wrap_future(future) for future in progress_futures),
                            return_exceptions=True,
                        )
        finally:
            if discard_runtime:
                async with self._registry_lock:
                    if self._runtimes.get(scope_id) is runtime:
                        self._runtimes.pop(scope_id)

    @staticmethod
    def _delete_inactive_cache(root: Path, protected_scopes: set[str]) -> int:
        removed_scopes: set[str] = set()
        for bucket_name in ("workspaces", "sessions"):
            bucket = root / bucket_name
            if not bucket.is_dir():
                continue
            for path in bucket.iterdir():
                if path.name in protected_scopes:
                    continue
                try:
                    if path.is_symlink() or path.is_file():
                        path.unlink(missing_ok=True)
                    else:
                        shutil.rmtree(path)
                    removed_scopes.add(path.name)
                except OSError as exc:
                    logger.warning("清理 DSH 缓存失败 %s: %s", path, exc)
        return len(removed_scopes)

    async def cleanup_cache(self) -> int:
        """Delete inactive DSH workspaces and sessions without racing new runs."""
        async with self._registry_lock:
            protected_scopes = set(self._active_scopes)
            stale_runtimes: list[_WorkspaceRuntime] = []
            for scope_id, runtime in list(self._runtimes.items()):
                if scope_id in protected_scopes:
                    continue
                self._runtimes.pop(scope_id, None)
                stale_runtimes.append(runtime)
            if stale_runtimes:
                await asyncio.gather(
                    *(asyncio.to_thread(runtime.harness.close) for runtime in stale_runtimes),
                    return_exceptions=True,
                )
            return await asyncio.to_thread(self._delete_inactive_cache, self._root(), protected_scopes)

    async def close(self) -> None:
        async with self._registry_lock:
            runtimes = list(self._runtimes.values())
            self._runtimes.clear()
        if runtimes:
            # close() intentionally does not wait for a workspace lock: SDK close
            # tears down the subprocess and unblocks an in-flight synchronous run.
            await asyncio.gather(
                *(asyncio.to_thread(runtime.harness.close) for runtime in runtimes),
                return_exceptions=True,
            )


dsh_service = DshAgentService()
