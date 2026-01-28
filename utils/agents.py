import time
import uuid
import zoneinfo
from datetime import datetime
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import PIIMiddleware
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
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
    if not system_prompt:
        try:
            with open("prompts/system_prompt.txt", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.warning("❌ 未找到 system prompt 文件: prompts/system_prompt.txt")
            system_prompt = "You are a helpful assistant."
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
        middleware=middleware or [],
        response_format=response_format,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]})
    if response_format:
        return result["structured_response"]
    content = ""
    for msg in result["messages"]:
        if msg.type == "ai" and not isinstance(msg.content, list):
            content += msg.content
    return content


class CustomAgentState(AgentState):
    user_id: str


class FrontierCognitive:
    def __init__(self):
        self.tools = agent_tools.all_tools
        self.subagents: list = [fact_check_subagent]
        self.checkpoint = InMemorySaver()
        self.backend = FilesystemBackend(root_dir="./cache/deep_agents")

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
            logger.error("❌ 未找到 system prompt 文件: prompts/system_prompt.txt")
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

    async def chat_agent(self, messages, user_id, user_name, capability: str = "minimal"):
        model = ChatOpenAI(
            api_key=EnvConfig.OPENAI_API_KEY,
            base_url=EnvConfig.OPENAI_BASE_URL,
            model=EnvConfig.ADVAN_MODEL,
            streaming=False,
            reasoning_effort=capability,
            verbosity="low",
            max_retries=2,
            timeout=60,
            use_responses_api=None,
        )
        agent = create_deep_agent(
            model=model,
            system_prompt=self.load_system_prompt(),
            tools=self.tools,
            middleware=[
                PIIMiddleware(
                    "api_key",
                    detector=r"sk-[a-zA-Z0-9]{32}",
                    strategy="block",
                )
            ],
            skills=None,
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
                "thread_id": uuid.uuid5(namespace=uuid.NAMESPACE_OID, name=user_id),
            }
        }
        try:
            response = await agent.ainvoke({"messages": messages, "user_id": user_id}, config=config)
        except TimeoutError as e:
            logger.error(f"❌ Agent请求超时 用户{user_id}: {e}")
            return {
                "response": {"messages": [AIMessage("⏱️ 请求超时，请稍后重试。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
            }
        except (ConnectionError, OSError) as e:
            logger.error(f"❌ Agent网络错误 用户{user_id}: {e}")
            return {
                "response": {"messages": [AIMessage("🌐 网络连接失败，请稍后重试。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
            }
        except (KeyError, AttributeError, ValueError) as e:
            logger.error(f"❌ Agent配置/数据错误 用户{user_id}: {type(e).__name__}: {e}")
            logger.exception("完整错误堆栈:")
            return {
                "response": {"messages": [AIMessage("⚙️ 系统配置错误，请联系管理员。")]},
                "total_time": time.time() - start_time,
                "uni_messages": [],
            }
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
