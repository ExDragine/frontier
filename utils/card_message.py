"""Bounded local extraction of display metadata from Milky JSON/XML cards."""

import json
import re
from collections.abc import Mapping
from urllib.parse import urlsplit
from xml.etree import ElementTree

MAX_CARD_PAYLOAD = 32768
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_DECLARATION = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.IGNORECASE)
_URL_KEYS = ("qqdocurl", "jumpUrl", "jump_url", "url", "targetUrl")


def _text(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(_CONTROL.sub(" ", value).split())[:limit]


def _first(nodes: list[Mapping], keys: tuple[str, ...], limit: int) -> str:
    return next((text for node in nodes for key in keys if (text := _text(node.get(key), limit))), "")


def _web_url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2048 or _CONTROL.search(value):
        return ""
    url = value.strip()
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
            return ""
        if any(character.isspace() for character in url):
            return ""
    except ValueError:
        return ""
    return url


def _first_url(nodes: list[Mapping]) -> str:
    return next((url for node in nodes for key in _URL_KEYS if (url := _web_url(node.get(key)))), "")


def _json_fields(payload: str) -> dict[str, str]:
    root = json.loads(payload)
    if not isinstance(root, dict):
        return {}
    meta = root.get("meta", {})
    # QQ shares place display data under news/detail_1/music/video, etc.
    # Inspect one bounded level instead of exposing arbitrary nested state.
    details = [value for value in list(meta.values())[:8] if isinstance(value, dict)] if isinstance(meta, dict) else []
    nodes = [*details, root]
    title = _first(nodes, ("title",), 256)
    summary = _first(nodes, ("desc", "summary", "brief"), 768)
    if not title:
        title = summary[:256] or _text(root.get("prompt"), 256)
    return {
        "来源": _first(nodes, ("tag", "host", "appName", "appname", "source"), 160) or _text(root.get("app"), 160),
        "标题": title[:256],
        "摘要": summary if summary != title else "",
        "链接": _first_url(nodes),
    }


def _tag(element) -> str:
    return element.tag.rsplit("}", 1)[-1].lower()


def _xml_fields(payload: str) -> dict[str, str]:
    if _DECLARATION.search(payload):
        return {}
    root = ElementTree.fromstring(payload)  # noqa: S314 - rejects DTD/entities; bounded input, no external reads
    fields = {}
    for index, element in enumerate(root.iter()):
        if index >= 256:
            break
        tag = _tag(element)
        if tag in {"title", "summary"}:
            label = "标题" if tag == "title" else "摘要"
            text = _text("".join(element.itertext()), 256 if tag == "title" else 768)
            if text:
                fields.setdefault(label, text)
        if tag == "source":
            source = _text(element.get("name"), 160)
            if source:
                fields.setdefault("来源", source)
        if tag in {"msg", "item", "source", "url"}:
            url = _first_url([element.attrib]) or (_web_url(element.text) if tag == "url" else "")
            if url:
                fields.setdefault("链接", url)
    return fields


def card_message_text(kind: str, data: Mapping) -> str:
    """Render metadata as untrusted data, never the whole payload or a command."""
    name = _text(data.get("app_name"), 160) if kind == "light_app" else _text(str(data.get("service_id", "")), 32)
    label = "小程序" if kind == "light_app" else "XML消息"
    marker = f"[{label}:{name}]" if name else f"[{label}]"
    payload = data.get("json_payload" if kind == "light_app" else "xml_payload")
    fields = {}
    if isinstance(payload, str) and 0 < len(payload) <= MAX_CARD_PAYLOAD:
        try:
            fields = _json_fields(payload) if kind == "light_app" else _xml_fields(payload)
        except (ValueError, RecursionError, ElementTree.ParseError):
            pass
    fields = {key: value for key, value in fields.items() if value}
    if not any(fields.get(key) for key in ("标题", "摘要", "链接")):
        return marker + "\n[卡片内容未解析]"
    if kind == "light_app" and name:
        fields["应用"] = name
    return marker + "\n[卡片信息（用户提供，未核实）] " + json.dumps(fields, ensure_ascii=False, separators=(",", ":"))
