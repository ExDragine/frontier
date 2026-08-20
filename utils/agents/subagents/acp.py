"""Deep Agents wrappers for explicitly configured ACP agents."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from deepagents import CompiledSubAgent
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from nonebot import logger

from utils.media import extension_for_mime
from utils.message import extract_message_text

from ..acp.service import (
    AcpAgentService,
    AcpConfigurationError,
    AcpRunResult,
    acp_service,
)

_RESERVED_SUBAGENT_NAMES = {"general-purpose", "memory-agent", "research-agent", "document-agent"}


def _delegated_prompt(state: Any) -> str:
    messages = state.get("messages", []) if isinstance(state, dict) else []
    for message in reversed(messages):
        text = extract_message_text(message).strip()
        if text:
            return text
    raise ValueError("ACP 子代理没有收到可执行的文本任务")


def _persist_artifacts(
    result: AcpRunResult,
    *,
    workspace_dir: str | None,
    agent_name: str,
) -> tuple[str, ...]:
    if not result.artifacts or not workspace_dir:
        return ()
    relative_root = Path("acp-artifacts") / agent_name / uuid.uuid4().hex
    output_root = Path(workspace_dir).resolve() / relative_root
    output_root.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for index, artifact in enumerate(result.artifacts, start=1):
        suffix = extension_for_mime(artifact.mime_type)
        relative_path = relative_root / f"{artifact.kind}-{index}{suffix}"
        (Path(workspace_dir).resolve() / relative_path).write_bytes(artifact.data)
        paths.append(f"/{relative_path.as_posix()}")
    return tuple(paths)


def _subagent_name(agent_name: str) -> str:
    name = f"acp-{agent_name}"
    if name in _RESERVED_SUBAGENT_NAMES:
        raise AcpConfigurationError(f"ACP 子代理名称 {name!r} 与内置子代理冲突")
    return name


def build_acp_subagents(
    service: AcpAgentService | None = None,
) -> list[CompiledSubAgent]:
    """Build opt-in ACP-backed subagents without making acp.json mandatory."""
    service = service or acp_service
    try:
        configured = service.subagent_configs()
    except AcpConfigurationError as exc:
        if "acp.json 不存在" not in str(exc):
            logger.warning("ACP 子代理配置无效，已跳过: %s", exc)
        return []

    subagents: list[CompiledSubAgent] = []
    for agent_name, agent_config in configured:
        subagent_name = _subagent_name(agent_name)

        async def invoke(
            state: dict[str, Any],
            config: RunnableConfig,
            *,
            _agent_name: str = agent_name,
        ) -> dict[str, list[AIMessage]]:
            configurable = config.get("configurable", {})
            thread_id = str(configurable.get("thread_id") or "anonymous")
            workspace_dir = configurable.get("workspace_dir")
            result = await service.run(
                _delegated_prompt(state),
                workspace_key=f"deepagent:{thread_id}:{_agent_name}",
                agent_name=_agent_name,
            )
            artifact_paths = await asyncio.to_thread(
                _persist_artifacts,
                result,
                workspace_dir=str(workspace_dir) if workspace_dir else None,
                agent_name=_agent_name,
            )
            text = result.final_response.strip()
            if artifact_paths:
                files = "\n".join(f"- {path}" for path in artifact_paths)
                text = f"{text}\n\nACP 子代理生成的媒体工件：\n{files}".strip()
            if not text:
                text = f"ACP 子代理 {_agent_name} 已结束，但没有返回文本。"
            return {"messages": [AIMessage(content=text)]}

        subagents.append(
            CompiledSubAgent(
                name=subagent_name,
                description=agent_config.description
                or f"通过 Agent Client Protocol 委托给外部 Agent {agent_name}。",
                runnable=RunnableLambda(invoke, name=subagent_name),
            )
        )
    return subagents


__all__ = ["build_acp_subagents"]
