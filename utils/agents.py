import base64
import json
import os
import re
import time
import uuid
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, LocalShellBackend
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    FilesystemFileSearchMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    ToolRetryMiddleware,
)
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from nonebot import logger
from pydantic import ValidationError

from tools import agent_tools
from utils.configs import EnvConfig
from utils.llm_factory import create_llm, model_supports
from utils.message import extract_message_text
from utils.staged_artifacts import extract_staged_artifact_ids, load_staged_artifact, strip_staged_artifact_handoffs
from utils.tool_search import DynamicToolSearchMiddleware, ToolSearchConfig, ToolSearchIndex

UniMessage = None

VISION_OMITTED_NOTICE = "[图片已省略：当前模型不支持视觉输入]"
SKILLS_BACKEND_PATH = "/skills"
MEMORY_BACKEND_PATH = "/memory"
MEMORY_FILE_PATH = "/memory/AGENTS.md"
NO_REPLY_SENTINEL = "_NO_REPLY_"


def _configured_model_route(model: str) -> dict[str, str]:
    if model == EnvConfig.BASIC_MODEL:
        return {
            "provider": EnvConfig.BASIC_MODEL_PROVIDER,
            "endpoint": EnvConfig.BASIC_MODEL_ENDPOINT,
        }
    if model == EnvConfig.ADVAN_MODEL:
        return {
            "provider": EnvConfig.ADVAN_MODEL_PROVIDER,
            "endpoint": EnvConfig.ADVAN_MODEL_ENDPOINT,
        }
    if model == EnvConfig.SIGNAL_MODEL:
        return {
            "provider": EnvConfig.SIGNAL_MODEL_PROVIDER,
            "endpoint": EnvConfig.SIGNAL_MODEL_ENDPOINT,
        }
    return {}


def _append_vision_notice(text: str) -> str:
    return f"{text}\n\n{VISION_OMITTED_NOTICE}" if text else VISION_OMITTED_NOTICE


def _build_user_content(text: str, images: list[bytes] | None, supports_vision: bool = True) -> str | list:
    if not images:
        return text
    if not supports_vision:
        return _append_vision_notice(text)
    return [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(b).decode()}"}}
        for b in images
    ]


def _filter_content_parts_for_text_model(content: list) -> list:
    filtered = [part for part in content if not (isinstance(part, dict) and part.get("type") == "image_url")]
    if len(filtered) == len(content):
        return content
    for index, part in enumerate(filtered):
        if isinstance(part, dict) and part.get("type") == "text":
            updated_part = dict(part)
            updated_part["text"] = _append_vision_notice(str(part.get("text", "")))
            return [*filtered[:index], updated_part, *filtered[index + 1 :]]
    return [{"type": "text", "text": VISION_OMITTED_NOTICE}, *filtered]


def _filter_messages_for_model_capabilities(messages: list[dict], model: str, endpoint: str | None) -> list[dict]:
    if model_supports(model, "vision", endpoint=endpoint):
        return messages
    filtered_messages = []
    for message in messages:
        if not isinstance(message, dict):
            filtered_messages.append(message)
            continue
        content = message.get("content")
        if isinstance(content, list):
            filtered_messages.append({**message, "content": _filter_content_parts_for_text_model(content)})
        else:
            filtered_messages.append(message)
    return filtered_messages


def _message_text_content(message) -> str:
    """提取消息文本（兼容旧名称，委托给 extract_message_text）。"""
    return extract_message_text(message)


def _json_document_candidates(text: str, *, prefer_object: bool = False) -> list[str]:
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        text = fenced_match.group(1).strip()

    decoder = json.JSONDecoder()
    candidates = []
    for index, char in enumerate(text):
        if char not in ("{" if prefer_object else "{["):
            continue
        try:
            _, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        candidates.append(text[index : index + end])
    return candidates or [text]


def _parse_structured_response_from_messages(messages: list, response_format):
    for message in reversed(messages):
        if getattr(message, "type", None) != "ai":
            continue
        text = _message_text_content(message).strip()
        if not text:
            continue
        if hasattr(response_format, "model_validate_json"):
            last_error = None
            for candidate in _json_document_candidates(text, prefer_object=True):
                try:
                    return response_format.model_validate_json(candidate)
                except ValidationError as e:
                    last_error = e
            if last_error is not None:
                raise last_error
        break
    raise KeyError("structured_response")


async def assistant_agent(
    system_prompt: str = "",
    user_prompt: str = "",
    use_model: str = EnvConfig.BASIC_MODEL,
    tools=None,
    response_format=None,
    middleware=None,
    images: list[bytes] | None = None,
    reasoning_effort: str | None = None,
    temperature: float | None = None,
    model_kwargs: dict | None = None,
) -> Any:
    if not system_prompt:
        try:
            with open("prompts/system_prompt.md", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.warning("❌ 未找到 system prompt 文件: prompts/system_prompt.md")
            system_prompt = "You are a helpful assistant."
    route = _configured_model_route(use_model)
    llm_kwargs: dict[str, Any] = {
        "model": use_model,
        "streaming": False,
        "max_retries": 2,
        "timeout": 300,
        "use_responses_api": EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
        **route,
    }
    if reasoning_effort is not None:
        llm_kwargs["reasoning_effort"] = reasoning_effort
    if temperature is not None:
        llm_kwargs["temperature"] = temperature
    if model_kwargs is not None:
        llm_kwargs["model_kwargs"] = model_kwargs
    model = create_llm(**llm_kwargs)
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware or [],
        response_format=response_format,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": _build_user_content(
                        user_prompt,
                        images,
                        supports_vision=model_supports(use_model, "vision", endpoint=route.get("endpoint")),
                    ),
                }
            ]
        }
    )
    if response_format:
        if "structured_response" in result:
            return result["structured_response"]
        return _parse_structured_response_from_messages(result.get("messages", []), response_format)
    content = ""
    for msg in result["messages"]:
        if msg.type == "ai" and msg.text:
            content += str(msg.text)
    return content


class CustomAgentState(AgentState):
    user_id: str
    group_id: int | None
    image_inputs: list[bytes]
    video_inputs: list[bytes]


def _agent_thread_id(user_id: str, group_id: int | None) -> uuid.UUID:
    scope = f"group:{group_id}:user:{user_id}" if group_id is not None else f"dm:{user_id}"
    return uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=scope)


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _build_agent_backend(working_dir: str, workspace_key: str) -> CompositeBackend:
    workspace_dir = _ensure_dir(os.path.join(working_dir, "workspaces", workspace_key))
    skills_dir = _ensure_dir(os.path.join(working_dir, "skills"))
    memory_dir = _ensure_dir(os.path.join(working_dir, "memory"))

    return CompositeBackend(
        default=LocalShellBackend(root_dir=workspace_dir, virtual_mode=True, inherit_env=True),
        routes={
            f"{SKILLS_BACKEND_PATH}/": FilesystemBackend(root_dir=skills_dir, virtual_mode=True),
            f"{MEMORY_BACKEND_PATH}/": FilesystemBackend(root_dir=memory_dir, virtual_mode=True),
        },
    )


class FrontierCognitive:
    def __init__(self):
        if EnvConfig.TOOL_SEARCH_ENABLED:
            self.tools = agent_tools.core_tools
            self.tool_search_index = ToolSearchIndex(
                agent_tools.searchable_tools,
                metadata_by_name=agent_tools.tool_metadata,
                config=ToolSearchConfig.from_env(),
            )
        else:
            self.tools = agent_tools.main_tools
        self.checkpoint = InMemorySaver()
        self.working_dir = os.path.join(os.getcwd(), "cache", "sandbox")
        _ensure_dir(self.working_dir)

    @staticmethod
    def load_system_prompt():
        """从外部文件加载 system prompt"""
        try:
            with open("prompts/system_prompt.md", encoding="utf-8") as f:
                system_prompt = f.read()
                system_prompt = system_prompt.format(
                    name=EnvConfig.BOT_NAME,
                )
                return system_prompt
        except FileNotFoundError:
            logger.error("❌ 未找到 system prompt 文件: prompts/system_prompt.md")
            return f"You are {EnvConfig.BOT_NAME}, a helpful assistant. [配置错误: system prompt文件缺失]"
        except PermissionError as e:
            logger.error(f"❌ 无权限读取 system prompt 文件: {e}")
            return f"You are {EnvConfig.BOT_NAME}, a helpful assistant. [配置错误: 无读取权限]"
        except UnicodeDecodeError as e:
            logger.error(f"❌ system prompt 文件编码错误: {e}")
            return f"You are {EnvConfig.BOT_NAME}, a helpful assistant. [配置错误: 文件编码无效]"
        except KeyError as e:
            logger.error(f"❌ system prompt 模板变量缺失: {e}")
            return f"You are {EnvConfig.BOT_NAME}, a helpful assistant. [配置错误: 模板变量缺失]"

    @staticmethod
    def _uni_message_cls():
        global UniMessage
        if UniMessage is not None:
            return UniMessage
        from nonebot import require

        require("nonebot_plugin_alconna")
        from nonebot_plugin_alconna import UniMessage as LoadedUniMessage

        UniMessage = LoadedUniMessage
        return LoadedUniMessage

    @staticmethod
    def _message_text(message) -> str:
        """提取消息文本（委托给 extract_message_text）。"""
        return extract_message_text(message)

    @staticmethod
    def clean_staged_artifact_handoffs(message):
        content = getattr(message, "content", None)
        if isinstance(content, str):
            cleaned = strip_staged_artifact_handoffs(content)
            if cleaned != content:
                try:
                    message.content = cleaned
                    if hasattr(message, "text") and not callable(getattr(message, "text", None)):
                        message.text = cleaned
                    return message
                except Exception:
                    return AIMessage(cleaned)
            return message
        if isinstance(content, list):
            changed = False
            cleaned_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = str(part.get("text", ""))
                    cleaned_text = strip_staged_artifact_handoffs(text)
                    changed = changed or cleaned_text != text
                    cleaned_parts.append({**part, "text": cleaned_text})
                else:
                    cleaned_parts.append(part)
            if changed:
                try:
                    message.content = cleaned_parts
                except Exception:
                    return AIMessage(cleaned_parts)
        return message

    @staticmethod
    async def extract_uni_messages(response):
        """直接从响应中提取 UniMessage 对象"""
        if not response or not isinstance(response, dict):
            logger.warning("⚠️ extract_uni_messages: response 为空或不是字典类型")
            return []

        uni_messages = []
        seen_staged_artifacts: set[str] = set()
        staged_send_tool_ran = any(
            getattr(message, "type", None) == "tool"
            and getattr(message, "name", None) == "send_staged_artifact"
            and getattr(message, "artifact", None) is not None
            for message in response.get("messages", [])
        )
        for message in response.get("messages", []):
            if getattr(message, "type", None) == "tool" and getattr(message, "artifact", None) is not None:
                tool_name = getattr(message, "name", "unknown")
                uni_messages.append(message.artifact)
                logger.info(f"📤 提取 UniMessage: {tool_name} - 类型: {type(message.artifact)}")
            if staged_send_tool_ran:
                continue
            for artifact_id in extract_staged_artifact_ids(FrontierCognitive._message_text(message)):
                if artifact_id in seen_staged_artifacts:
                    continue
                try:
                    uni_messages.append(
                        load_staged_artifact(artifact_id, uni_message_cls=FrontierCognitive._uni_message_cls())
                    )
                    seen_staged_artifacts.add(artifact_id)
                    logger.info(f"📤 从 staged_artifact 兜底提取 UniMessage: {artifact_id}")
                except Exception as exc:
                    logger.warning(f"⚠️ staged_artifact 提取失败: {artifact_id} ({type(exc).__name__}: {exc})")

        logger.info(f"📨 总共提取到 {len(uni_messages)} 个 UniMessage")
        return uni_messages

    async def chat_agent(
        self,
        messages,
        user_id,
        user_name,
        capability: str = "none",
        group_id: int | None = None,
        query_text: str = "",
        image_inputs: list[bytes] | None = None,
        video_inputs: list[bytes] | None = None,
        thread_id_override: uuid.UUID | str | None = None,
    ):
        model_kwargs: dict = {
            "model": EnvConfig.ADVAN_MODEL,
            "streaming": False,
            "max_retries": 2,
            "timeout": EnvConfig.AGENT_LLM_TIMEOUT_SECONDS,
            "use_responses_api": EnvConfig.ADVAN_MODEL_USE_RESPONSES_API,
            "provider": EnvConfig.ADVAN_MODEL_PROVIDER,
            "endpoint": EnvConfig.ADVAN_MODEL_ENDPOINT,
        }
        if EnvConfig.ADVAN_MODEL_USE_RESPONSES_API:
            model_kwargs["reasoning_effort"] = capability
            model_kwargs["verbosity"] = "low"
        model = create_llm(**model_kwargs)
        messages = _filter_messages_for_model_capabilities(
            messages,
            EnvConfig.ADVAN_MODEL,
            endpoint=EnvConfig.ADVAN_MODEL_ENDPOINT,
        )
        working_dir = getattr(self, "working_dir", os.path.join(os.getcwd(), "cache", "sandbox"))
        thread_id = thread_id_override or _agent_thread_id(user_id, group_id)
        if not isinstance(thread_id, uuid.UUID):
            thread_id = uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=str(thread_id))
        workspace_key = str(group_id) if group_id is not None else str(user_id)
        backend = _build_agent_backend(working_dir, workspace_key)
        workspace_dir = os.path.join(working_dir, "workspaces", workspace_key)
        system_prompt = self.load_system_prompt()

        # ── 注入长期用户画像到 system prompt ──
        try:
            from utils.user_profile import get_profile_manager

            profile_context = get_profile_manager().build_context_injection(int(user_id) if user_id else 0, group_id)
            if profile_context:
                system_prompt = f"{system_prompt}\n\n{profile_context}"
        except Exception as exc:
            logger.debug("Profile context injection skipped: %s: %s", type(exc).__name__, exc)
        middleware = []
        if tool_search_index := getattr(self, "tool_search_index", None):
            middleware.append(DynamicToolSearchMiddleware(tool_search_index))
        middleware.extend(
            [
                PIIMiddleware(
                    "api_key",
                    detector=r"sk-[a-zA-Z0-9]{32}",
                    strategy="block",
                ),
                ToolRetryMiddleware(),
                ModelRetryMiddleware(),
                FilesystemFileSearchMiddleware(root_path=workspace_dir),
            ]
        )
        agent = create_deep_agent(
            name=EnvConfig.BOT_NAME,
            model=model,
            system_prompt=system_prompt,
            tools=self.tools,
            middleware=middleware,
            skills=[SKILLS_BACKEND_PATH],
            memory=[MEMORY_FILE_PATH],
            interrupt_on={
                "write_file": False,
                "read_file": False,
                "edit_file": False,
                "execute": False,
            },
            backend=backend,
            context_schema=CustomAgentState,
            debug=EnvConfig.AGENT_DEBUG_MODE,
        )
        start_time = time.time()
        logger.info(f"Agent烧烤中~🍖 思考等级: {capability} 用户: {user_name} (ID: {user_id})")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "group_id": group_id,
                "workspace_dir": workspace_dir,
            }
        }
        try:
            response = await agent.ainvoke(
                {
                    "messages": messages,
                    "user_id": user_id,
                    "group_id": group_id,
                    "image_inputs": image_inputs or [],
                    "video_inputs": video_inputs or [],
                },
                config=config,
            )
        except Exception as e:
            # 其他意外错误，记录详细信息
            logger.error(f"❌ Agent执行出现意外错误 用户{user_id}: {type(e).__name__}: {e}")
            logger.exception("完整错误堆栈:")
            return {
                "response": {"messages": [AIMessage("💥 服务暂时不可用，请稍后重试。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
                "error": str(e),
            }

        uni_messages = await FrontierCognitive.extract_uni_messages(response)
        ai_messages = [msg for msg in response.get("messages", []) if getattr(msg, "type", None) == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")
        final_response = FrontierCognitive.clean_staged_artifact_handoffs(final_response)

        processing_time = time.time() - start_time
        logger.info(f"Agent烤熟了~🥓 (耗时: {processing_time:.2f}s)")

        return {
            "response": {"messages": [final_response]},
            "total_time": processing_time,
            "uni_messages": uni_messages,
        }
