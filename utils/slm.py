import os

import dotenv
from langchain.agents import create_agent
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

dotenv.load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "")
SLM_MODEL = os.getenv("SLM_MODEL", "")
BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = SecretStr(os.getenv("OPENAI_API_KEY", ""))
AGENT_DEBUG_MODE = os.getenv("AGENT_DEBUG_MODE", "false")

if not SLM_MODEL or not API_KEY or not BASE_URL:
    raise ValueError("OPENAI_MODEL and OPENAI_API_KEY must be set")


class ReplyCheck(BaseModel):
    should_reply: str = Field(
        description="Should or not reply message. If should, reply with yes, either reply with no"
    )


async def reply_check(user_prompt):
    system = "你是一个分类器，用来判断是否应该介入当前多个用户的对话中,当明确提及“小李子”，且上下文表达出需要帮助且别人没提供相关信息时，且不会破坏交流的情况下才需要做出回复。"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])
    model_with_struct = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=SLM_MODEL,
        streaming=False,
    ).with_structured_output(ReplyCheck)
    model_with_struct_and_prompt = prompt | model_with_struct
    result: ReplyCheck = await model_with_struct_and_prompt.ainvoke(user_prompt)  # type: ignore
    match result.should_reply.lower():
        case "yes":
            return True
        case _:
            return False


async def slm_cognitive(system_prompt: str = "", user_prompt: str = "", use_model: str = SLM_MODEL, tools=None):
    model = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=use_model,
        streaming=False,
    )
    agent = create_agent(
        model=model, tools=tools, system_prompt=system_prompt, debug=AGENT_DEBUG_MODE.lower() == "true"
    )
    if not system_prompt:
        with open("configs/system_prompt.txt") as f:
            SYSTEM_PROMPT = f.read()
        system_prompt = SYSTEM_PROMPT
    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]})
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                pass
            else:
                return content
