"""A small, static Markdown component dialect compiled to the existing UI schema.

No Vue/JSX evaluation: attributes are literal values and every node is validated.
The block rule runs alongside Markdown's fence/list rules, so examples stay code.
"""

from __future__ import annotations

import html
import json
import re
import shlex
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock
from markdown_it.token import Token
from pydantic import ValidationError

from utils.markdown_rich import (
    MAX_RICH_BLOCK_CHARS,
    MAX_UI_DEPTH,
    UIBlock,
    parse_rich_block,
    rich_block_placeholder,
)

_LAYOUTS = {"card", "section", "grid", "row", "column"}
_MEDIA = {"image", "map", "iframe"}
_COMPONENTS = _LAYOUTS | _MEDIA | {"steps"}
_OPEN = re.compile(r"^(:{2,})[ \t]*([a-z][a-z0-9-]*)(.*)$")
_CLOSE = re.compile(r"^:{2,}[ \t]*$")
_FENCE = re.compile(r"^(`{3,}|~{3,})(.*)$")
_CANDIDATE = re.compile(r":{2,}[ \t]*(?:" + "|".join(sorted(_COMPONENTS)) + r")\b")
_NUMBER_FIELDS = {"columns", "height", "latitude", "longitude", "zoom"}
_DEPTH_KEY = "frontier_component_depth"
_RULE_NAME = "frontier_component"


def _plain_parser() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"]).disable("image")


def _attributes(source: str) -> dict[str, Any]:
    source = source.strip()
    if not source:
        return {}
    if not (source.startswith("{") and source.endswith("}")):
        raise ValueError("component attributes require braces")
    values: dict[str, Any] = {}
    for attribute in shlex.split(source[1:-1], comments=False):
        key, separator, value = attribute.partition("=")
        if not separator or not re.fullmatch(r"[a-z][a-z_]*", key):
            raise ValueError("component attributes must be literal key=value pairs")
        if key in values or key in {"type", "children", "items", "config", "rendered"}:
            raise ValueError("duplicate or reserved component attribute")
        if key in _NUMBER_FIELDS:
            number = json.loads(value)
            if isinstance(number, bool) or not isinstance(number, int | float):
                raise ValueError("numeric component attribute required")
            values[key] = number
        elif key == "full_page":
            if value not in {"true", "false"}:
                raise ValueError("full_page must be true or false")
            values[key] = value == "true"
        else:
            values[key] = value
    return values


def _block_end(state: StateBlock, start: int, end: int) -> tuple[int, bool]:
    """Balance component markers, ignoring fenced and indented code content."""
    nesting = 1
    fence: tuple[str, int] | None = None
    for line in range(start + 1, end):
        if state.sCount[line] < state.blkIndent and not state.isEmpty(line):
            return line, False
        if state.is_code_block(line):
            continue
        source = state.src[state.bMarks[line] + state.tShift[line] : state.eMarks[line]]
        marker = _FENCE.fullmatch(source)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            continue
        if marker and (marker[1][0] != "`" or "`" not in marker[2]):
            fence = marker[1][0], len(marker[1])
            continue
        if _OPEN.fullmatch(source):
            nesting += 1
        elif _CLOSE.fullmatch(source):
            nesting -= 1
            if not nesting:
                return line, True
    return end, False


def _fence_nodes(token: Token) -> list[dict[str, Any]] | None:
    kind = token.info.strip()
    if kind == "mermaid" and len(token.content) <= 2000:
        return [{"type": "mermaid", "text": token.content}]
    # These blocks use the same validated JSON contract as the other rich
    # blocks.  Keeping the language tag explicit prevents them from falling
    # through to an opaque `json` code block in the renderer.
    if kind not in {"chart", "stats", "timeline", "ui", "three", "flow"}:
        return None
    try:
        config = parse_rich_block(kind, token.content).model_dump(mode="json", exclude_none=True, exclude_unset=True)
        if kind == "ui":
            return config["children"]
        # chart/stats/timeline are wrapped in a config object for the
        # renderer; media-style rich nodes already match UIComponent directly.
        if kind in {"three", "flow"}:
            return [config]
        return [{"type": kind, "config": config}]
    except (ValidationError, TypeError, ValueError):
        return None  # Keep invalid data as Markdown code, alongside valid siblings.


def _markdown_children(md: MarkdownIt, source: str, env: dict[str, Any]) -> list[dict[str, Any]]:
    lines = source.splitlines(keepends=True)
    nodes: list[dict[str, Any]] = []
    cursor = 0

    def prose(stop: int) -> None:
        text = "".join(lines[cursor:stop]).strip()
        if text:
            nodes.append({"type": "prose", "text": text})

    for token in md.parse(source, env):
        if token.level or token.map is None:
            continue
        replacements = None
        if token.type == _RULE_NAME:
            replacements = [token.meta.get("node") or {"type": "prose", "text": token.content}]
        elif token.type == "fence":
            replacements = _fence_nodes(token)
        if replacements is not None:
            prose(token.map[0])
            nodes.extend(replacements)
            cursor = token.map[1]
    prose(len(lines))
    return nodes


def _step_items(md: MarkdownIt, source: str, env: dict[str, Any]) -> list[dict[str, str]]:
    tokens = md.parse(source, env)
    if not tokens or tokens[0].type != "ordered_list_open" or tokens[-1].type != "ordered_list_close":
        raise ValueError("steps require one Markdown ordered list")
    if any(token.level == 0 and token.type not in {"ordered_list_open", "ordered_list_close"} for token in tokens):
        raise ValueError("steps require one Markdown ordered list")
    lines = source.splitlines()
    items = []
    for token in tokens:
        if token.type != "list_item_open" or token.level != 1 or token.map is None:
            continue
        item = lines[token.map[0] : token.map[1]]
        marker = re.match(r"^ {0,3}\d+[.)][ \t]+", item[0])
        if marker is None:
            raise ValueError("invalid step marker")
        indent = marker.end()
        body = [item[0][indent:]]
        body.extend(line[indent:] if line[:indent].isspace() else line for line in item[1:])
        items.append({"type": "prose", "text": "\n".join(body).strip()})
    return items


def _component_rule(state: StateBlock, start: int, end: int, silent: bool) -> bool:
    if state.is_code_block(start):
        return False
    header = state.src[state.bMarks[start] + state.tShift[start] : state.eMarks[start]]
    match = _OPEN.fullmatch(header)
    if match is None or match[2] not in _COMPONENTS:
        return False
    if silent:
        return True
    stop, closed = _block_end(state, start, end)
    state.line = stop + int(closed)
    body = state.getLines(start + 1, stop, state.sCount[start], True)
    token = state.push(_RULE_NAME, "", 0)
    token.block = True
    token.map = [start, state.line]
    token.content = body
    token.meta = {"name": match[2]}
    depth = state.env.get(_DEPTH_KEY, 0)
    try:
        if not closed or depth >= MAX_UI_DEPTH or len(header) + len(body) > MAX_RICH_BLOCK_CHARS:
            raise ValueError("unclosed or oversized component")
        attrs = _attributes(match[3])
        name = match[2]
        node: dict[str, Any] = {"type": name, **attrs}
        env = {**state.env, _DEPTH_KEY: depth + 1}
        if name in _LAYOUTS:
            if name == "card":
                node.setdefault("variant", "muted")
            node["children"] = _markdown_children(state.md, body, env)
        elif name == "steps":
            node["items"] = _step_items(state.md, body, env)
        elif body.strip():
            raise ValueError("media components have no body; use caption")
        validated = UIBlock.model_validate({"children": [node]})
        token.meta["node"] = validated.model_dump(mode="json", exclude_none=True, exclude_unset=True)["children"][0]
    except (ValidationError, TypeError, ValueError, RecursionError):
        # Recover the prose, rather than turn a whole answer into a JSON/code wall.
        # The plain parser also leaves nested invalid syntax inert.
        pass
    return True


def markdown_components_plugin(md: MarkdownIt, *, plain_text: bool = False) -> None:
    def render(_renderer, tokens, index, options, env) -> str:
        token = tokens[index]
        node = token.meta.get("node")
        if node is None:
            if token.meta["name"] in _MEDIA and not token.content.strip():
                return "<p>素材未能展示。</p>"
            return _plain_parser().render(token.content)
        if plain_text:
            labels = [node.get("title"), node.get("alt")]
            content = "".join(f"<p>{html.escape(label)}</p>" for label in labels if label)
            content += md.render(token.content, env)
            if node["type"] == "map":
                content += f'<p>{node["latitude"]}, {node["longitude"]}</p>'
            content += "".join(
                f"<p>{html.escape(str(node[key]))}</p>" for key in ("caption", "url", "footer") if node.get(key)
            )
            return content
        return rich_block_placeholder("ui", UIBlock.model_validate({"children": [node]}))

    md.block.ruler.before("fence", _RULE_NAME, _component_rule, {"alt": ["paragraph", "reference", "blockquote", "list"]})
    md.add_render_rule(_RULE_NAME, render)


def has_markdown_components(source: str) -> bool:
    """Recognize real components, excluding syntax examples inside Markdown code."""
    # Markdown containers can prefix a component with `>` or a list marker.
    # The parser, rather than this cheap prefilter, decides whether it is a block.
    if not _CANDIDATE.search(source):
        return False
    md = _plain_parser().use(markdown_components_plugin)
    return any(token.type == _RULE_NAME and token.meta.get("node") for token in md.parse(source))
