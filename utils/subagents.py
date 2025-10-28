import zoneinfo
from datetime import datetime

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from tools import agent_tools
from utils.configs import EnvConfig

ADVAN_MODEL = EnvConfig.ADVAN_MODEL
BASIC_MODEL = EnvConfig.BASIC_MODEL
OPENAI_BASE_URL = EnvConfig.OPENAI_BASE_URL
OPENAI_API_KEY = SecretStr(EnvConfig.OPENAI_API_KEY)
AGENT_DEBUG_MODE = EnvConfig.AGENT_DEBUG_MODE

model = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    model=BASIC_MODEL,
)
fact_check_subagent = {
    "name": "fact_check_agent",
    "description": "核查信息中提到的关键内容的真实性，提供准确的事实依据。",
    "system_prompt": f"""
        ## Basic Requirements
        Verify the authenticity of the key information mentioned in the information provided by the user.
        Please provide accurate factual evidence based on reliable sources and data. The following are a few guiding principles:
        1. Find authoritative sources: Prioritize authoritative sources such as government websites, well-known news organizations, and academic papers.
        2. Multi-source verification: Verify key information from multiple sources to ensure its accuracy and consistency.
        3. Provide citations: Provide citations for the sources of information in the answer for users to consult further.
        4. Avoid bias: Ensure the neutrality of the information, avoiding any form of bias and misinformation.
        Please verify the information provided by the user according to the above guiding principles and provide accurate factual evidence.
        
        Please follow the following guidelines when replying:
        1.  Point out the information points that need correction and provide the correct factual basis.
        2.  Provide citations for the sources of the information to facilitate further verification by the user.
        3.  Keep it brief and clear, and avoid lengthy explanations.
        
        ## Additional Instructions
        The current time is UTC+8: {datetime.now().astimezone(zoneinfo.ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")}
    """,
    "tools": agent_tools.web_tools,
    "model": model,
    # "middleware": [],
    # "interrupt_on": {},
}
