# ruff: noqa: S101

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

from utils.markdown_components import has_markdown_components, markdown_components_plugin
from utils.markdown_rich import render_rich_markdown_blocks


def _render(source: str) -> BeautifulSoup:
    md = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"]).use(markdown_components_plugin)
    return BeautifulSoup(render_rich_markdown_blocks(md.render(source)), "html.parser")


def _nodes(document: BeautifulSoup) -> list[dict]:
    return [json.loads(node["data-rich-config"])["children"][0] for node in document.select('[data-rich-kind="ui"]')]


def test_markdown_cards_mix_with_prose_and_nested_responsive_layouts():
    source = '''先给出结论。

::grid{columns=2 gap="lg"}
::card{title="方案 A" color="blue"}
支持 **Markdown**，不需要转义 "引号"。

- 第一项
- 第二项
::
::card{title="方案 B" color="violet" footer="辅助说明"}
## 依据
保留自然段落。
::
::

接着展开解释。
'''
    document = _render(source)
    grid = _nodes(document)[0]
    assert grid["type"] == "grid" and grid["columns"] == 2 and grid["gap"] == "lg"
    assert [card["color"] for card in grid["children"]] == ["blue", "violet"]
    assert grid["children"][0]["variant"] == "muted"
    prose = BeautifulSoup(grid["children"][0]["children"][0]["rendered"], "html.parser")
    assert prose.strong.get_text() == "Markdown" and len(prose.select("li")) == 2
    assert document.find("p").get_text() == "先给出结论。"
    assert document.find_all("p")[-1].get_text() == "接着展开解释。"


def test_markdown_steps_preserve_commands_formatting_and_continuation_paragraphs():
    node = _nodes(_render('''::steps
1. **启动服务**

   ```sh
   python app.py --name "测试"
   ```

   检查启动日志。
2. **验证结果**
   访问服务，确认回答。
::
'''))[0]
    assert node["type"] == "steps" and len(node["items"]) == 2
    step = BeautifulSoup(node["items"][0]["rendered"], "html.parser")
    assert step.strong.get_text() == "启动服务"
    assert step.code.get_text().strip() == 'python app.py --name "测试"'
    assert "检查启动日志。" in step.get_text()


def test_defaults_do_not_become_invalid_explicit_fields_when_nodes_are_nested():
    source = '::section\n::row\n正文\n::\n\n```ui\n{"children":[{"type":"code","text":"print(1)"}]}\n```\n::'
    children = _nodes(_render(source))[0]["children"]
    assert children[0]["type"] == "row"
    assert children[1]["type"] == "code" and children[1]["text"] == "print(1)"


def test_tables_math_and_data_can_live_inside_markdown_sections():
    source = '''::section{title="证据"}
公式 $E=mc^2$ 与 ~~旧结论~~。

| 对象 | 数量 |
| --- | --- |
| A | 2 |

```chart
{"type":"bar","labels":["A"],"series":[{"name":"数量","values":[2]}]}
```

```mermaid
flowchart TD
A[输入] --> B[验证]
```
::
'''
    children = _nodes(_render(source))[0]["children"]
    prose = BeautifulSoup(children[0]["rendered"], "html.parser")
    assert prose.table and prose.s and "$E=mc^2$" in prose.get_text()
    assert children[1]["type"] == "chart" and children[1]["config"]["series"][0]["values"] == [2.0]
    assert children[2]["type"] == "mermaid"


@pytest.mark.parametrize("fence", ["```markdown", "~~~markdown", "````markdown"])
def test_component_examples_inside_code_are_not_executed(fence):
    end = fence.split("markdown")[0]
    source = f'{fence}\n::card{{color="blue"}}\n示例\n::\n{end}\n'
    assert not _nodes(_render(source))
    assert not has_markdown_components(source)
    assert "::card" in _render(source).code.get_text()


def test_markers_inside_fenced_or_indented_code_do_not_close_a_card():
    source = '''::card{title="代码" color="cyan"}
```text
::
::card{color="rose"}
```

    ::
    ::card

正文仍属于同一卡片。
::
'''
    node = _nodes(_render(source))[0]
    prose = BeautifulSoup(node["children"][0]["rendered"], "html.parser")
    assert len(prose.select("pre")) == 2 and "正文仍属于同一卡片。" in prose.get_text()


@pytest.mark.parametrize("source", [
    "> ::card{color=blue}\n> 内容\n> ::\n",
    "- ::card{color=blue}\n  内容\n  ::\n",
])
def test_components_inside_markdown_containers_also_trigger_image_delivery(source):
    assert _nodes(_render(source))[0]["color"] == "blue"
    assert has_markdown_components(source)


@pytest.mark.parametrize("source", [
    '    ::card{color="blue"}\n    示例\n    ::\n',
    '示例语法是 `::card{color="blue"}`，正文继续。',
])
def test_indented_or_inline_component_examples_remain_literal_text(source):
    assert not has_markdown_components(source) and not _nodes(_render(source))


@pytest.mark.parametrize(
    "header",
    [
        '::card{color="unknown"}',
        '::card{style="position:absolute"}',
        '::card{color="blue" color="rose"}',
        '::card{type="prose"}',
        '::card{rendered="<script>bad()</script>"}',
        '::card{:color="dynamic"}',
        '::card{onload="bad()"}',
        '::card{title="unclosed}',
        '::grid{columns=4}',
        '::grid{columns=true}',
    ],
)
def test_bad_attributes_recover_only_the_affected_body(header):
    source = f'{header}\n**保留正文**\n::\n\n::card{{color="blue"}}\n正确部分\n::\n'
    document = _render(source)
    assert document.strong.get_text() == "保留正文"
    assert len(_nodes(document)) == 1 and _nodes(document)[0]["color"] == "blue"
    assert not document.select("script, img")


def test_unclosed_component_recovers_markdown_and_does_not_hide_following_text():
    document = _render('::card{color="blue"}\n**内容**\n\n后续段落\n')
    assert not _nodes(document) and document.strong.get_text() == "内容"
    assert "后续段落" in document.get_text() and "::card" not in document.get_text()


@pytest.mark.parametrize(
    "header, expected",
    [
        ('::image{url="https://example.com/a.png" alt="图片" fit="cover"}', {"type": "image", "fit": "cover"}),
        ('::iframe{url="https://example.com" title="页面" height=600 full_page=false}', {"type": "iframe", "height": 600, "full_page": False}),
        ('::map{latitude=31.2304 longitude=121.4737 zoom=12}', {"type": "map", "zoom": 12}),
    ],
)
def test_standalone_media_uses_the_existing_validated_contract(header, expected):
    source = header + "\n::\n"
    node = _nodes(_render(source))[0]
    assert all(node[key] == value for key, value in expected.items())
    assert has_markdown_components(source)


@pytest.mark.parametrize("source", [
    '::image{url="file:///etc/passwd" alt="非法"}\n::',
    '::iframe{url="javascript:alert(1)" title="非法"}\n::',
    '::map{latitude=90 longitude=0}\n::',
    '::map{latitude=NaN longitude=0}\n::',
    '::image{url="https://example.com/a.png" alt="图片"}\n不支持的正文\n::',
])
def test_invalid_media_never_reaches_the_media_loader(source):
    assert not _nodes(_render(source)) and not has_markdown_components(source)
    assert _render(source).get_text().strip()


def test_prose_stays_inert_and_long_paragraphs_need_no_manual_json_splitting():
    source = '::card{color="blue"}\n' + "长段落" * 1000 + '\n\n<script>bad()</script> ![远程](https://example.com/a.png) [危险](javascript:alert(1))\n::'
    node = _nodes(_render(source))[0]
    prose = BeautifulSoup(node["children"][0]["rendered"], "html.parser")
    assert len(node["children"][0]["text"]) > 2000
    assert not prose.select("script, img, a[href^='javascript:']")
    assert "<script>bad()</script>" in prose.get_text()


def test_component_depth_and_raw_size_are_bounded_without_recursive_failure():
    source = "::section\n" * 100 + "**正文**\n" + "::\n" * 100
    document = _render(source)
    assert "正文" in str(document)
    assert not has_markdown_components('::card\n' + "字" * 50001 + '\n::')


def test_old_ui_json_still_renders_alongside_the_new_dialect():
    document = _render('::card{color="blue"}\n新内容\n::\n\n```ui\n{"children":[{"type":"text","text":"旧内容"}]}\n```')
    assert len(_nodes(document)) == 2
    assert _nodes(document)[1]["type"] == "text"


@pytest.mark.parametrize("name", ["article", "comparison", "guide", "media"])
def test_markdown_skill_examples_use_real_components_without_fallback(name):
    source = (Path(__file__).resolve().parents[2] / "skills/rich-markdown/examples" / f"{name}.md").read_text()
    md = MarkdownIt("commonmark", {"html": False}).use(markdown_components_plugin)
    components = [token for token in md.parse(source) if token.type == "frontier_component"]
    assert components and all(token.meta.get("node") for token in components)
