import zoneinfo
from datetime import datetime

from tools import agent_tools
from utils.configs import EnvConfig
from utils.llm_factory import create_llm

ADVAN_MODEL = EnvConfig.ADVAN_MODEL
BASIC_MODEL = EnvConfig.BASIC_MODEL
AGENT_DEBUG_MODE = EnvConfig.AGENT_DEBUG_MODE

model = create_llm(
    model=BASIC_MODEL,
    max_retries=2,
    timeout=30,
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
    provider=EnvConfig.BASIC_MODEL_PROVIDER,
    endpoint=EnvConfig.BASIC_MODEL_ENDPOINT,
)


def _tools_for(group: str) -> list:
    return list(agent_tools.subagent_tools.get(group, []))


def _domain_subagent(name: str, description: str, system_prompt: str, tools: list) -> dict:
    return {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": tools,
        "model": model,
    }


def get_general_purpose_subagent() -> dict:
    return _domain_subagent(
        name="general-purpose",
        description="Handle general reasoning tasks that do not require specialized tools.",
        system_prompt="""
        You are a general-purpose reasoning subagent.
        Help with analysis, decomposition, and drafting when no specialized tool is required.
        Do not claim to have used tools; you have no tools available.
        Keep responses concise and hand results back to the main agent.
    """,
        tools=[],
    )


def get_fact_check_subagent() -> dict:
    current_time = datetime.now().astimezone(zoneinfo.ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    return {
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
        The current time is UTC+8: {current_time}
    """,
        "tools": agent_tools.web_tools,
        "model": model,
        # "middleware": [],
        # "interrupt_on": {},
    }


def get_research_subagent() -> dict:
    return _domain_subagent(
        name="research_agent",
        description="Search and summarize papers, web pages, encyclopedia entries, and online video metadata.",
        system_prompt="""
        You are a research subagent.
        Use research and web retrieval tools to find relevant external information.
        Prefer concise summaries with source context when available.
        Do not perform media generation, reminders, or chat history search.
    """,
        tools=_tools_for("research"),
    )


def get_astro_subagent() -> dict:
    return _domain_subagent(
        name="astro_agent",
        description="Handle astronomy, space weather, satellite imagery, rocket launch, and comet queries.",
        system_prompt="""
        You are an astronomy and space environment subagent.
        Use the astronomy, satellite, space weather, and launch tools for domain-specific data.
        Explain observations in plain language and include timestamps or data source context when returned by tools.
    """,
        tools=_tools_for("astro"),
    )


def get_earth_subagent() -> dict:
    return _domain_subagent(
        name="earth_agent",
        description="Handle weather, radar, and earthquake information requests.",
        system_prompt="""
        You are an earth information subagent.
        Use weather, radar, and earthquake tools to answer location and event questions.
        Be explicit about locations, times, and uncertainty when tool outputs include them.
    """,
        tools=_tools_for("earth"),
    )


def get_media_subagent() -> dict:
    return _domain_subagent(
        name="media_agent",
        description="Create images or videos from user prompts and available reference media.",
        system_prompt="""
        You are a media generation subagent.
        Use image and video generation tools when the user asks to create or transform media.
        Return the tool result clearly and do not use adapter/send tools directly.
    """,
        tools=_tools_for("media"),
    )


def get_memory_subagent() -> dict:
    return _domain_subagent(
        name="memory_agent",
        description="Search and summarize stored chat history for the current conversation scope.",
        system_prompt="""
        You are a chat history memory subagent.
        Use message summary and search tools to answer questions about stored chat records.
        Respect the current group or private-message scope enforced by the tools.
    """,
        tools=_tools_for("memory"),
    )


def get_divination_subagent() -> dict:
    return _domain_subagent(
        name="divination_agent",
        description="Handle tarot and I Ching divination requests.",
        system_prompt="""
        You are a divination subagent.
        Use tarot and I Ching tools only when the user explicitly asks for divination, spreads, hexagrams, or readings.
        Keep results framed as entertainment or cultural interpretation rather than factual prediction.
    """,
        tools=_tools_for("divination"),
    )


def get_external_subagent() -> dict:
    return _domain_subagent(
        name="external_agent",
        description="Use externally configured MCP tools when no local domain subagent fits the request.",
        system_prompt="""
        You are an external tools subagent.
        Use MCP-provided tools for external services that are not covered by local domain agents.
        Summarize tool results and hand them back to the main agent.
    """,
        tools=_tools_for("external"),
    )


def get_domain_subagents() -> list[dict]:
    return [
        get_general_purpose_subagent(),
        get_fact_check_subagent(),
        get_research_subagent(),
        get_astro_subagent(),
        get_earth_subagent(),
        get_media_subagent(),
        get_memory_subagent(),
        get_divination_subagent(),
        get_external_subagent(),
    ]
