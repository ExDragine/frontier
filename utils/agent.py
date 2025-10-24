import dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

from utils.config import EnvConfig

dotenv.load_dotenv()

ADVAN_MODEL = EnvConfig.ADVAN_MODEL
BASIC_MODEL = EnvConfig.BASIC_MODEL
OPENAI_BASE_URL = EnvConfig.OPENAI_BASE_URL
OPENAI_API_KEY = SecretStr(EnvConfig.OPENAI_API_KEY)
AGENT_DEBUG_MODE = EnvConfig.AGENT_DEBUG_MODE


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with yes, either reply with no"
    )
    confidence: float = Field(description="The confidence of the decision, a float number between 0 and 1")


async def reply_check(user_prompt: str):
    system_prompt = """ You are a classifier to determine whether to intervene in the current multi-party conversation.
                        You should only reply \"yes\" or \"no\" when \"小李子\" is explicitly mentioned, 
                        the context indicates a need for help and no one else has provided relevant information, 
                        and the intervention will not disrupt the conversation. 
                        Try to avoid inserting into the conversation arbitrarily and only reply when it is absolutely necessary."""
    model = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        model=BASIC_MODEL,
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
    system_prompt: str = "", user_prompt: str = "", use_model: str = BASIC_MODEL, tools=None, response_format=None
):
    model = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        model=use_model,
        streaming=False,
    )
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[TodoListMiddleware()],
        response_format=response_format,
        debug=AGENT_DEBUG_MODE,
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
