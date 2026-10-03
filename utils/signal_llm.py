import json
from typing import Any

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from utils.configs import EnvConfig
from utils.llm_factory import (
    create_llm,
    provider_decision_extra_body,
    provider_signal_extra_body,
    structured_output_options,
)

_JSON_MODE_INSTRUCTION = (
    "Return ONLY valid JSON matching the requested schema. Do not wrap the JSON in markdown or include explanations."
)

# 这两种策略把完整 schema 放进提示词：json_mode 仍请求供应商的 JSON 模式，
# text_json 只依赖文本输出并本地解析。
_PROMPT_SCHEMA_METHODS = frozenset({"json_mode", "text_json"})


def _message_text(message: Any) -> str:
    """Normalize LangChain's text or structured content into plain text."""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content if isinstance(content, list) else []:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "".join(parts)


def _parse_text_json(schema: type[BaseModel], message: Any) -> Any:
    """Parse JSON out of a plain text reply, tolerating fences and surrounding prose."""
    parser = PydanticOutputParser(pydantic_object=schema)
    text = _message_text(message)
    try:
        return parser.parse(text)
    except OutputParserException:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise
        return parser.parse(text[start : end + 1])


class DecisionLLM:
    """Low-overhead LLM wrapper for provider-aware structured decisions."""

    _model_attribute = "DECISION_MODEL"
    _provider_attribute = "DECISION_MODEL_PROVIDER"
    _request_tag = "frontier:decision"
    _extra_body_resolver = staticmethod(provider_decision_extra_body)

    def __init__(
        self,
        *,
        model: str | None = None,
        provider: str | None = None,
        max_retries: int = 2,
        timeout: int = 30,
    ):
        self.model = model or getattr(EnvConfig, self._model_attribute)
        self.provider = getattr(EnvConfig, self._provider_attribute) if provider is None else provider
        self.max_retries = max_retries
        self.timeout = timeout

    def _llm_kwargs(
        self,
        *,
        temperature: float | None = None,
        model_kwargs: dict | None = None,
        extra_body: dict | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "streaming": False,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "provider": self.provider,
            "tags": [self._request_tag],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if model_kwargs is not None:
            kwargs["model_kwargs"] = model_kwargs
        # provider 级 decision 请求参数（如关闭思考模式）优先，调用点显式传入的覆盖它。
        payload = self._extra_body_resolver(self.model, self.provider)
        if extra_body:
            payload.update(extra_body)
        if payload:
            kwargs["extra_body"] = payload
        return kwargs

    @staticmethod
    def _system_prompt(system_prompt: str, schema: type[BaseModel], *, method: str) -> str:
        system_prompt = system_prompt.strip()
        if method not in _PROMPT_SCHEMA_METHODS:
            return system_prompt or "按指定结构返回判断结果。"
        instruction = _JSON_MODE_INSTRUCTION + "\nJSON Schema:\n" + json.dumps(schema.model_json_schema(), ensure_ascii=False)
        return f"{system_prompt}\n\n{instruction}".strip()

    async def structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        *,
        method: str | None = None,
        temperature: float | None = None,
        model_kwargs: dict | None = None,
        extra_body: dict | None = None,
    ) -> Any:
        llm = create_llm(**self._llm_kwargs(temperature=temperature, model_kwargs=model_kwargs, extra_body=extra_body))
        options = structured_output_options(self.model, self.provider, llm, method=method)
        messages = [
            ("system", self._system_prompt(system_prompt, schema, method=options["method"])),
            ("human", user_prompt),
        ]
        if options["method"] == "text_json":
            # 思考模式等路由拒绝强制 tool_choice 和 response_format，
            # 保持普通文本请求，由 Pydantic 在本地校验。
            result = _parse_text_json(schema, await llm.ainvoke(messages))
        else:
            structured_llm = llm.with_structured_output(schema, **options)
            result = await structured_llm.ainvoke(messages)
        return schema.model_validate(result)


class SignalLLM(DecisionLLM):
    """Deprecated compatibility wrapper for the former Signal name."""

    _model_attribute = "SIGNAL_MODEL"
    _provider_attribute = "SIGNAL_MODEL_PROVIDER"
    _request_tag = "frontier:signal"
    _extra_body_resolver = staticmethod(provider_signal_extra_body)


async def decision_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[BaseModel],
    *,
    temperature: float | None = None,
    model_kwargs: dict | None = None,
    extra_body: dict | None = None,
    method: str | None = None,
) -> Any:
    """Run one structured decision using the configured decision model."""

    return await DecisionLLM().structured(
        system_prompt,
        user_prompt,
        schema,
        method=method,
        temperature=temperature,
        model_kwargs=model_kwargs,
        extra_body=extra_body,
    )


async def signal_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[BaseModel],
    *,
    temperature: float | None = None,
    model_kwargs: dict | None = None,
    extra_body: dict | None = None,
    method: str | None = None,
) -> Any:
    """Deprecated compatibility entry point.

    A normal runtime reload keeps the legacy aliases equal to the decision
    settings, so old imports still emit decision-tagged requests.  Tests and
    external integrations that intentionally override only the old settings
    continue to exercise the legacy wrapper.
    """

    model_matches_decision = getattr(EnvConfig, "SIGNAL_MODEL", None) == getattr(EnvConfig, "DECISION_MODEL", None)
    provider_matches_decision = getattr(EnvConfig, "SIGNAL_MODEL_PROVIDER", None) == getattr(
        EnvConfig, "DECISION_MODEL_PROVIDER", None
    )
    client = DecisionLLM if model_matches_decision and provider_matches_decision else SignalLLM
    return await client().structured(
        system_prompt,
        user_prompt,
        schema,
        method=method,
        temperature=temperature,
        model_kwargs=model_kwargs,
        extra_body=extra_body,
    )
