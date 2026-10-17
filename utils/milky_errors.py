"""Bounded, redacted Milky API diagnostics for server logs only."""

import json
import re
from collections.abc import Iterator

from nonebot.adapters.milky.exception import ActionFailed

_HEADERS = re.compile(r'''(?im)["']?\b(?:authorization|proxy-authorization|cookie|set-cookie)["']?\s*[:=]\s*[^\r\n]*''')
_SECRETS = re.compile(
    r'''(?ix)(["']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|password|passwd|session[_-]?id)["']?\s*[:=]\s*)'''
    r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;}\]]+)'''
)
_PAYLOAD = re.compile(
    r'''(?is)["']?\b(?:text|content|prompt|raw_message|segments|message_chain|message|data|request|params|args|body)["']?\s*[:=]\s*.*'''
)
_URLS = re.compile(r'''(?i)\b(?:https?|wss?|file)://[^\s<>"']+''')
_PATHS = re.compile(r'''(?:[A-Za-z]:[\\/]|(?<!\w)/)[^\s<>"',;}\]]+''')
_TOKENS = re.compile(r"(?i)\b(?:bearer\s+[^\s,;}\]]+|sk-[a-z0-9_-]+)")
_EMAILS = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b")
_IDENTIFIERS = re.compile(r"(?<!\w)\d{5,}(?!\w)")


def _sensitive_strings(value: object, depth: int = 0) -> Iterator[str]:
    if isinstance(value, str):
        if value:
            yield value
    elif depth < 8:
        if isinstance(value, dict):
            for item in value.values():
                yield from _sensitive_strings(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from _sensitive_strings(item, depth + 1)


def _redact_message(message: str, sensitive: object) -> str:
    # Platform errors can echo the submitted text, including JSON-escaped text.
    for value in sorted(set(_sensitive_strings(sensitive)), key=len, reverse=True):
        variants = {value, json.dumps(value, ensure_ascii=True)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1]}
        for variant in variants:
            message = message.replace(variant, "[content]")
            if len(variant) > 16:
                # Some implementations return only the beginning of a rejected
                # long message. Drop that echo and its tail as well.
                message = re.sub(re.escape(variant[:8]) + r".*", "[content]", message, flags=re.DOTALL)
    message = _HEADERS.sub("[credentials]", message)
    message = _SECRETS.sub(r"\1[redacted]", message)
    message = _PAYLOAD.sub("[payload]", message)
    message = _URLS.sub("[url]", message)
    message = _PATHS.sub("[path]", message)
    message = _TOKENS.sub("[credentials]", message)
    message = _EMAILS.sub("[email]", message)
    message = _IDENTIFIERS.sub("[id]", message)
    message = " ".join("".join(char if char.isprintable() else " " for char in message).split())
    return message[:511] + "…" if len(message) > 512 else message


def milky_error_details(exc: BaseException, *, sensitive: object = None) -> str:
    """Extract only known response fields; never stringify the raw exception/data."""
    seen = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen and len(seen) < 8:
        if isinstance(current, ActionFailed):
            break
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    if not isinstance(current, ActionFailed) or not isinstance(current.info, dict):
        return ""

    info = current.info
    status = info.get("status")
    status = status if isinstance(status, str) and status in {"ok", "failed"} else "unknown"
    retcode = info.get("retcode")
    if not (type(retcode) is int or isinstance(retcode, str) and re.fullmatch(r"-?\d{1,12}", retcode)):
        retcode = "unknown"
    message = next((info[key] for key in ("message", "msg", "wording") if isinstance(info.get(key), str)), "")
    safe_message = json.dumps(_redact_message(message, sensitive), ensure_ascii=False)
    return f" milky_status={status} milky_retcode={retcode} milky_message={safe_message}"
