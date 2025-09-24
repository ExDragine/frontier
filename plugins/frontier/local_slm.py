import os

import dotenv
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from llama_cpp import Llama

dotenv.load_dotenv()

SLM_MODEL = os.getenv("SLM_MODEL", "")
SLM_MODEL_FILE = os.getenv("SLM_MODEL_FILE", "")
AGENT_DEBUG_MODE = os.getenv("AGENT_DEBUG_MODE", "false")

with open("configs/system_prompt.txt") as f:
    SYSTEM_PROMPT = f.read()

if os.path.exists(f"cache/models/{SLM_MODEL_FILE}"):
    print("Model already exists.")
else:
    Llama.from_pretrained(
        SLM_MODEL,
        filename=SLM_MODEL_FILE,
        verbose=True,
        local_dir="./cache/models/",
    )


llm = ChatLlamaCpp(
    model_path=f"cache/models/{SLM_MODEL_FILE}",
    temperature=0.6,
    n_ctx=1024,
    max_tokens=64,
    top_p=0.95,
    verbose=True,
    streaming=False,
)  # type: ignore

agent = create_react_agent(model=llm, tools=[], debug=AGENT_DEBUG_MODE.lower() == "true")


async def slm_cognitive(system_prompt: str="",user_prompt:str=""):
    if not system_prompt:
        system_prompt = SYSTEM_PROMPT
    messages = {"messages": [SystemMessage(system_prompt), HumanMessage(user_prompt)]}
    result = await agent.ainvoke(messages)
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content,list):
                pass
            else:
                return content
