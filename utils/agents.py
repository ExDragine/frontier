import time
import uuid
import zoneinfo
from datetime import datetime
from typing import Any, Literal

from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import PIIMiddleware, SummarizationMiddleware, TodoListMiddleware, ToolRetryMiddleware
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from nonebot import logger

from tools import agent_tools
from utils.configs import EnvConfig
from utils.subagents import fact_check_subagent


async def assistant_agent(
    system_prompt: str = "",
    user_prompt: str = "",
    use_model: str = EnvConfig.BASIC_MODEL,
    tools=None,
    response_format=None,
    middleware=None,
) -> Any:
    model = ChatOpenAI(
        api_key=EnvConfig.OPENAI_API_KEY,
        base_url=EnvConfig.OPENAI_BASE_URL,
        model=use_model,
        streaming=False,
        max_retries=2,
        timeout=30,
    )
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware if middleware else [],
        response_format=response_format,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    if not system_prompt:
        with open("prompts/system_prompt.txt", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()
        system_prompt = SYSTEM_PROMPT
    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]})
    if response_format:
        return result["structured_response"]
    content = ""
    for msg in result["messages"]:
        if msg.type == "ai":
            if isinstance(msg.content, list):
                pass
            else:
                content += msg.content
    return content


class CustomAgentState(AgentState):
    user_id: str


class FrontierCognitive:
    def __init__(self):
        self.tools = agent_tools.all_tools
        self.subagents: list = [fact_check_subagent]
        self.prompt_template = FrontierCognitive.load_system_prompt()
        self.model = FrontierCognitive.create_model(reasoning_effort="medium")
        self.backend = FilesystemBackend(root_dir="./cache/deep_agents")
        self.interrupt_on = None
        self.middleware = [
            FilesystemMiddleware(backend=self.backend),
            TodoListMiddleware(),
            ToolRetryMiddleware(),
            PIIMiddleware(
                "api_key",
                detector=r"sk-[a-zA-Z0-9]{32}",
                strategy="block",
            ),
            SubAgentMiddleware(
                default_model=self.model,
                default_tools=self.tools,
                subagents=self.subagents if self.subagents is not None else [],
                default_middleware=[
                    TodoListMiddleware(),
                    FilesystemMiddleware(backend=self.backend),
                    SummarizationMiddleware(
                        model=self.model,
                        max_tokens_before_summary=170000,
                        messages_to_keep=6,
                    ),
                    PatchToolCallsMiddleware(),
                ],
                default_interrupt_on=self.interrupt_on,
                general_purpose_agent=True,
            ),
            SummarizationMiddleware(
                model=FrontierCognitive.create_model(reasoning_effort="low", verbosity="medium"),
                max_tokens_before_summary=50000,
            ),
            PatchToolCallsMiddleware(),
        ]

    @staticmethod
    def create_model(
        streaming: bool = False,
        reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = "minimal",
        verbosity: Literal["low", "medium", "high"] | None = "low",
    ):
        model = ChatOpenAI(
            api_key=EnvConfig.OPENAI_API_KEY,
            base_url=EnvConfig.OPENAI_BASE_URL,
            model=EnvConfig.ADVAN_MODEL,
            streaming=streaming,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            max_retries=2,
            timeout=60,
        )
        return model

    @staticmethod
    def create_agent(model, middleware, prompt_template, subagents, tools, agent_capability) -> CompiledStateGraph:
        agents = {
            "normal": create_agent(
                model=model,
                tools=tools,
                system_prompt=prompt_template,
                middleware=[
                    PIIMiddleware(
                        "api_key",
                        detector=r"sk-[a-zA-Z0-9]{32}",
                        strategy="block",
                    ),
                    PatchToolCallsMiddleware(),
                ],
                checkpointer=InMemorySaver(),
                state_schema=CustomAgentState,
                debug=EnvConfig.AGENT_DEBUG_MODE,
            ),
            "heavy": create_agent(
                model=model,
                tools=tools,
                system_prompt=prompt_template,
                middleware=middleware,
                checkpointer=InMemorySaver(),
                state_schema=CustomAgentState,
                debug=EnvConfig.AGENT_DEBUG_MODE,
            ),
        }
        agent: Any = agents.get(agent_capability, EnvConfig.AGENT_CAPABILITY)
        return agent

    @staticmethod
    def load_system_prompt():
        """从外部文件加载 system prompt"""
        try:
            with open("prompts/system_prompt.txt", encoding="utf-8") as f:
                system_prompt = f.read()
                system_prompt = system_prompt.format(
                    name=EnvConfig.BOT_NAME,
                    current_time=datetime.now()
                    .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
                    .strftime("%Y-%m-%d %H:%M:%S"),
                )
                return system_prompt
        except FileNotFoundError:
            logger.warning("❌ 未找到 system prompt 文件: prompts/system_prompt.txt")
            return "Your are a helpful assistant."

    @staticmethod
    async def extract_uni_messages(response):
        """直接从响应中提取 UniMessage 对象"""
        uni_messages = []

        if not response or not isinstance(response, dict):
            logger.warning("⚠️ extract_uni_messages: response 为空或不是字典类型")
            return uni_messages

        if "messages" in response and response["messages"]:
            for message in response["messages"]:
                # 检查是否是 ToolMessage 并且有 artifact
                if (
                    hasattr(message, "type")
                    and message.type == "tool"
                    and hasattr(message, "artifact")
                    and message.artifact is not None
                ):
                    tool_name = getattr(message, "name", "unknown")
                    uni_messages.append(message.artifact)
                    logger.info(f"📤 提取 UniMessage: {tool_name} - 类型: {type(message.artifact)}")

        logger.info(f"📨 总共提取到 {len(uni_messages)} 个 UniMessage")
        return uni_messages

    async def chat_agent(self, messages, user_id, user_name, agent_capability: Literal["lite", "normal", "heavy"]):
        start_time = time.time()
        agent = FrontierCognitive.create_agent(
            self.model, self.middleware, self.prompt_template, self.subagents, self.tools, agent_capability
        )
        logger.info(f"Agent烧烤中~🍖 思考等级: {agent_capability} 用户: {user_name} (ID: {user_id})")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=user_id),
            }
        }
        try:
            response = await agent.ainvoke({"messages": messages, "user_id": user_id}, config=config)
        except Exception as e:
            logger.error(f"❌ 智能代理系统执行失败: {str(e)}")
            return {
                "response": {"messages": [AIMessage("💥 这不是你的问题，也不是我的问题，这是服务商的问题。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
            }
        uni_messages = await FrontierCognitive.extract_uni_messages(response)
        ai_messages = []
        if response and isinstance(response, dict) and "messages" in response:
            ai_messages = [msg for msg in response["messages"] if hasattr(msg, "type") and msg.type == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")
        processing_time = time.time() - start_time
        logger.info(f"Agent烤熟了~🥓 (耗时: {processing_time:.2f}s)")
        response_data = {
            "response": {"messages": [final_response]},
            "total_time": processing_time,
            "uni_messages": uni_messages,
        }
        return response_data
