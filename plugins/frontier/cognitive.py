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
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.store.memory import InMemoryStore
from nonebot import logger, require
from pydantic import SecretStr

from plugins.frontier.tools import ModuleTools

require("nonebot_plugin_alconna")

dotenv.load_dotenv()

module_tools = ModuleTools()


# 移除全局store，改为在函数内创建
def create_user_store():
    """为每个用户会话创建独立的store实例"""
    return InMemoryStore(
        index={"dims": 384, "embed": HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")}
    )


# 自定义状态，支持消息历史管理
class CustomAgentState(AgentState):
    """自定义Agent状态，支持消息历史管理"""

    max_messages: int  # 最大消息数量，默认10条
    context: dict[str, Any]  # 用于存储额外的上下文信息


def load_system_prompt():
    """从外部文件加载 system prompt"""
    try:
        with open("configs/system_prompt.txt", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("❌ 未找到 system prompt 文件: configs/system_prompt.txt")
        return "Keep response simple."


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
        max_tokens=64,
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
    )
    return {"messages": trimmed_messages}


# ... existing code ...
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL")
API_KEY = os.getenv("OPENAI_API_KEY")

if not MODEL or not API_KEY or not BASE_URL:
    raise ValueError("OPENAI_MODEL and OPENAI_API_KEY must be set")
API_KEY = SecretStr(API_KEY)

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL,
    max_tokens=1024,  # type: ignore
    reasoning={"enable": True},
    temperature=0.7,
    streaming=False,
)


async def create_user_checkpointer(user_id: str):
    """为每个用户会话创建独立的SQLite checkpointer实例"""
    # 确保cache目录存在
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"📁 创建cache目录: {cache_dir}")

    # 为每个用户创建独立的SQLite数据库文件
    db_path = f"{cache_dir}/checkpoints_user_{user_id}.db"
    logger.debug(f"💾 用户 {user_id} 的数据库路径: {db_path}")
    return AsyncSqliteSaver.from_conn_string(db_path)


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
        user_id: 用户唯一标识符，用于数据隔离

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

        # 为当前用户创建独立的store实例
        user_store = create_user_store()

        logger.info(f"👤 为用户 {user_id} 创建独立的存储实例")
        logger.debug(f"🔍 Store实例ID: {id(user_store)}")

        # 使用SQLite checkpointer的异步上下文管理器
        async with await create_user_checkpointer(user_id) as user_checkpointer:
            logger.debug(f"🔍 Checkpointer实例ID: {id(user_checkpointer)}")

            # 创建智能代理，使用自定义状态和消息修剪钩子
            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt=prompt,
                checkpointer=user_checkpointer,
                state_schema=CustomAgentState,
                store=user_store,
                pre_model_hook=pre_model_hook,  # 添加消息修剪钩子
                debug=os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true",
            )

            logger.info("🤖 开始执行智能 Agent...")
            config: RunnableConfig = {
                "configurable": {
                    "thread_id": f"user_{user_id}_thread",
                    "user_id": str(user_id),  # 添加用户ID以增强隔离
                }
            }

            # 准备状态，包含最大消息数设置
            agent_input = {
                "messages": messages,
                "context": {},
                "max_messages": 10,  # 默认最大消息数
            }

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
            final_response = (
                ai_messages[-1] if ai_messages else HumanMessage(content="智能代理处理完成，但没有生成响应。")
            )

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
