import os
import time
from datetime import datetime
from typing import Any

import dotenv
from langchain_core.messages import HumanMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_core.runnables import RunnableConfig
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool
from nonebot import logger, require
from pydantic import SecretStr

from plugins.frontier.tools import ModuleTools

require("nonebot_plugin_alconna")

dotenv.load_dotenv()

store = InMemoryStore(
    index={"dims": 1536, "embed": HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")}
)

module_tools = ModuleTools()


# 自定义状态，支持消息历史管理
class CustomAgentState(AgentState):
    """自定义Agent状态，支持消息历史管理"""

    max_messages: int  # 最大消息数量
    context: dict[str, Any]  # 用于存储额外的上下文信息


def load_system_prompt():
    """从外部文件加载 system prompt"""
    try:
        with open("configs/system_prompt.txt", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("❌ 未找到 system prompt 文件: configs/system_prompt.txt")
        # 返回一个基本的备用 prompt
        return """你的名字是伊卡洛斯，是一个知书达理又随性的可爱的小猫助手。
你具备强大的工具调用能力，能够处理各种问题。根据问题性质灵活选择处理方式。
保持自然对话风格，根据问题复杂程度决定是否使用工具。"""


def prompt(state):
    """准备发送给 LLM 的消息"""

    # 从外部文件加载 system prompt 模板
    prompt_template = load_system_prompt()

    # 格式化 system prompt，替换占位符
    system_prompt = prompt_template.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 确保总是返回消息列表
    return [{"role": "system", "content": system_prompt}, *state["messages"]]


def pre_model_hook(state):
    trimmed_messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=8192,
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
    )
    return {"messages": trimmed_messages}


# ... existing code ...
MODEL = os.getenv("OPENROUTER_MODEL")
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not MODEL or not API_KEY:
    raise ValueError("OPENROUTER_MODEL and OPENROUTER_API_KEY must be set")
API_KEY = SecretStr(API_KEY)

checkpointer = InMemorySaver()
model = ChatOpenAI(model=MODEL, api_key=API_KEY, base_url="https://openrouter.ai/api/v1")


def extract_artifacts(response):
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


def process_artifacts(artifacts):
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


def get_message_segments(processed_artifacts):
    """从处理后的工件中提取所有 MessageSegment"""
    message_segments = []

    for item in processed_artifacts:
        if item["type"] == "uni_message":
            message_segments.append(item["uni_message"])
            logger.info(f"📤 提取 UniMessage: {item['tool_name']}")

    logger.info(f"📨 总共提取到 {len(message_segments)} 个 UniMessage")
    return message_segments


# 简化的主函数 - 直接使用复杂智能体，并添加记忆管理
async def intelligent_agent(messages, user_id):
    """
    智能代理主函数 - 直接使用复杂智能体处理所有问题，支持消息历史长度限制

    Args:
        messages: 用户消息列表
        max_messages: 最大消息历史长度，默认10条

    Returns:
        dict: 包含响应和相关信息的字典
    """
    if not messages:
        return {
            "response": {"messages": [HumanMessage(content="请提供有效的消息内容")]},
            "agent_used": "error",
            "processing_time": 0.0,
            "total_time": 0.0,
            "artifacts": [],
            "processed_artifacts": [],
            "message_segments": [],
        }

    start_time = time.time()
    logger.info("🚀 启动智能代理系统")

    try:
        tools = module_tools.all_tools

        # 创建智能代理，使用自定义状态和消息修剪钩子
        agent = create_react_agent(
            model=model,
            tools=tools + [create_manage_memory_tool(namespace=("memories",))],
            prompt=prompt,
            checkpointer=checkpointer,
            state_schema=CustomAgentState,
            store=store,
            pre_model_hook=pre_model_hook,  # 添加消息修剪钩子
            debug=os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true",
        )

        logger.info("🤖 开始执行智能 Agent...")
        config: RunnableConfig = {"configurable": {"thread_id": f"{user_id}"}}

        # 准备状态，包含最大消息数设置
        agent_input = {"messages": messages, "context": {}}

        response = await agent.ainvoke(agent_input, config=config)

        processing_time = time.time() - start_time
        logger.info(f"✅ 智能代理完成 (耗时: {processing_time:.2f}s)")

        # 提取工件
        artifacts = extract_artifacts(response)
        processed_artifacts = process_artifacts(artifacts)
        message_segments = get_message_segments(processed_artifacts)

        # 获取最后的AI响应
        ai_messages = []
        if response and isinstance(response, dict) and "messages" in response:
            ai_messages = [msg for msg in response["messages"] if hasattr(msg, "type") and msg.type == "ai"]
        final_response = ai_messages[-1] if ai_messages else HumanMessage(content="智能代理处理完成，但没有生成响应。")

        # 构建返回结果
        response_data = {
            "response": {"messages": [final_response]},
            "agent_used": "intelligent",
            "processing_time": processing_time,
            "total_time": processing_time,
            "artifacts": artifacts,
            "processed_artifacts": processed_artifacts,
            "uni_messages": message_segments,
        }

        return response_data

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"💥 智能代理系统执行失败: {str(e)}")

        return {
            "response": {"messages": [HumanMessage(content=f"系统处理出现错误: {str(e)}")]},
            "agent_used": "error",
            "processing_time": total_time,
            "total_time": total_time,
            "artifacts": [],
            "processed_artifacts": [],
            "uni_messages": [],
            "error": str(e),
        }
