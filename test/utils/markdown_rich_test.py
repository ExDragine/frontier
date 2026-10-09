# ruff: noqa: S101

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
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


def test_three_and_flow_models_are_available_to_the_rich_parser():
    cases = {
        "three": '{"type":"three","objects":[{"kind":"sphere","position":[0,0,0]}]}',
        "flow": '{"type":"flow","nodes":[{"id":"a","label":"开始"}]}',
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
        assert f"language-{kind}" in rendered
        assert "md-rich-block" not in rendered


def test_rich_block_capacity_limits_are_enforced():
    series = ",".join(f'{{"name":"s{index}","values":[1]}}' for index in range(9))
    rendered = _render(f'```chart\n{{"type":"bar","labels":["A"],"series":[{series}]}}\n```')

    assert "language-chart" in rendered
    assert "md-rich-block" not in rendered


def test_composed_ui_validates_nested_layout_and_existing_data_components():
    block = {
        "title": "方案比较",
        "children": [
            {
                "type": "grid",
                "columns": 2,
                "children": [
                    {
                        "type": "card",
                        "title": "方案 A",
                        "children": [
                            {"type": "badge", "text": "已验证", "status": "success"},
                            {"type": "text", "text": "<script>alert(1)</script>"},
                        ],
                    },
                    {
                        "type": "chart",
                        "config": {
                            "type": "bar",
                            "labels": ["A"],
                            "series": [{"name": "延迟", "values": [12]}],
                        },
                    },
                ],
            }
        ],
    }
    rendered = _render(f"```ui\n{json.dumps(block)}\n```")
    assert 'data-rich-kind="ui"' in rendered
    assert "<script>" not in rendered
    assert "language-ui" not in rendered


def test_map_layers_and_three_scene_are_declarative_components():
    block = {
        "children": [
            {
                "type": "map",
                "latitude": 31.23,
                "longitude": 121.47,
                "markers": [{"latitude": 31.23, "longitude": 121.47, "label": "中心"}],
                "paths": [{"points": [[31.2, 121.4], [31.3, 121.5]], "color": "#e11d48"}],
            },
            {
                "type": "three",
                "objects": [{"kind": "cube", "position": [0, 0.5, 0], "color": "#6366f1"}],
            },
        ]
    }
    rendered = _render(f"```ui\n{json.dumps(block)}\n```")
    assert 'data-rich-kind="ui"' in rendered
    assert "language-ui" not in rendered


def test_map_analysis_and_flow_validate_references():
    block = {
        "children": [
            {
                "type": "map",
                "latitude": 31.23,
                "longitude": 121.47,
                "paths": [{"points": [[31.2, 121.4], [31.3, 121.5]]}],
                "analysis": {"type": "distance", "label": "路线长度"},
            },
            {
                "type": "flow",
                "nodes": [{"id": "a", "label": "开始"}, {"id": "b", "label": "结束"}],
                "edges": [{"source": "a", "target": "b"}],
            },
        ]
    }
    rendered = _render(f"```ui\n{json.dumps(block)}\n```")
    assert 'data-rich-kind="ui"' in rendered
    assert "language-ui" not in rendered

    invalid = {"children": [{"type": "flow", "nodes": [{"id": "a", "label": "A"}], "edges": [{"source": "a", "target": "missing"}]}]}
    invalid_rendered = _render(f"```ui\n{json.dumps(invalid)}\n```")
    assert "language-ui" in invalid_rendered


@pytest.mark.parametrize(
    "node",
    [
        {"type": "image", "src": "file:///etc/passwd"},
        {"type": "text", "text": "hello", "style": "color:red"},
        {"type": "link", "label": "打开", "url": "javascript:alert(1)"},
        {"type": "grid", "columns": 4, "children": [{"type": "text", "text": "a"}]},
        {"type": "row", "columns": 2, "children": [{"type": "text", "text": "a"}]},
        {"type": "table", "columns": ["A", "B"], "rows": [["1"]]},
        {"type": "callout", "text": "test", "status": "unknown"},
        {"type": "text", "text": "x" * 2001},
    ],
)
def test_invalid_ui_components_remain_readable_code(node):
    rendered = _render(f"```ui\n{json.dumps({'children': [node]})}\n```")
    assert "language-ui" in rendered
    assert "md-rich-block" not in rendered


def test_ui_capacity_is_bounded_across_the_whole_tree():
    leaf = {"type": "text", "text": "test"}
    deep = leaf
    for _ in range(6):
        deep = {"type": "column", "children": [deep]}
    wide = {"type": "card", "children": [leaf] * 12}
    for children in ([deep], [wide] * 7):
        rendered = _render(f"```ui\n{json.dumps({'children': children})}\n```")
        assert "language-ui" in rendered
        assert "md-rich-block" not in rendered


@pytest.mark.parametrize("name", ["article", "comparison", "guide", "media"])
def test_skill_examples_match_the_live_component_contract(name):
    root = Path(__file__).resolve().parents[2] / "skills" / "rich-markdown" / "examples"
    block = json.loads((root / f"{name}.json").read_text())
    rendered = _render(f"```ui\n{json.dumps(block)}\n```")
    assert 'data-rich-kind="ui"' in rendered
    assert "language-ui" not in rendered


def test_prose_compiler_supports_formatting_without_accepting_raw_html_or_images():
    block = {
        "children": [
            {
                "type": "prose",
                "text": "**重点** `代码` $E=mc^2$ <script>alert(1)</script> "
                "[危险](javascript:alert(1)) ![图片](https://example.com/image.png)",
            }
        ]
    }
    placeholder = BeautifulSoup(_render(f"```ui\n{json.dumps(block)}\n```"), "html.parser")
    config = json.loads(placeholder.select_one('[data-rich-kind="ui"]')["data-rich-config"])
    prose = BeautifulSoup(config["children"][0]["rendered"], "html.parser")
    assert prose.strong.get_text() == "重点"
    assert prose.code.get_text() == "代码"
    assert not prose.select("script, img")
    assert not prose.select('a[href^="javascript:"]')
    assert "<script>alert(1)</script>" in prose.get_text()
    assert "$E=mc^2$" in prose.get_text()


@pytest.mark.parametrize(
    "node",
    [
        {"type": "prose", "text": "safe", "rendered": "<script>alert(1)</script>"},
        {"type": "text", "text": "safe", "variant": "absolute"},
        {"type": "code", "text": "safe", "variant": "lead"},
        {"type": "card", "variant": "custom", "children": [{"type": "text", "text": "safe"}]},
        {"type": "section", "children": []},
        {"type": "list", "items": [{"title": "safe", "html": "<b>test</b>"}]},
        {"type": "facts", "columns": 3, "items": [{"label": "safe", "value": "safe"}]},
        {"type": "sources", "items": [{"label": "safe", "url": "file:///etc/passwd"}]},
        {"type": "progress", "label": "test", "value": 101},
        {"type": "progress", "label": "test", "value": float("nan")},
        {"type": "table", "columns": ["A", "B"], "rows": [["1", "2"]], "column_widths": [1]},
        {"type": "table", "columns": ["A"], "rows": [["1"]], "column_widths": [0]},
    ],
)
def test_new_component_fields_preserve_strict_validation(node):
    rendered = _render(f"```ui\n{json.dumps({'children': [node]})}\n```")
    assert "language-ui" in rendered
    assert "md-rich-block" not in rendered


def test_section_nesting_counts_toward_the_same_depth_limit():
    node = {"type": "prose", "text": "leaf"}
    for _ in range(6):
        node = {"type": "section", "children": [node]}
    rendered = _render(f"```ui\n{json.dumps({'children': [node]})}\n```")
    assert "language-ui" in rendered
