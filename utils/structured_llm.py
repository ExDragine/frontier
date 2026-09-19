"""Provider-aware structured calls without Agent loops or Signal-specific settings."""

import json
import re

from pydantic import BaseModel


def parse_json_response(schema: type[BaseModel], message):
    content = getattr(message, "content", message)
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else part
                          for part in content if isinstance(part, (str, dict)))
    if not isinstance(content, str) or len(content) > 150_000:
        raise ValueError("invalid structured response size or type")
    text = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    return schema.model_validate_json(fenced.group(1) if fenced else text)


async def structured_call(*, model: str, provider: str, schema: type[BaseModel],
                          system_prompt: str, user_prompt: str, timeout: int,
                          extra_body: dict | None = None, tag: str = "frontier:news"):
    # Lazy imports let pure news validation/tests run without loading the Agent plugin.
    from utils.llm_factory import create_llm, structured_output_options

    kwargs = dict(model=model, provider=provider, streaming=False, max_retries=0,
                  timeout=timeout, max_tokens=8192, tags=[tag])
    if extra_body:
        kwargs["extra_body"] = extra_body
    llm = create_llm(**kwargs)
    options = structured_output_options(model, provider, llm)
    method = options["method"]
    if method in {"text_json", "json_mode"}:
        system_prompt += "\nReturn only valid JSON conforming to:\n" + json.dumps(schema.model_json_schema(), ensure_ascii=False)
    messages = [("system", system_prompt), ("human", user_prompt)]
    if method == "text_json":
        return parse_json_response(schema, await llm.ainvoke(messages))
    result = await llm.with_structured_output(schema, **options).ainvoke(messages)
    return schema.model_validate(result)
