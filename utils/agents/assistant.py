"""Lightweight Agent helper used by scheduled jobs and tools."""

import json
import re
from typing import Any, Literal

from langchain.agents import create_agent
from pydantic import ValidationError

from utils.configs import EnvConfig
from utils.llm_factory import create_llm, model_supports, provider_uses_responses_api
from utils.message import extract_message_text

from .inputs import build_user_content


def configured_model_route(
    model: str,
    role: Literal["basic", "signal", "advanced"] | None = None,
) -> dict[str, str]:
    if role == "basic":
        return {"provider": EnvConfig.BASIC_MODEL_PROVIDER}
    if role == "signal":
        return {"provider": EnvConfig.SIGNAL_MODEL_PROVIDER}
    if role == "advanced":
        return {"provider": EnvConfig.ADVAN_MODEL_PROVIDER}
    if model == EnvConfig.BASIC_MODEL:
        return {"provider": EnvConfig.BASIC_MODEL_PROVIDER}
    if model == EnvConfig.ADVAN_MODEL:
        return {"provider": EnvConfig.ADVAN_MODEL_PROVIDER}
    if model == EnvConfig.SIGNAL_MODEL:
        return {"provider": EnvConfig.SIGNAL_MODEL_PROVIDER}
    return {}


def json_document_candidates(text: str, *, prefer_object: bool = False) -> list[str]:
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        text = fenced_match.group(1).strip()

    decoder = json.JSONDecoder()
    candidates = []
    for index, char in enumerate(text):
        if char not in ("{" if prefer_object else "{["):
            continue
        try:
            _, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        candidates.append(text[index : index + end])
    return candidates or [text]


def parse_structured_response_from_messages(messages: list, response_format):
    for message in reversed(messages):
        if getattr(message, "type", None) != "ai":
            continue
        text = extract_message_text(message).strip()
        if not text:
            continue
        if hasattr(response_format, "model_validate_json"):
            last_error = None
            for candidate in json_document_candidates(text, prefer_object=True):
                try:
                    return response_format.model_validate_json(candidate)
                except ValidationError as exc:
                    last_error = exc
            if last_error is not None:
                raise last_error
        break
    raise KeyError("structured_response")


async def assistant_agent(
    system_prompt: str = "",
    user_prompt: str = "",
    use_model: str | None = None,
    model_role: Literal["basic", "signal", "advanced"] | None = None,
    tools=None,
    response_format=None,
    middleware=None,
    images: list[bytes] | None = None,
    reasoning_effort: str | None = None,
    temperature: float | None = None,
    model_kwargs: dict | None = None,
) -> Any:
    if use_model is None:
        use_model = EnvConfig.BASIC_MODEL
        model_role = model_role or "basic"
    route = configured_model_route(use_model, model_role)
    llm_kwargs: dict[str, Any] = {
        "model": use_model,
        "streaming": False,
        "max_retries": 2,
        "timeout": 300,
        **route,
    }
    if reasoning_effort is not None and provider_uses_responses_api(use_model, route.get("provider")):
        llm_kwargs["reasoning_effort"] = reasoning_effort
    if temperature is not None:
        llm_kwargs["temperature"] = temperature
    if model_kwargs is not None:
        llm_kwargs["model_kwargs"] = model_kwargs
    model = create_llm(**llm_kwargs)
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware or [],
        response_format=response_format,
        debug=EnvConfig.AGENT_DEBUG_MODE,
    )
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": build_user_content(
                        user_prompt,
                        images,
                        supports_vision=model_supports(use_model, "vision", role=model_role),
                    ),
                }
            ]
        }
    )
    if response_format:
        if "structured_response" in result:
            return result["structured_response"]
        return parse_structured_response_from_messages(result.get("messages", []), response_format)
    content = ""
    for message in result["messages"]:
        if message.type == "ai" and message.text:
            content += str(message.text)
    return content
