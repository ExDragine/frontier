from __future__ import annotations

import html
import json
import logging
import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

logger = logging.getLogger(__name__)

MAX_RICH_BLOCK_CHARS = 50_000
MAX_CHART_POINTS = 200
MAX_CHART_SERIES = 8
MAX_PIE_ITEMS = 12
MAX_STAT_ITEMS = 12
MAX_TIMELINE_ITEMS = 50

ShortText = Annotated[str, Field(max_length=200)]
LabelText = Annotated[str, Field(max_length=80)]
LongText = Annotated[str, Field(max_length=2_000)]

_RICH_FENCE_RE = re.compile(
    r'<pre><code class="language-(?P<kind>chart|stats|timeline)">(?P<body>.*?)</code></pre>',
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
    items: list[StatItem] = Field(min_length=1, max_length=MAX_STAT_ITEMS)


class TimelineItem(_RichModel):
    time: LabelText
    title: ShortText
    content: LongText | None = None
    status: Literal["neutral", "success", "warning", "danger"] = "neutral"


class TimelineBlock(_RichModel):
    title: ShortText | None = None
    items: list[TimelineItem] = Field(min_length=1, max_length=MAX_TIMELINE_ITEMS)


_RICH_MODELS: dict[str, type[_RichModel]] = {
    "chart": ChartBlock,
    "stats": StatsBlock,
    "timeline": TimelineBlock,
}


def _rich_placeholder(kind: str, data: _RichModel) -> str:
    serialized = json.dumps(data.model_dump(mode="json", exclude_none=True), ensure_ascii=False, separators=(",", ":"))
    encoded = html.escape(serialized, quote=True)
    return f'<div class="md-rich-block" data-rich-kind="{kind}" data-rich-config="{encoded}"></div>'


def render_rich_markdown_blocks(html_content: str) -> str:
    """将受控 JSON fenced block 转成可信占位节点；非法块保持为代码块。"""

    def replace(match: re.Match[str]) -> str:
        kind = match.group("kind").lower()
        source = html.unescape(match.group("body")).strip()
        if len(source) > MAX_RICH_BLOCK_CHARS:
            logger.warning("Markdown %s 富内容块超过 %s 字符，保留为代码块", kind, MAX_RICH_BLOCK_CHARS)
            return match.group(0)
        try:
            raw: Any = json.loads(source)
            data = _RICH_MODELS[kind].model_validate(raw)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            logger.warning("Markdown %s 富内容块校验失败，保留为代码块: %s", kind, exc)
            return match.group(0)
        return _rich_placeholder(kind, data)

    return _RICH_FENCE_RE.sub(replace, html_content)
