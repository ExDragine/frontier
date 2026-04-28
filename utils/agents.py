import base64
import time
import uuid
import zoneinfo
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
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

from tools import agent_tools
from utils.configs import EnvConfig
from utils.llm_factory import create_llm, model_supports
from utils.subagents import get_fact_check_subagent

VISION_OMITTED_NOTICE = "[图片已省略：当前模型不支持视觉输入]"


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


async def assistant_agent(
    system_prompt: str = "",
    user_prompt: str = "",
    use_model: str = EnvConfig.BASIC_MODEL,
    tools=None,
    response_format=None,
    middleware=None,
    images: list[bytes] | None = None,
) -> Any:
    if not system_prompt:
        try:
            with open("prompts/system_prompt.md", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.warning("❌ 未找到 system prompt 文件: prompts/system_prompt.md")
            system_prompt = "You are a helpful assistant."
    route = _configured_model_route(use_model)
    model = create_llm(
        model=use_model,
        streaming=False,
        max_retries=2,
        timeout=300,
        use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
        **route,
    )
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
        return result["structured_response"]
    content = ""
    for msg in result["messages"]:
        if msg.type == "ai" and msg.text:
            content += str(msg.text)
    return content


class CustomAgentState(AgentState):
    user_id: str
    group_id: int


def _agent_thread_id(user_id: str, group_id: int | None) -> uuid.UUID:
    scope = f"group:{group_id}:user:{user_id}" if group_id is not None else f"dm:{user_id}"
    return uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=scope)


class FrontierCognitive:
    def __init__(self):
        self.tools = agent_tools.all_tools
        self.subagents: list = [get_fact_check_subagent()]
        self.checkpoint = InMemorySaver()
        self.backend = FilesystemBackend(root_dir="./cache/sandbox")

    @staticmethod
    def load_system_prompt():
        """从外部文件加载 system prompt"""
        try:
            with open("prompts/system_prompt.md", encoding="utf-8") as f:
                system_prompt = f.read()
                system_prompt = system_prompt.format(
                    name=EnvConfig.BOT_NAME,
                    current_time=datetime.now()
                    .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
                    .strftime("%Y-%m-%d %H:%M:%S"),
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
    async def extract_uni_messages(response):
        """直接从响应中提取 UniMessage 对象"""
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
        query_text: str = "",
    ):
        model_kwargs: dict = {
            "model": EnvConfig.ADVAN_MODEL,
            "streaming": False,
            "max_retries": 2,
            "timeout": 300,
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
        agent = create_deep_agent(
            name=EnvConfig.BOT_NAME,
            model=model,
            system_prompt=self.load_system_prompt(),
            tools=self.tools,
            middleware=[
                PIIMiddleware(
                    "api_key",
                    detector=r"sk-[a-zA-Z0-9]{32}",
                    strategy="block",
                ),
                ToolRetryMiddleware(),
                ModelRetryMiddleware(),
                FilesystemFileSearchMiddleware(root_path="./sandbox/"),
            ],
            skills=["./sandbox/skills/"],
            interrupt_on={
                "write_file": False,
                "read_file": False,
                "edit_file": False,
            },
            backend=self.backend,
            subagents=self.subagents,
            checkpointer=self.checkpoint,
            context_schema=CustomAgentState,
            debug=EnvConfig.AGENT_DEBUG_MODE,
        )
        start_time = time.time()
        logger.info(f"Agent烧烤中~🍖 思考等级: {capability} 用户: {user_name} (ID: {user_id})")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": _agent_thread_id(user_id, group_id),
                "user_id": user_id,
                "group_id": group_id,
            }
        }
        try:
            response = await agent.ainvoke(
                {"messages": messages, "user_id": user_id, "group_id": group_id},
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
            }

        uni_messages = await FrontierCognitive.extract_uni_messages(response)
        ai_messages = [msg for msg in response.get("messages", []) if getattr(msg, "type", None) == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")

        processing_time = time.time() - start_time
        logger.info(f"Agent烤熟了~🥓 (耗时: {processing_time:.2f}s)")

        return {
            "response": {"messages": [final_response]},
            "total_time": processing_time,
            "uni_messages": uni_messages,
        }
