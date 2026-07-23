"""Main Frontier Deep Agent composition and execution."""

import asyncio
import os
import time
import uuid
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.graph import DeepAgentState
from langchain.agents.middleware import (
    FilesystemFileSearchMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    ToolRetryMiddleware,
)
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_quickjs import CodeInterpreterMiddleware
from nonebot import logger

from tools import agent_tools
from utils.agent_context import FrontierRuntimeContext
from utils.configs import EnvConfig
from utils.harness_profiles import register_frontier_harness_profiles
from utils.llm_factory import create_llm, provider_uses_responses_api

from .capture import detect_browser_capture_intent
from .inputs import filter_messages_for_model_capabilities
from .progress import (
    ProgressEvent,
    ProgressReporter,
    collect_progress,
    emit_progress,
    finish_progress_collection,
)
from .prompts import load_system_prompt as compose_system_prompt
from .runtime import agent_thread_id
from .subagents import build_earth_data_subagent, build_memory_subagent
from .workspace import SKILLS_BACKEND_PATH, build_agent_backend

register_frontier_harness_profiles()


class FrontierAgentState(DeepAgentState):
    """Mutable graph state; identity fields remain as a compatibility bridge for tools."""

    user_id: str
    group_id: int | None
    image_inputs: list[bytes]
    video_inputs: list[bytes]


class FrontierCognitive:
    def __init__(self):
        self.tools = agent_tools.main_tools
        self.memory_subagent = build_memory_subagent(agent_tools.subagent_tools["memory"])
        self.earth_data_subagent = build_earth_data_subagent(agent_tools.earth_query_tools)

    @staticmethod
    def load_system_prompt(
        group_id: int | None = None,
        wake_word: str | None = None,
        workspace_key: str | None = None,
    ) -> str:
        return compose_system_prompt(group_id, wake_word, workspace_key)

    @staticmethod
    async def extract_uni_messages(response):
        """直接从响应中提取 UniMessage 对象。"""
        if not response or not isinstance(response, dict):
            logger.warning("⚠️ extract_uni_messages: response 为空或不是字典类型")
            return []

        uni_messages = []
        for message in response.get("messages", []):
            if getattr(message, "type", None) == "tool" and getattr(message, "artifact", None) is not None:
                tool_name = getattr(message, "name", "unknown")
                uni_messages.append(message.artifact)
                logger.info(f"📤 提取 UniMessage: {tool_name} - 类型: {type(message.artifact)}")

        logger.info(f"📨 总共提取到 {len(uni_messages)} 个 UniMessage")
        return uni_messages

    async def chat_agent(
        self,
        messages,
        user_id,
        user_name,
        capability: str = "none",
        group_id: int | None = None,
        image_inputs: list[bytes] | None = None,
        video_inputs: list[bytes] | None = None,
        thread_id_override: uuid.UUID | str | None = None,
        wake_word: str | None = None,
        group_member_role: str | None = None,
        progress_reporter: ProgressReporter | None = None,
        user_text: str | None = None,
    ):
        uses_responses_api = provider_uses_responses_api(
            EnvConfig.ADVAN_MODEL,
            EnvConfig.ADVAN_MODEL_PROVIDER,
        )
        model_kwargs: dict = {
            "model": EnvConfig.ADVAN_MODEL,
            "streaming": False,
            "max_retries": 2,
            "timeout": EnvConfig.AGENT_LLM_TIMEOUT_SECONDS,
            "provider": EnvConfig.ADVAN_MODEL_PROVIDER,
        }
        if uses_responses_api:
            model_kwargs["reasoning_effort"] = capability
            model_kwargs["verbosity"] = "low"
        model = create_llm(**model_kwargs)
        messages = filter_messages_for_model_capabilities(
            messages,
            EnvConfig.ADVAN_MODEL,
            role="advanced",
        )
        working_dir = getattr(self, "working_dir", os.path.join(os.getcwd(), "cache", "sandbox"))
        thread_id = thread_id_override or agent_thread_id(user_id, group_id)
        if not isinstance(thread_id, uuid.UUID):
            thread_id = uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=str(thread_id))
        workspace_key = str(group_id) if group_id is not None else str(user_id)
        backend = build_agent_backend(working_dir, workspace_key)
        workspace_dir = os.path.join(working_dir, "workspaces", workspace_key)
        system_prompt = self.load_system_prompt(group_id, wake_word, workspace_key)

        effective_tools = list(self.tools)
        allowed_capture_tools = await detect_browser_capture_intent(user_text)
        if allowed_capture_tools:
            for restricted_tool in agent_tools.restricted_tools:
                if restricted_tool.name in allowed_capture_tools:
                    effective_tools.append(restricted_tool)
                    logger.info(f"用户明确请求浏览器捕获工具，已暴露: {restricted_tool.name}")
        else:
            logger.debug("用户未请求截图/录屏，restricted 工具未暴露")

        for restricted_tool in agent_tools.restricted_tools:
            if restricted_tool.name in ("ens_normal", "ens_professional"):
                effective_tools.append(restricted_tool)

        ptc_tool_names = [tool.name for tool in effective_tools] if effective_tools else []
        memory_subagent = getattr(self, "memory_subagent", None) or build_memory_subagent(
            agent_tools.subagent_tools["memory"]
        )
        earth_data_subagent = getattr(self, "earth_data_subagent", None) or build_earth_data_subagent(
            agent_tools.earth_query_tools
        )
        middleware = [
            PIIMiddleware(
                "api_key",
                detector=r"sk-[a-zA-Z0-9]{32}",
                strategy="mask",
            ),
            ToolRetryMiddleware(),
            ModelRetryMiddleware(),
            FilesystemFileSearchMiddleware(root_path=workspace_dir),
            CodeInterpreterMiddleware(ptc=ptc_tool_names),
        ]
        agent = create_deep_agent(
            name=EnvConfig.BOT_NAME,
            model=model,
            system_prompt=system_prompt,
            tools=effective_tools,
            subagents=[memory_subagent, earth_data_subagent],
            middleware=middleware,
            skills=[SKILLS_BACKEND_PATH],
            memory=[f"/memory/{workspace_key}/SOUL.md"],
            permissions=[
                FilesystemPermission(
                    operations=["write"],
                    paths=[SKILLS_BACKEND_PATH, f"{SKILLS_BACKEND_PATH}/**"],
                    mode="deny",
                )
            ],
            backend=backend,
            state_schema=FrontierAgentState,
            context_schema=FrontierRuntimeContext,
            debug=EnvConfig.AGENT_DEBUG_MODE,
        )
        start_time = time.time()
        logger.info(f"Agent烧烤中~🍖 思考等级: {capability} 用户: {user_name} (ID: {user_id})")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "group_id": group_id,
                "group_member_role": group_member_role,
                "workspace_dir": workspace_dir,
            }
        }
        runtime_context = FrontierRuntimeContext(
            user_id=str(user_id),
            group_id=group_id,
            group_member_role=group_member_role,
            workspace_dir=workspace_dir,
        )
        try:
            input_data: Any = {
                "messages": messages,
                "user_id": user_id,
                "group_id": group_id,
                "image_inputs": image_inputs or [],
                "video_inputs": video_inputs or [],
            }
            stream = await agent.astream_events(
                input_data,
                config=config,
                context=runtime_context,
                version="v3",
            )
            progress_task = asyncio.create_task(collect_progress(stream, progress_reporter))
            try:
                response = await stream.output()
            finally:
                await finish_progress_collection(progress_task)
        except Exception as exc:
            logger.error(f"❌ Agent执行出现意外错误 用户{user_id}: {type(exc).__name__}")
            logger.exception("完整错误堆栈:")
            await emit_progress(
                progress_reporter,
                ProgressEvent(type="done", message="Agent 执行失败", detail={"success": False}),
            )
            return {
                "response": {"messages": [AIMessage("💥 服务暂时不可用，请稍后重试。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
                "error": str(exc),
            }

        uni_messages = await FrontierCognitive.extract_uni_messages(response)
        ai_messages = [message for message in response.get("messages", []) if getattr(message, "type", None) == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")

        processing_time = time.time() - start_time
        logger.info(f"Agent烤熟了~🥓 (耗时: {processing_time:.2f}s)")
        await emit_progress(
            progress_reporter,
            ProgressEvent(type="done", message="Agent 已完成", detail={"success": True}),
        )

        return {
            "response": {"messages": [final_response]},
            "total_time": processing_time,
            "uni_messages": uni_messages,
        }
