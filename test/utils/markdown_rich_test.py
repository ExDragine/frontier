# ruff: noqa: S101

import json

import pytest
from markdown_it import MarkdownIt

from utils.markdown_rich import render_rich_markdown_blocks


def _render(markdown: str) -> str:
    return render_rich_markdown_blocks(MarkdownIt("commonmark", {"html": False}).render(markdown))


def test_valid_line_chart_becomes_trusted_placeholder():
    rendered = _render(
        """```chart
{"type":"line","title":"趋势","labels":["一月","二月"],"series":[{"name":"销量","values":[1,2]}]}
```"""
    )

    assert 'class="md-rich-block"' in rendered
    assert 'data-rich-kind="chart"' in rendered
    assert "language-chart" not in rendered
    assert "&quot;type&quot;:&quot;line&quot;" in rendered


def test_valid_pie_stats_and_timeline_blocks_are_supported():
    cases = {
        "chart": '{"type":"pie","data":[{"name":"A","value":1}]}',
        "stats": '{"items":[{"label":"可用率","value":"99%","status":"success"}]}',
        "timeline": '{"items":[{"time":"今天","title":"发布","content":"完成"}]}',
    }

    for kind, body in cases.items():
        rendered = _render(f"```{kind}\n{body}\n```")
        assert f'data-rich-kind="{kind}"' in rendered


def test_rich_text_is_encoded_in_data_attribute():
    rendered = _render(
        """```stats
{"items":[{"label":"<script>alert(1)</script>","value":"ok"}]}
```"""
    )

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_invalid_rich_blocks_remain_code_blocks():
    cases = [
        ("chart", '{"type":"line","labels":["A","B"],"series":[{"name":"x","values":[1]}]}'),
        ("chart", '{"type":"pie","data":[{"name":"A","value":-1}]}'),
        ("stats", '{"items":[{"label":"x","value":"1","unknown":true}]}'),
        ("timeline", "not-json"),
    ]

    for kind, body in cases:
        rendered = _render(f"```{kind}\n{body}\n```")
        assert f'language-{kind}' in rendered
        assert "md-rich-block" not in rendered


def test_rich_block_capacity_limits_are_enforced():
    series = ",".join(f'{{"name":"s{index}","values":[1]}}' for index in range(9))
    rendered = _render(f'```chart\n{{"type":"bar","labels":["A"],"series":[{series}]}}\n```')

    assert "language-chart" in rendered
    assert "md-rich-block" not in rendered


def test_composed_ui_validates_nested_layout_and_existing_data_components():
    block = {
        "title": "方案比较",
        "children": [{
            "type": "grid", "columns": 2,
            "children": [
                {"type": "card", "title": "方案 A", "children": [
                    {"type": "badge", "text": "已验证", "status": "success"},
                    {"type": "text", "text": "<script>alert(1)</script>"},
                ]},
                {"type": "chart", "config": {
                    "type": "bar", "labels": ["A"], "series": [{"name": "延迟", "values": [12]}],
                }},
            ],
        }],
    }
    rendered = _render(f"```ui\n{json.dumps(block)}\n```")
    assert 'data-rich-kind="ui"' in rendered
    assert "<script>" not in rendered
    assert "language-ui" not in rendered


@pytest.mark.parametrize("node", [
    {"type": "image", "src": "file:///etc/passwd"},
    {"type": "text", "text": "hello", "style": "color:red"},
    {"type": "link", "label": "打开", "url": "javascript:alert(1)"},
    {"type": "grid", "columns": 4, "children": [{"type": "text", "text": "a"}]},
    {"type": "row", "columns": 2, "children": [{"type": "text", "text": "a"}]},
    {"type": "table", "columns": ["A", "B"], "rows": [["1"]]},
    {"type": "callout", "text": "test", "status": "unknown"},
    {"type": "text", "text": "x" * 2001},
])
def test_invalid_ui_components_remain_readable_code(node):
    rendered = _render(f'```ui\n{json.dumps({"children": [node]})}\n```')
    assert "language-ui" in rendered
    assert "md-rich-block" not in rendered


def test_ui_capacity_is_bounded_across_the_whole_tree():
    leaf = {"type": "text", "text": "test"}
    deep = leaf
    for _ in range(6):
        deep = {"type": "column", "children": [deep]}
    wide = {"type": "card", "children": [leaf] * 12}
    for children in ([deep], [wide] * 7):
        rendered = _render(f'```ui\n{json.dumps({"children": children})}\n```')
        assert "language-ui" in rendered
        assert "md-rich-block" not in rendered
