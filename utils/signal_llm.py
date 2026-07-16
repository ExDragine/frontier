from typing import Any

from pydantic import BaseModel

from utils.configs import EnvConfig
from utils.llm_factory import create_llm

_JSON_MODE_INSTRUCTION = (
    "Return ONLY valid JSON matching the requested schema. Do not wrap the JSON in markdown or include explanations."
)


class SignalLLM:
    """Low-overhead LLM wrapper for routing and structured decisions."""

    def __init__(
        self,
        *,
        model: str | None = None,
        provider: str | None = None,
        max_retries: int = 2,
        timeout: int = 30,
    ):
        self.model = model or EnvConfig.SIGNAL_MODEL
        self.provider = EnvConfig.SIGNAL_MODEL_PROVIDER if provider is None else provider
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
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if model_kwargs is not None:
            kwargs["model_kwargs"] = model_kwargs
        if extra_body is not None:
            kwargs["extra_body"] = extra_body
        return kwargs

    @staticmethod
    def _system_prompt(system_prompt: str) -> str:
        system_prompt = system_prompt.strip()
        if not system_prompt:
            return _JSON_MODE_INSTRUCTION
        return f"{system_prompt}\n\n{_JSON_MODE_INSTRUCTION}"

    async def structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        *,
        method: str = "json_mode",
        temperature: float | None = None,
        model_kwargs: dict | None = None,
        extra_body: dict | None = None,
    ) -> Any:
        llm = create_llm(**self._llm_kwargs(temperature=temperature, model_kwargs=model_kwargs, extra_body=extra_body))
        structured_llm = llm.with_structured_output(schema, method=method)
        return await structured_llm.ainvoke(
            [
                ("system", self._system_prompt(system_prompt)),
                ("human", user_prompt),
            ]
        )


async def signal_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[BaseModel],
    *,
    temperature: float | None = None,
    model_kwargs: dict | None = None,
    extra_body: dict | None = None,
    method: str = "json_mode",
) -> Any:
    return await SignalLLM().structured(
        system_prompt,
        user_prompt,
        schema,
        method=method,
        temperature=temperature,
        model_kwargs=model_kwargs,
        extra_body=extra_body,
    )
