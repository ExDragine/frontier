import os

import dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from pydantic import SecretStr

dotenv.load_dotenv()

SLM_MODEL = os.getenv("SLM_MODEL", "")
BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
AGENT_DEBUG_MODE = os.getenv("AGENT_DEBUG_MODE", "false")

if not SLM_MODEL or not API_KEY or not BASE_URL:
    raise ValueError("OPENAI_MODEL and OPENAI_API_KEY must be set")
API_KEY = SecretStr(API_KEY)

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=SLM_MODEL,
    streaming=False,
)

with open("configs/system_prompt.txt") as f:
    SYSTEM_PROMPT = f.read()


agent = create_react_agent(model=model, tools=[], debug=AGENT_DEBUG_MODE.lower() == "true")


async def slm_cognitive(system_prompt: str = "", user_prompt: str = ""):
    if not system_prompt:
        system_prompt = SYSTEM_PROMPT
    messages = {"messages": [SystemMessage(system_prompt), HumanMessage(user_prompt)]}
    result = await agent.ainvoke(messages)
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                pass
            else:
                return content
