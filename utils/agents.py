import time
import zoneinfo
from datetime import datetime

from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from nonebot import logger
from pydantic import BaseModel, Field

from tools import agent_tools
from utils.configs import EnvConfig
from utils.subagents import fact_check_subagent


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with yes, either reply with no"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


async def reply_check(user_prompt: str):
    system_prompt = f""" You are a classifier to determine whether to intervene in the current multi-party conversation.
                        You should only reply \"yes\" or \"no\" when \"{EnvConfig.BOT_NAME}\" is explicitly mentioned, 
                        the context indicates a need for help and no one else has provided relevant information, 
                        and the intervention will not disrupt the conversation. 
                        Try to avoid inserting into the conversation arbitrarily and only reply when it is absolutely necessary."""
    model = ChatOpenAI(
        api_key=EnvConfig.OPENAI_API_KEY,
        base_url=EnvConfig.OPENAI_BASE_URL,
        model=EnvConfig.BASIC_MODEL,
        reasoning_effort="high",
    )
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=system_prompt,
        response_format=ReplyCheck,
    )
    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]})
    structured_response: ReplyCheck = result["structured_response"]
    if structured_response.should_reply.lower() == "yes" and structured_response.confidence >= 0.7:
        return True
    return False


async def cognitive(
    system_prompt: str = "",
    user_prompt: str = "",
    use_model: str = EnvConfig.BASIC_MODEL,
    tools=None,
    response_format=None,
):
    model = ChatOpenAI(
        api_key=EnvConfig.OPENAI_API_KEY,
        base_url=EnvConfig.OPENAI_BASE_URL,
        model=use_model,
        streaming=False,
    )
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[TodoListMiddleware()],
        response_format=response_format,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    if not system_prompt:
        with open("configs/system_prompt.txt") as f:
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


class FrontierCognitive:
    def __init__(self):
        self.model = ChatOpenAI(
            api_key=EnvConfig.OPENAI_API_KEY,
            base_url=EnvConfig.OPENAI_BASE_URL,
            model=EnvConfig.ADVAN_MODEL,
            streaming=False,
            reasoning_effort="high",
            verbosity="low",
        )
        self.tools = agent_tools.all_tools
        self.subagents: list = [fact_check_subagent]
        self.prompt_template = FrontierCognitive.load_system_prompt()
        self.agent = create_deep_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.prompt_template,
            subagents=self.subagents,
            debug=EnvConfig.AGENT_DEBUG_MODE,
        )

    @staticmethod
    def load_system_prompt():
        """从外部文件加载 system prompt"""
        try:
            with open("configs/system_prompt.txt", encoding="utf-8") as f:
                system_prompt = f.read()
                system_prompt = system_prompt.format(
                    name=EnvConfig.BOT_NAME,
                    current_time=datetime.now()
                    .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
                    .strftime("%Y-%m-%d %H:%M:%S"),
                )
                return system_prompt
        except FileNotFoundError:
            logger.warning("❌ 未找到 system prompt 文件: configs/system_prompt.txt")
            return "Your are a helpful assistant."

    @staticmethod
    async def extract_artifacts(response):
        """提取响应中的工件"""
        artifacts = []

        # 添加安全检查
        if not response or not isinstance(response, dict):
            logger.warning("⚠️ extract_artifacts: response 为空或不是字典类型")
            return artifacts

        if "messages" in response and response["messages"]:
            for message in response["messages"]:
                # 检查是否是 ToolMessage 并且有 artifact
                if hasattr(message, "type") and message.type == "tool":
                    if hasattr(message, "artifact") and message.artifact is not None:
                        artifact_info = {
                            "tool_name": getattr(message, "name", "unknown"),
                            "tool_call_id": getattr(message, "tool_call_id", ""),
                            "content": message.content,
                            "artifact": message.artifact,
                        }
                        artifacts.append(artifact_info)
                        logger.info(f"🎯 发现工件: {artifact_info['tool_name']} - 类型: {type(message.artifact)}")
        logger.info(f"📦 总共提取到 {len(artifacts)} 个工件")
        return artifacts

    @staticmethod
    async def process_artifacts(artifacts):
        """处理工件，提取可直接使用的内容"""
        processed = []

        for artifact_info in artifacts:
            artifact = artifact_info["artifact"]
            tool_name = artifact_info["tool_name"]

            processed_item = {
                "tool_name": tool_name,
                "type": "uni_message",
                "content": artifact_info["content"],
                "uni_message": artifact,
            }
            processed.append(processed_item)
            logger.info(f"✨ 处理工件: {tool_name}")

        return processed

    @staticmethod
    async def get_message_segments(processed_artifacts):
        """从处理后的工件中提取所有 MessageSegment"""
        message_segments = []

        for item in processed_artifacts:
            if item["type"] == "uni_message":
                message_segments.append(item["uni_message"])
                logger.info(f"📤 提取 UniMessage: {item['tool_name']}")

        logger.info(f"📨 总共提取到 {len(message_segments)} 个 UniMessage")
        return message_segments

    async def chat_agent(self, messages, user_id, user_name):
        start_time = time.time()
        if not messages:
            return {
                "response": {"messages": [AIMessage(content="请提供有效的消息内容")]},
                "total_time": 0.0,
                "artifacts": [],
                "processed_artifacts": [],
                "uni_messages": [],
            }
        logger.info(f"Agent烧烤中~🍖 用户: {user_name} (ID: {user_id})")
        config: RunnableConfig = {
            "configurable": {
                "thread_id": f"user_{user_id}_thread",
                "user_id": f"user_{user_id}",  # 添加用户ID以增强隔离
            }
        }
        try:
            response = await self.agent.ainvoke({"messages": messages}, config=config)
        except Exception as e:
            return {
                "response": {"messages": [AIMessage(f"💥 智能代理系统执行失败: {str(e)}")]},
                "total_time": time.time() - start_time,
                "artifacts": [],
                "processed_artifacts": [],
                "uni_messages": [],
            }
        artifacts = await FrontierCognitive.extract_artifacts(response)
        processed_artifacts = await FrontierCognitive.process_artifacts(artifacts)
        message_segments = await FrontierCognitive.get_message_segments(processed_artifacts)
        ai_messages = []
        if response and isinstance(response, dict) and "messages" in response:
            ai_messages = [msg for msg in response["messages"] if hasattr(msg, "type") and msg.type == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")
        processing_time = time.time() - start_time
        logger.info(f"Agent烤熟了~🥓 (耗时: {processing_time:.2f}s)")
        response_data = {
            "response": {"messages": [final_response]},
            "total_time": processing_time,
            "artifacts": artifacts,
            "processed_artifacts": processed_artifacts,
            "uni_messages": message_segments,
        }
        return response_data
