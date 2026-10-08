"""Smoke-test the production Markdown renderer with a real Chromium browser.

Browser plugin not available in CI; use the project's locked Playwright runtime.
Flow: composed Markdown -> trusted UI -> long PNG -> rerender at narrow width.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils import browser_runtime, markdown_render  # noqa: E402

ui = {
    "title": "Frontier · 方案比较与任务说明",
    "children": [
        {
            "type": "callout",
            "title": "先看结论",
            "text": "根据任务选择展示方式。核心结论清楚，点开长图后可以阅读完整细节。",
            "status": "success",
        },
        {
            "type": "grid",
            "columns": 2,
            "children": [
                {
                    "type": "card",
                    "title": "本地部署",
                    "children": [
                        {"type": "badge", "text": "可离线", "status": "success"},
                        {"type": "text", "text": "适合需要本地处理数据的任务。需要维护硬件、模型和服务。"},
                        {"type": "link", "label": "示例文档", "url": "https://example.com/local"},
                    ],
                },
                {
                    "type": "card",
                    "title": "托管 API",
                    "children": [
                        {"type": "badge", "text": "依赖网络", "status": "warning"},
                        {"type": "text", "text": "无需维护推理服务。先核对费用、数据要求和接口能力。"},
                        {
                            "type": "code",
                            "text": 'const result = await client.responses.create({\n  model: "your-model",\n  input: "Hello"\n});',
                        },
                    ],
                },
            ],
        },
        {"type": "heading", "text": "同一数据，组合展示"},
        {
            "type": "column",
            "children": [
                {
                    "type": "stats",
                    "config": {
                        "columns": 3,
                        "items": [
                            {"label": "示例指标 A", "value": "12", "unit": "项"},
                            {"label": "示例指标 B", "value": "8", "unit": "项"},
                            {"label": "示例指标 C", "value": "4", "unit": "项"},
                        ],
                    },
                },
                {
                    "type": "chart",
                    "config": {
                        "type": "bar",
                        "title": "示例数据，不代表实际评测",
                        "labels": ["方案 A", "方案 B", "方案 C"],
                        "series": [{"name": "示例值", "values": [12, 8, 4]}],
                    },
                },
            ],
        },
        {
            "type": "table",
            "columns": ["比较维度", "本地部署", "托管 API"],
            "rows": [["维护", "自行维护", "服务方维护"], ["网络", "可离线", "需要网络"]],
        },
        {"type": "steps", "items": ["确认需求和约束", "用实际任务验证效果", "再决定部署方式"]},
        {
            "type": "mermaid",
            "text": "flowchart LR\nA[用户问题] --> B[选择内容模块]\nB --> C[渲染长图]\nC --> D[发送 QQ]",
        },
        {
            "type": "timeline",
            "config": {
                "title": "示例执行过程",
                "items": [
                    {"time": "第一步", "title": "准备", "content": "确认输入数据", "status": "success"},
                    {"time": "第二步", "title": "验证", "content": "核对结果与来源"},
                ],
            },
        },
        {
            "type": "row",
            "children": [
                {
                    "type": "card",
                    "title": "完整细节",
                    "children": [{"type": "text", "text": "长图保留必要说明。用户可以点开并放大查看。\n" * 8}],
                },
                {
                    "type": "card",
                    "title": "文本转义验证",
                    "children": [
                        {
                            "type": "text",
                            "text": "<script>window.injection = true</script>\n<img src=x onerror=alert(1)> 应作为普通文字出现。",
                        }
                    ],
                },
            ],
        },
    ],
}

article_ui = {
    "title": "长图排版回归示例",
    "children": [
        {"type": "callout", "title": "先看结论", "text": "以下为排版示例，用于检查长图中的字体、模块间距和表格列宽。"},
        {
            "type": "stats",
            "config": {
                "columns": 4,
                "items": [
                    {"label": "手稿", "value": "719", "unit": "篇", "detail": "示例数据，持续更新"},
                    {"label": "结果族", "value": "372", "detail": "按数学分支分类"},
                    {"label": "主结果已形式化", "value": "42", "unit": "%", "status": "success"},
                    {"label": "平均算力", "value": "3", "unit": "小时 ChatGPT Pro"},
                ],
            },
        },
        {
            "type": "card",
            "title": "仓库里有什么",
            "children": [{"type": "steps", "items": [
                "preprints/：每篇的 PDF、源文件、单独的构建说明和引用信息",
                "lean/：形式化库和形式化目录",
                "Comparator：按 JSON 配置逐个核对指定定理、解答模块和允许的公理",
            ]}],
        },
        {
            "type": "table",
            "columns": ["族", "结果说明"],
            "rows": [
                ["003", "这是一段较长的结果说明，包含 Dirichlet L 函数与数学符号，用来验证说明列获得足够空间。"],
                ["074", "三维柱谷极大函数猜想与四维 Hausdorff 维数猜想"],
                ["002 / 006", "每条有理椭圆曲线的二次扭曲族上，完整的公式应当清楚可读。"],
            ],
        },
        {"type": "callout", "title": "阅读提示", "text": "示例结果仅用于验证排版。长图保留完整内容，点开后可以放大阅读。", "status": "warning"},
        {"type": "link", "label": "示例仓库", "url": "https://github.com/example/math"},
    ],
}


async def verify(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    original_wait = markdown_render._wait_for_renderer_ready
    original_logging = markdown_render._attach_page_logging
    try:
        for width in (1000, 390):
            observed = {}
            page_errors = []
            blocked_remote_requests = []
            ui["title"] = f"Frontier · 方案比较与任务说明 · {width}"
            source = "以下为混合模块示例。\n\n```ui\n" + json.dumps(ui, ensure_ascii=False) + "\n```\n\n$E=mc^2$\n"
            source += "\n```ui\n" + json.dumps(article_ui, ensure_ascii=False) + "\n```\n"

            async def after_load(page, observed=observed):
                await original_wait(page)
                observed.update(
                    await page.evaluate("""() => {
                    const article = [...document.querySelectorAll('.md-ui-document')].at(-1);
                    const table = article.querySelector('.md-ui-table');
                    const cells = table.querySelectorAll('th');
                    const modules = [...article.children].map(node => node.getBoundingClientRect());
                    return {
                    title: document.title,
                    state: window.__FRONTIER_RENDER__,
                    text: document.body.textContent,
                    width: document.querySelector('#markdown-content').clientWidth,
                    scrollWidth: document.querySelector('#markdown-content').scrollWidth,
                    chart: document.querySelector('[data-chart-rendered]')?.dataset.chartRendered,
                    chartWidth: document.querySelector('.md-chart-canvas svg')?.getBoundingClientRect().width,
                    chartHeight: document.querySelector('.md-chart-canvas svg')?.getBoundingClientRect().height,
                    chartPaths: document.querySelectorAll('.md-chart-canvas svg path').length,
                    mermaid: document.querySelector('[data-mermaid-rendered]')?.dataset.mermaidRendered,
                    gridColumns: getComputedStyle(document.querySelector('.md-ui-grid')).gridTemplateColumns,
                    scripts: document.querySelectorAll('#markdown-content script').length,
                    height: document.querySelector('#markdown-content').scrollHeight,
                    articleGaps: modules.slice(1).map((rect, i) => rect.top - modules[i].bottom),
                    shortColumnRatio: cells[0].getBoundingClientRect().width / table.getBoundingClientRect().width,
                    statLabelSize: parseFloat(getComputedStyle(article.querySelector('.md-stat-label')).fontSize),
                    tableTextSize: parseFloat(getComputedStyle(table).fontSize)
                }}""")
                )

            def logging(page, page_errors=page_errors, blocked_remote_requests=blocked_remote_requests):
                original_logging(page)
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.on(
                    "request",
                    lambda request: (
                        blocked_remote_requests.append(request.url)
                        if request.url.startswith(("http:", "https:"))
                        else None
                    ),
                )

            markdown_render._wait_for_renderer_ready = after_load
            markdown_render._attach_page_logging = logging
            png = await markdown_render.markdown_to_image(source, width=width)
            if not png:
                raise RuntimeError("Renderer returned no image")
            image = Image.open(io.BytesIO(png))
            (output_dir / f"ui-{width}.png").write_bytes(png)
            checks = {
                "page_identity": observed["title"] == "Markdown Rendered",
                "meaningful_content": ui["title"] in observed["text"],
                "ready": observed["state"]["state"] == "ready",
                "no_render_errors": not observed["state"]["errors"] and not page_errors,
                "chart": observed["chart"] == "true",
                "chart_geometry": observed["chartWidth"] > 100 and observed["chartHeight"] > 100
                and observed["chartPaths"] >= 3,
                "mermaid": observed["mermaid"] == "true",
                "escaped_text": observed["scripts"] == 0 and "window.injection = true" in observed["text"],
                "no_remote_requests": not blocked_remote_requests,
                "no_horizontal_overflow": observed["scrollWidth"] <= observed["width"],
                "long_image": image.height > 1500 and image.width == width,
                "responsive_grid": len(observed["gridColumns"].split()) == (2 if width == 1000 else 1),
                "article_spacing": all(gap >= 23 for gap in observed["articleGaps"]),
                "content_table_columns": observed["shortColumnRatio"] < 0.3,
                "readable_secondary_text": observed["statLabelSize"] >= 18 and observed["tableTextSize"] >= 19,
            }
            result = {
                "viewport": width,
                "png_size": image.size,
                "bytes": len(png),
                "checks": checks,
                "render_errors": observed["state"]["errors"],
                "page_errors": page_errors,
            }
            (output_dir / f"ui-{width}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(json.dumps(result, ensure_ascii=False))
            if not all(checks.values()):
                raise RuntimeError(f"Renderer smoke check failed: {result}")
    finally:
        markdown_render._wait_for_renderer_ready = original_wait
        markdown_render._attach_page_logging = original_logging
        await browser_runtime.close_browser()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(tempfile.mkdtemp(prefix="frontier-ui-")))
    args = parser.parse_args()
    asyncio.run(verify(args.output_dir))


if __name__ == "__main__":
    main()
