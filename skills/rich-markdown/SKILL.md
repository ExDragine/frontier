---
name: rich-markdown
description: Use when a reply benefits from comparisons, cards, steps, composed layouts, Mermaid diagrams, numeric charts, metric summaries, or timelines rendered as a QQ long image.
---

# Rich Markdown output

直接输出 Markdown，不要添加 `<frontier-render>` 等外层信封，也不要输出原始 HTML、
JavaScript 或 CSS。普通聊天优先短文本；仅当图形明显比文字更清楚时才使用增强块：

- 流程、架构、关系图：使用标准 `mermaid` 代码块。
- 有明确数值的柱状图、折线图、饼图：使用 `chart` 代码块。
- 一组关键指标：使用 `stats` 代码块。
- 事件发展过程：使用 `timeline` 代码块。
- 多个内容模块需要组合排版：使用 `ui` 代码块。

QQ 支持点开长图和放大。把核心结论和分区标题做得醒目，保留完整细节，沿纵向展开；
不要为了缩略图能读完而删减必要内容，也不要为了装饰使用卡片。普通文字达到配置的
长度阈值（默认 500 字符）也会转图。短文字不会因为有标题或列表就转图。

## Composed UI

`ui` 内部使用严格 JSON。顶层只允许可选 `title` 和非空 `children`。
每个组件使用 `type` 选择类型；由渲染器提供固定样式，不传 HTML、CSS、JavaScript、
函数或任意样式字段。组件中的文字是纯文字，不解析 Markdown。

| 组件 type | 字段 |
| --- | --- |
| `row` / `column` | `children`：组件列表；row 自动换行，column 纵向排列 |
| `grid` | `children`；可选 `columns`：1–3，默认 2 |
| `card` | `children`；可选 `title` |
| `heading` / `text` | `text` |
| `badge` | `text`；可选 `status` |
| `callout` | `text`；可选 `title`、`status` |
| `steps` | `items`：1–20 条步骤文字 |
| `table` | `columns`：1–8 个列名；`rows`：1–50 行，每行与列数一致 |
| `link` | `label`、`url`：完整 HTTP(S) 地址 |
| `code` / `mermaid` | `text`：代码或 Mermaid 源码 |
| `chart` / `stats` / `timeline` | `config`：下方对应增强块的完整 JSON 契约 |

`status` 只能为 `neutral`、`success`、`warning`、`danger`，默认 `neutral`。
每个 `children` 最多 12 项；整块最多 80 个组件，最多 6 层嵌套。
文字最多 2000 字符，标题最多 200 字符，标签最多 80 字符。
比较通常用 2 列；多张图表或长说明优先纵向排列，避免挤压标签。
不要在截图中画不可点击的按钮、输入框、滚动区域或折叠区域。

```ui
{"title":"两种部署方案","children":[{"type":"callout","title":"选择依据","text":"先确认是否需要离线运行，再比较维护成本。"},{"type":"grid","columns":2,"children":[{"type":"card","title":"本地部署","children":[{"type":"badge","text":"可离线","status":"success"},{"type":"text","text":"需要自行维护硬件、模型和服务。"}]},{"type":"card","title":"托管 API","children":[{"type":"badge","text":"依赖网络"},{"type":"text","text":"无需维护推理服务，按实际使用计费。"}]}]},{"type":"steps","items":["确认网络和数据要求","核对预算与硬件","用实际任务验证效果"]}]}
```

模型负责选择并组合模块，渲染器负责排版。缺少数据时直接说明；不要虚构数值、
来源、排名或推荐标记。链接可以在图中展示，但需要复制代码或点击链接时，
按主提示词使用 `send_plain_text` 发送原文。图片/视频继续通过媒体工具发送。

`chart`、`stats` 和 `timeline` 块内部必须是严格 JSON：双引号、无注释、无尾逗号，
并且不得包含下方契约之外的字段。不要虚构缺失数据；无法满足格式时使用普通 Markdown。

## Chart

柱状图或折线图中，`type` 只能是 `bar` 或 `line`。最多 8 个系列，每个系列最多
200 个点：

```chart
{"type":"line","title":"季度收入","unit":"万元","labels":["Q1","Q2","Q3","Q4"],"series":[{"name":"2025","values":[120,138,151,176]},{"name":"2026","values":[132,149,170,198]}],"show_legend":true}
```

饼图最多 12 项，数值不得为负：

```chart
{"type":"pie","title":"请求来源","unit":"次","data":[{"name":"群聊","value":72},{"name":"私聊","value":28}],"show_legend":true}
```

## Stats

`columns` 只能是 1–4，最多 12 项；`status` 只能是 `neutral`、`success`、
`warning` 或 `danger`：

```stats
{"title":"服务状态","columns":3,"items":[{"label":"可用率","value":"99.95","unit":"%","detail":"最近 30 天","status":"success"},{"label":"平均延迟","value":"182","unit":"ms","status":"neutral"},{"label":"待处理告警","value":"2","status":"warning"}]}
```

## Timeline

时间线最多 50 项：

```timeline
{"title":"发布进度","items":[{"time":"09:00","title":"开始构建","content":"生成生产制品","status":"success"},{"time":"09:12","title":"灰度发布","content":"10% 流量观察中","status":"warning"}]}
```

不要传入函数、表达式、颜色、布局、任意图表 `option` 或未列出的字段。不同量纲或
差距悬殊的数据优先拆成多张图，避免误导。
