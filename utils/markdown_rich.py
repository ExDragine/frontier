from __future__ import annotations

import html
import json
import logging
import re
from typing import Annotated, Any, Literal

from markdown_it import MarkdownIt
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, model_validator

logger = logging.getLogger(__name__)

MAX_RICH_BLOCK_CHARS = 50_000
MAX_CHART_POINTS = 200
MAX_CHART_SERIES = 8
MAX_PIE_ITEMS = 12
MAX_STAT_ITEMS = 12
MAX_TIMELINE_ITEMS = 50
MAX_UI_COMPONENTS = 80
MAX_UI_DEPTH = 6

ShortText = Annotated[str, Field(max_length=200)]
LabelText = Annotated[str, Field(max_length=80)]
LongText = Annotated[str, Field(max_length=2_000)]

_RICH_FENCE_RE = re.compile(
    r'<pre><code class="language-(?P<kind>chart|stats|timeline|ui)">(?P<body>.*?)</code></pre>',
    re.DOTALL | re.IGNORECASE,
)


class _RichModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ChartSeries(_RichModel):
    name: LabelText
    values: list[float] = Field(min_length=1, max_length=MAX_CHART_POINTS)


class PieItem(_RichModel):
    name: LabelText
    value: float


class ChartBlock(_RichModel):
    type: Literal["bar", "line", "pie"]
    title: ShortText | None = None
    unit: LabelText | None = None
    labels: list[LabelText] = Field(default_factory=list, max_length=MAX_CHART_POINTS)
    series: list[ChartSeries] = Field(default_factory=list, max_length=MAX_CHART_SERIES)
    data: list[PieItem] = Field(default_factory=list, max_length=MAX_PIE_ITEMS)
    show_legend: bool = True

    @model_validator(mode="after")
    def validate_shape(self) -> ChartBlock:
        if self.type == "pie":
            if not self.data or self.labels or self.series:
                raise ValueError("pie chart requires data only")
            if any(item.value < 0 for item in self.data):
                raise ValueError("pie values must be non-negative")
            if not any(item.value > 0 for item in self.data):
                raise ValueError("pie chart requires at least one positive value")
            return self
        if not self.labels or not self.series or self.data:
            raise ValueError("bar/line chart requires labels and series")
        if any(len(item.values) != len(self.labels) for item in self.series):
            raise ValueError("series values length must match labels")
        return self


class StatItem(_RichModel):
    label: LabelText
    value: ShortText
    unit: LabelText | None = None
    detail: ShortText | None = None
    status: Literal["neutral", "success", "warning", "danger"] = "neutral"


class StatsBlock(_RichModel):
    title: ShortText | None = None
    columns: int = Field(default=3, ge=1, le=4)
    variant: Literal["plain", "cards"] = "plain"
    items: list[StatItem] = Field(min_length=1, max_length=MAX_STAT_ITEMS)


class TimelineItem(_RichModel):
    time: LabelText
    title: ShortText
    content: LongText | None = None
    status: Literal["neutral", "success", "warning", "danger"] = "neutral"


class TimelineBlock(_RichModel):
    title: ShortText | None = None
    items: list[TimelineItem] = Field(min_length=1, max_length=MAX_TIMELINE_ITEMS)


class UIText(_RichModel):
    type: Literal["text", "heading", "code", "mermaid"]
    text: LongText
    variant: Literal["body", "lead", "muted", "small"] = "body"

    @model_validator(mode="after")
    def validate_variant(self) -> UIText:
        if self.type != "text" and "variant" in self.model_fields_set:
            raise ValueError("text variants are only supported by text")
        return self


class UIProse(_RichModel):
    type: Literal["prose"]
    text: Annotated[str, Field(max_length=MAX_RICH_BLOCK_CHARS)]


class UIBadge(_RichModel):
    type: Literal["badge"]
    text: LabelText
    status: Literal["neutral", "success", "warning", "danger"] = "neutral"
    variant: Literal["secondary", "outline", "solid"] = "secondary"


class UILink(_RichModel):
    type: Literal["link"]
    label: LabelText
    url: HttpUrl


class UICallout(_RichModel):
    type: Literal["alert", "callout"]
    title: ShortText | None = None
    text: LongText
    status: Literal["neutral", "success", "warning", "danger"] = "neutral"


class UILayout(_RichModel):
    type: Literal["row", "column", "grid"]
    columns: int = Field(default=2, ge=1, le=3)
    children: list[UIComponent] = Field(min_length=1, max_length=12)
    gap: Literal["sm", "md", "lg"] = "md"

    @model_validator(mode="after")
    def validate_columns(self) -> UILayout:
        if self.type != "grid" and "columns" in self.model_fields_set:
            raise ValueError("columns is only supported by grid")
        return self


class UICard(_RichModel):
    type: Literal["card"]
    title: ShortText | None = None
    description: LongText | None = None
    eyebrow: LabelText | None = None
    footer: ShortText | None = None
    variant: Literal["outline", "muted", "ghost"] = "outline"
    color: Literal["neutral", "blue", "emerald", "violet", "amber", "rose", "cyan"] = "neutral"
    children: list[UIComponent] = Field(min_length=1, max_length=12)


class UISection(_RichModel):
    type: Literal["section"]
    title: ShortText | None = None
    description: LongText | None = None
    eyebrow: LabelText | None = None
    children: list[UIComponent] = Field(min_length=1, max_length=12)


class UIItem(_RichModel):
    title: ShortText
    description: LongText | None = None
    meta: LabelText | None = None


class UISteps(_RichModel):
    type: Literal["steps"]
    items: list[LongText | UIItem | UIProse] = Field(min_length=1, max_length=20)


class UIList(_RichModel):
    type: Literal["list"]
    variant: Literal["plain", "divided", "outline"] = "plain"
    items: list[UIItem] = Field(min_length=1, max_length=20)


class UIFact(_RichModel):
    label: LabelText
    value: LongText


class UIFacts(_RichModel):
    type: Literal["facts"]
    columns: int = Field(default=1, ge=1, le=2)
    items: list[UIFact] = Field(min_length=1, max_length=20)


class UISeparator(_RichModel):
    type: Literal["separator"]
    label: LabelText | None = None


class UIQuote(_RichModel):
    type: Literal["quote"]
    text: LongText
    attribution: ShortText | None = None


class UISource(_RichModel):
    label: ShortText
    url: HttpUrl
    description: ShortText | None = None


class UISources(_RichModel):
    type: Literal["sources"]
    items: list[UISource] = Field(min_length=1, max_length=12)


class UIProgress(_RichModel):
    type: Literal["progress"]
    label: LabelText
    value: float = Field(ge=0, le=100)
    detail: ShortText | None = None


class UITable(_RichModel):
    type: Literal["table"]
    columns: list[LabelText] = Field(min_length=1, max_length=8)
    rows: list[list[ShortText]] = Field(min_length=1, max_length=50)
    caption: ShortText | None = None
    column_widths: list[Annotated[int, Field(ge=1, le=12)]] | None = Field(default=None, min_length=1, max_length=8)

    @model_validator(mode="after")
    def validate_rows(self) -> UITable:
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("table rows must match columns")
        if self.column_widths is not None and len(self.column_widths) != len(self.columns):
            raise ValueError("table column widths must match columns")
        return self


class UIImage(_RichModel):
    type: Literal["image"]
    url: HttpUrl
    alt: ShortText
    caption: ShortText | None = None
    fit: Literal["contain", "cover"] = "contain"
    aspect: Literal["original", "landscape", "portrait", "square"] = "original"


class UIFrame(_RichModel):
    type: Literal["iframe"]
    url: HttpUrl
    title: ShortText
    height: int = Field(default=480, ge=200, le=1200)
    full_page: bool = True
    caption: ShortText | None = None


class UIMap(_RichModel):
    type: Literal["map"]
    latitude: float = Field(ge=-85, le=85)
    longitude: float = Field(ge=-180, le=180)
    zoom: int = Field(default=13, ge=2, le=18)
    height: int = Field(default=480, ge=200, le=1000)
    title: ShortText | None = None
    caption: ShortText | None = None


class UIChart(_RichModel):
    type: Literal["chart"]
    config: ChartBlock


class UIStats(_RichModel):
    type: Literal["stats"]
    config: StatsBlock


class UITimeline(_RichModel):
    type: Literal["timeline"]
    config: TimelineBlock


UIComponent = Annotated[
    UIText
    | UIProse
    | UIBadge
    | UILink
    | UICallout
    | UILayout
    | UICard
    | UISection
    | UISteps
    | UIList
    | UIFacts
    | UISeparator
    | UIQuote
    | UISources
    | UIProgress
    | UITable
    | UIImage
    | UIFrame
    | UIMap
    | UIChart
    | UIStats
    | UITimeline,
    Field(discriminator="type"),
]


class UIBlock(_RichModel):
    title: ShortText | None = None
    eyebrow: LabelText | None = None
    description: LongText | None = None
    children: list[UIComponent] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_capacity(self) -> UIBlock:
        pending = [(child, 1) for child in self.children]
        count = 0
        while pending:
            child, depth = pending.pop()
            count += 1
            if count > MAX_UI_COMPONENTS or depth > MAX_UI_DEPTH:
                raise ValueError("UI component count or depth limit exceeded")
            if isinstance(child, UILayout | UICard | UISection):
                pending.extend((item, depth + 1) for item in child.children)
            elif isinstance(child, UISteps):
                pending.extend((item, depth + 1) for item in child.items if isinstance(item, UIProse))
        return self


UIBlock.model_rebuild()


_RICH_MODELS: dict[str, type[_RichModel]] = {
    "chart": ChartBlock,
    "stats": StatsBlock,
    "timeline": TimelineBlock,
    "ui": UIBlock,
}


def rich_block_placeholder(kind: str, data: _RichModel) -> str:
    payload = data.model_dump(mode="json", exclude_none=True)
    if kind == "ui":
        # HTML is produced only by this parser, never accepted from model JSON.
        parser = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"]).disable("image")

        def compile_prose(node: dict[str, Any]) -> None:
            if node.get("type") == "prose":
                node["rendered"] = parser.render(node["text"])
            for child in node.get("children", []):
                compile_prose(child)
            for item in node.get("items", []):
                if isinstance(item, dict):
                    compile_prose(item)

        compile_prose(payload)
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    encoded = html.escape(serialized, quote=True)
    return f'<div class="md-rich-block" data-rich-kind="{kind}" data-rich-config="{encoded}"></div>'


def parse_rich_block(kind: str, source: str) -> _RichModel:
    if len(source) > MAX_RICH_BLOCK_CHARS:
        raise ValueError("rich block exceeds the character limit")
    return _RICH_MODELS[kind].model_validate(json.loads(source))


def render_rich_markdown_blocks(html_content: str) -> str:
    """将受控 JSON fenced block 转成可信占位节点；非法块保持为代码块。"""

    def replace(match: re.Match[str]) -> str:
        kind = match.group("kind").lower()
        source = html.unescape(match.group("body")).strip()
        if len(source) > MAX_RICH_BLOCK_CHARS:
            logger.warning("Markdown %s 富内容块超过 %s 字符，保留为代码块", kind, MAX_RICH_BLOCK_CHARS)
            return match.group(0)
        try:
            data = parse_rich_block(kind, source)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            logger.warning("Markdown %s 富内容块校验失败，保留为代码块: %s", kind, exc)
            return match.group(0)
        return rich_block_placeholder(kind, data)

    return _RICH_FENCE_RE.sub(replace, html_content)
