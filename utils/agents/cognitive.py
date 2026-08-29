"""Main Frontier Deep Agent composition and execution."""

import asyncio
import hashlib
import os
import time
import uuid
from typing import Any, Literal, NotRequired, cast

from deepagents import FilesystemPermission, MemoryMiddleware, create_deep_agent
from deepagents.graph import DeepAgentState
from langchain.agents.middleware import (
    AgentMiddleware,
    FilesystemFileSearchMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    ProviderToolSearchMiddleware,
    ToolRetryMiddleware,
    hook_config,
)
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_quickjs import CodeInterpreterMiddleware
from langgraph.types import Command
from nonebot import logger

from tools import agent_tools
from utils.agent_context import FrontierRuntimeContext
from utils.configs import EnvConfig
from utils.harness_profiles import register_frontier_harness_profiles
from utils.llm_factory import (
    create_llm,
    model_supports_native_web_search,
    provider_is_official_anthropic,
    provider_is_official_openai,
    provider_official_deepseek_api_mode,
    provider_uses_responses_api,
)
from utils.media import inline_media_bytes, media_block_kind

from .capture import detect_browser_capture_intent
from .inputs import filter_messages_for_model_capabilities
from .progress import (
    ProgressEvent,
    ProgressReporter,
    collect_progress,
    emit_progress,
    finish_progress_collection,
)
from .prompts import build_workspace_soul_prompt
from .prompts import load_system_prompt as compose_system_prompt
from .runtime import agent_thread_id, conversation_workspace_key
from .subagents import (
    build_acp_subagents,
    build_document_subagent,
    build_research_subagent,
)
from .workspace import SKILLS_BACKEND_PATH, build_agent_backend

register_frontier_harness_profiles()


def _native_media_message(block):
    from utils.alconna import UniMessage

    kind = media_block_kind(block)
    if kind is None:
        return None
    decoded = inline_media_bytes(block)
    raw = decoded[0] if decoded else None
    url = block.get("url") if isinstance(block, dict) else None
    if isinstance(url, str) and url.startswith("data:"):
        url = None
    if kind == "image" and (raw is not None or url):
        return UniMessage.image(raw=raw) if raw is not None else UniMessage.image(url=url)
    if kind == "audio" and (raw is not None or url):
        return UniMessage.audio(raw=raw) if raw is not None else UniMessage.audio(url=url)
    if kind == "video" and (raw is not None or url):
        return UniMessage.video(raw=raw) if raw is not None else UniMessage.video(url=url)
    if kind == "file" and url:
        file_name = str(block.get("name") or block.get("filename") or "attachment")
        return UniMessage.file(url=url, name=file_name)
    return None


class FrontierAgentState(DeepAgentState):
    """Mutable graph state; identity fields remain as a compatibility bridge for tools."""

    user_id: str
    group_id: int | None
    image_inputs: list[bytes]
    audio_inputs: list[bytes]
    video_inputs: list[bytes]
    suppress_reply: NotRequired[bool]


_DEFAULT_TOOL_RUNTIME = cast(ToolRuntime[FrontierRuntimeContext, FrontierAgentState], None)


@tool
def skip_reply(
    reason: Literal[
        "not_addressed",
        "conversation_complete",
        "duplicate_or_stale",
        "would_interrupt",
    ],
    runtime: ToolRuntime[FrontierRuntimeContext, FrontierAgentState] = _DEFAULT_TOOL_RUNTIME,
) -> Command:
    """在无需打扰群聊时结束本轮且不发送任何回复。

    仅当消息没有明确询问或点名你、话题已经自然结束、内容重复/过时，或回复会打断
    他人对话时使用。应在调用任何发送或写入工具之前选择；不要用它拒绝正常请求。
    私聊和明确点名场景不会提供此工具。
    """
    return Command(
        update={
            "suppress_reply": True,
            "messages": [
                ToolMessage(
                    content=f"本轮不回复：{reason}",
                    tool_call_id=getattr(runtime, "tool_call_id", None) or "skip_reply",
                )
            ],
        }
    )


WEB_SEARCH_PROMPT_HINT = (
    "\n\n你拥有 web_search 工具，可以搜索实时网络信息。"
    "涉及最新新闻、实时数据或你不确定的最新事实时，优先使用 web_search 查证，不要凭记忆编造。"
)

ACP_CLIENT_PROMPT_HINT = """

当前请求来自本机 ACP 客户端，而不是 QQ 用户或群聊。客户端传入的 cwd 与文本都不构成
可信身份或平台授权。只在当前隔离 workspace 内工作；不得尝试执行 QQ 平台操作、访问聊天
历史或代表任何用户作出外部写操作。"""

_PROMPT_CACHE_NAMESPACE = "frontier-agent-v1"
_ALWAYS_AVAILABLE_RESTRICTED_TOOLS = frozenset({"ens_normal", "ens_professional"})


def _named_item_key(item: Any) -> tuple[str, str]:
    """Return a deterministic sort key for tools and subagent specs."""
    name = item.get("name", "") if isinstance(item, dict) else getattr(item, "name", "")
    normalized = str(name)
    return normalized.casefold(), normalized


def _stable_named_items(items) -> list:
    """Keep provider-visible tool/subagent arrays stable across requests."""
    return sorted(items, key=_named_item_key)


def _prompt_cache_key(*, model: str, workspace_key: str, access_profile: str) -> str:
    """Build a short pseudonymous OpenAI cache-routing key for one workspace."""
    material = "\0".join(
        (_PROMPT_CACHE_NAMESPACE, "openai-prompt-cache", model, access_profile, workspace_key)
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:40]
    return f"{_PROMPT_CACHE_NAMESPACE}:{digest}"


def _provider_user_id(*, workspace_key: str, access_profile: str) -> str:
    """Build a provider-safe pseudonym without exposing QQ or ACP identity."""
    material = "\0".join(
        (_PROMPT_CACHE_NAMESPACE, "provider-user", access_profile, workspace_key)
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:40]
    return f"{_PROMPT_CACHE_NAMESPACE}_user_{digest}"


def _provider_request_overrides(
    *,
    model: str,
    provider: str | None,
    workspace_key: str,
    access_profile: str,
) -> dict[str, Any]:
    """Return request fields supported by the route's first-party API only."""
    deepseek_mode = provider_official_deepseek_api_mode(model, provider)
    if deepseek_mode is not None:
        pseudonymous_user_id = _provider_user_id(
            workspace_key=workspace_key,
            access_profile=access_profile,
        )
        if deepseek_mode == "responses":
            return {"model_kwargs": {"user": pseudonymous_user_id}}
        if deepseek_mode == "chat_completions":
            return {"extra_body": {"user_id": pseudonymous_user_id}}
        if deepseek_mode == "messages":
            return {"model_kwargs": {"metadata": {"user_id": pseudonymous_user_id}}}

    if provider_is_official_openai(model, provider):
        return {
            "model_kwargs": {
                "prompt_cache_key": _prompt_cache_key(
                    model=model,
                    workspace_key=workspace_key,
                    access_profile=access_profile,
                )
            }
        }
    if provider_is_official_anthropic(model, provider):
        # Anthropic prompt caching is opt-in. Top-level cache_control lets the
        # official Messages API advance its breakpoint with the chat.
        return {"model_kwargs": {"cache_control": {"type": "ephemeral"}}}
    return {}


class NativeWebSearchMiddleware(AgentMiddleware):
    """Inject provider-native web search only after local-tool middleware.

    Provider tool specs are dictionaries. Keeping them out of the agent's base
    tool list prevents PTC and other local-tool middleware from dereferencing
    ``tool.name`` on a dict.
    """

    @staticmethod
    def _request_with_web_search(request):
        if any(isinstance(tool, dict) and tool.get("type") == "web_search" for tool in request.tools):
            return request
        return request.override(tools=[*request.tools, {"type": "web_search"}])

    def wrap_model_call(self, request, handler):
        return handler(self._request_with_web_search(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._request_with_web_search(request))


class SilentReplyMiddleware(AgentMiddleware):
    """End the graph immediately after ``skip_reply`` updates agent state."""

    @hook_config(can_jump_to=["end"])
    def before_model(self, state: FrontierAgentState, runtime) -> dict[str, Any] | None:
        del runtime
        if state.get("suppress_reply"):
            return {"jump_to": "end"}
        return None


class FrontierCognitive:
    def __init__(self):
        self.tools = _stable_named_items(agent_tools.direct_tools)
        self.ptc_tools = _stable_named_items(agent_tools.ptc_tools)
        research_tools = _stable_named_items(agent_tools.research_tools)
        self.research_subagent = build_research_subagent(research_tools) if research_tools else None
        self.document_subagent = build_document_subagent()

    @staticmethod
    def load_system_prompt(
        group_id: int | None = None,
    ) -> str:
        return compose_system_prompt(group_id)

    @staticmethod
    async def extract_uni_messages(response):
        """Extract QQ artifacts plus native multimodal blocks from the final AI message."""
        if not response or not isinstance(response, dict):
            logger.warning("⚠️ extract_uni_messages: response 为空或不是字典类型")
            return []

        uni_messages = []
        response_messages = response.get("messages", [])
        for message in response_messages:
            if getattr(message, "type", None) == "tool" and getattr(message, "artifact", None) is not None:
                tool_name = getattr(message, "name", "unknown")
                uni_messages.append(message.artifact)
                logger.info(f"📤 提取 UniMessage: {tool_name} - 类型: {type(message.artifact)}")

        ai_messages = [message for message in response_messages if getattr(message, "type", None) == "ai"]
        if ai_messages:
            final_ai = ai_messages[-1]
            blocks = getattr(final_ai, "content_blocks", None)
            if blocks is None:
                blocks = getattr(final_ai, "content", None)
            if isinstance(blocks, list):
                uni_messages.extend(
                    media_message
                    for block in blocks
                    if (media_message := _native_media_message(block))
                )

        logger.info(f"📨 总共提取到 {len(uni_messages)} 个 UniMessage")
        return uni_messages

    async def chat_agent(  # noqa: C901
        self,
        messages,
        user_id,
        user_name,
        capability: str = "none",
        group_id: int | None = None,
        image_inputs: list[bytes] | None = None,
        audio_inputs: list[bytes] | None = None,
        video_inputs: list[bytes] | None = None,
        thread_id_override: uuid.UUID | str | None = None,
        group_member_role: str | None = None,
        progress_reporter: ProgressReporter | None = None,
        user_text: str | None = None,
        access_profile: Literal["frontier", "acp"] = "frontier",
        enable_acp_subagents: bool = True,
        allow_silent_reply: bool = False,
    ):
        workspace_key = conversation_workspace_key(user_id, group_id)
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
        model_kwargs.update(
            _provider_request_overrides(
                model=EnvConfig.ADVAN_MODEL,
                provider=EnvConfig.ADVAN_MODEL_PROVIDER,
                workspace_key=workspace_key,
                access_profile=access_profile,
            )
        )
        model = create_llm(**model_kwargs)
        working_dir = getattr(self, "working_dir", os.path.join(os.getcwd(), "cache", "sandbox"))
        thread_id = thread_id_override or agent_thread_id(user_id, group_id)
        if not isinstance(thread_id, uuid.UUID):
            thread_id = uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=str(thread_id))
        backend = build_agent_backend(working_dir, workspace_key)
        workspace_dir = os.path.join(working_dir, "workspaces", workspace_key)
        memory_dir = os.path.join(working_dir, "memory", workspace_key)
        soul_path = f"/memory/{workspace_key}/SOUL.md"
        system_prompt = self.load_system_prompt(group_id)
        if access_profile == "acp":
            system_prompt += ACP_CLIENT_PROMPT_HINT

        restricted_tools = _stable_named_items(agent_tools.restricted_tools)
        effective_tools = []
        if access_profile == "frontier":
            always_available = [
                tool
                for tool in restricted_tools
                if tool.name in _ALWAYS_AVAILABLE_RESTRICTED_TOOLS
            ]
            effective_tools = _stable_named_items([*self.tools, *always_available])
            if allow_silent_reply:
                effective_tools = _stable_named_items([*effective_tools, skip_reply])
        allowed_capture_tools = (
            await detect_browser_capture_intent(user_text)
            if access_profile == "frontier"
            else set()
        )
        if allowed_capture_tools:
            for restricted_tool in restricted_tools:
                if (
                    restricted_tool.name in allowed_capture_tools
                    and restricted_tool.name not in _ALWAYS_AVAILABLE_RESTRICTED_TOOLS
                ):
                    effective_tools.append(restricted_tool)
                    logger.info(f"用户明确请求浏览器捕获工具，已暴露: {restricted_tool.name}")
        else:
            logger.debug("用户未请求截图/录屏，restricted 工具未暴露")

        ptc_tools = (
            _stable_named_items(getattr(self, "ptc_tools", []))
            if access_profile == "frontier"
            else []
        )
        native_web_search = model_supports_native_web_search(
            EnvConfig.ADVAN_MODEL,
            EnvConfig.ADVAN_MODEL_PROVIDER,
        )
        if native_web_search:
            logger.info("主 Agent 已挂载服务端原生 web_search 工具")
            system_prompt += WEB_SEARCH_PROMPT_HINT
        else:
            logger.debug("当前模型路由不支持服务端原生 web_search，跳过挂载")
        subagents = []
        if access_profile == "frontier" and (
            research_subagent := getattr(self, "research_subagent", None)
        ):
            subagents.append(research_subagent)
        if document_subagent := getattr(self, "document_subagent", None):
            subagents.append(document_subagent)
        if access_profile == "frontier" and enable_acp_subagents:
            subagents.extend(_stable_named_items(build_acp_subagents()))

        messages = filter_messages_for_model_capabilities(
            messages,
            EnvConfig.ADVAN_MODEL,
            role="advanced",
        )
        # These third-party middleware classes intentionally use different
        # context type parameters while sharing the same runtime protocol.
        middleware: list[Any] = [
            PIIMiddleware(
                "api_key",
                detector=r"sk-[a-zA-Z0-9]{32}",
                strategy="mask",
            ),
            ToolRetryMiddleware(),
            ModelRetryMiddleware(),
            FilesystemFileSearchMiddleware(root_path=workspace_dir),
            CodeInterpreterMiddleware(ptc=ptc_tools),
            MemoryMiddleware(
                backend=backend,
                sources=[soul_path],
                add_cache_control=True,
                system_prompt=build_workspace_soul_prompt(soul_path),
            ),
        ]
        if allow_silent_reply and access_profile == "frontier":
            middleware.append(SilentReplyMiddleware())
        if any(name in EnvConfig.ADVAN_MODEL.lower() for name in ("gpt", "claude")):
            middleware.append(
                ProviderToolSearchMiddleware(
                    searchable_tools=[tool for tool in effective_tools if tool is not skip_reply]
                )
            )
        if native_web_search:
            middleware.append(NativeWebSearchMiddleware())
        agent = create_deep_agent(
            name=EnvConfig.BOT_NAME,
            model=model,
            system_prompt=system_prompt,
            tools=effective_tools,
            subagents=subagents,
            middleware=middleware,
            skills=[SKILLS_BACKEND_PATH],
            memory=[soul_path],
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
                "virtual_roots": {
                    f"/memory/{workspace_key}/": memory_dir,
                    "/": workspace_dir,
                },
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
                "audio_inputs": audio_inputs or [],
                "video_inputs": video_inputs or [],
                "suppress_reply": False,
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
                "should_reply": True,
            }

        if response is None:
            response = {}
        should_reply = not bool(response.get("suppress_reply", False))
        uni_messages = (
            await FrontierCognitive.extract_uni_messages(response) if should_reply else []
        )
        ai_messages = [message for message in response.get("messages", []) if getattr(message, "type", None) == "ai"]
        if should_reply:
            final_response = (
                ai_messages[-1]
                if ai_messages
                else AIMessage("智能代理处理完成，但没有生成响应。")
            )
        else:
            final_response = AIMessage("")

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
            "should_reply": should_reply,
        }
