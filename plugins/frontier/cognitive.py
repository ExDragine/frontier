import os
import time
from datetime import datetime

import dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from nonebot import logger, require
from pydantic import SecretStr

from plugins.frontier.tools import ModuleTools

require("nonebot_plugin_alconna")

dotenv.load_dotenv()


SLM_MODEL = os.getenv("SLM_MODEL", "")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL")
API_KEY = os.getenv("OPENAI_API_KEY")

if not MODEL or not API_KEY or not BASE_URL:
    raise ValueError("OPENAI_MODEL and OPENAI_API_KEY must be set")
API_KEY = SecretStr(API_KEY)

model = ChatOpenAI(
    api_key=API_KEY, base_url=BASE_URL, model=MODEL, streaming=False, reasoning_effort="high", verbosity="low"
)
slm_model = ChatOpenAI(model=SLM_MODEL, api_key=API_KEY, base_url=BASE_URL, streaming=False)


def load_system_prompt(user_name):
    """从外部文件加载 system prompt"""
    try:
        with open("configs/system_prompt.txt", encoding="utf-8") as f:
            system_prompt = f.read()
            system_prompt = system_prompt.format(
                current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name=user_name
            )
            return system_prompt
    except FileNotFoundError:
        logger.warning("❌ 未找到 system prompt 文件: configs/system_prompt.txt")
        return "Your are a helpful assistant."


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


async def chat_agent(messages, user_id, user_name):
    if not messages:
        return {
            "response": {"messages": [AIMessage(content="请提供有效的消息内容")]},
            "agent_used": "error",
            "processing_time": 0.0,
            "total_time": 0.0,
            "artifacts": [],
            "processed_artifacts": [],
            "message_segments": [],
        }

    start_time = time.time()
    logger.info("🚀 启动智能代理系统")
    prompt_template = load_system_prompt(user_name)
    tools = ModuleTools().all_tools
    logger.info("🤖 开始执行智能 Agent...")
    config: RunnableConfig = {
        "configurable": {
            "thread_id": f"user_{user_id}_thread",
            "user_id": f"user_{user_id}",  # 添加用户ID以增强隔离
        }
    }
    try:
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=prompt_template,
            middleware=[
                # SummarizationMiddleware(model=slm_model),
                # LLMToolSelectorMiddleware(model=slm_model, max_tools=10),
                TodoListMiddleware(),
            ],
            debug=os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true",
        )
        response = await agent.ainvoke({"messages": messages}, config=config)
        processing_time = time.time() - start_time
        logger.info(f"✅ 智能代理完成 (耗时: {processing_time:.2f}s)")
        artifacts = extract_artifacts(response)
        processed_artifacts = process_artifacts(artifacts)
        message_segments = get_message_segments(processed_artifacts)
        ai_messages = []
        if response and isinstance(response, dict) and "messages" in response:
            ai_messages = [msg for msg in response["messages"] if hasattr(msg, "type") and msg.type == "ai"]
        final_response = ai_messages[-1] if ai_messages else AIMessage("智能代理处理完成，但没有生成响应。")
        response_data = {
            "response": {"messages": [final_response]},
            "processing_time": processing_time,
            "total_time": processing_time,
            "artifacts": artifacts,
            "processed_artifacts": processed_artifacts,
            "uni_messages": message_segments,
        }
        return response_data
    except Exception as e:
        logger.error(f"💥 智能代理系统执行失败: {str(e)}")
