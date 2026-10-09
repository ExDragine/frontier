# Legacy JSON UI component contract

旧 `ui` JSON 继续支持。新回复优先使用 [Markdown 组件](components.md)；需要这里独有的 facts/list/quote/sources 等组件时再读取本契约。

## Contents

- Document and limits
- Text and structure
- Lists and facts
- Evidence and status
- Data and tables

## Document and limits

使用一个 `ui` 代码块，内部是严格 JSON：双引号，无注释、尾逗号、函数或表达式。
顶层 `children` 必填，可选 `title`（200 字符）、`eyebrow`（80）、`description`（2000）。
每个组件用 `type` 区分，不支持未列出的字段。文本长度按 Unicode 字符计算。

- 每个 `children` 为 1–12 项；整棵树最多 80 个组件、深度最多 6 层。
- 每块原始 JSON 最多 50,000 字符。prose 正文最多 50,000 字符；其他长文字最多 2000，标题/短说明 200，标签/单位 80。
- 需要更多内容时拆成多个正文/分区，或直接用普通 Markdown。无效块会显示为代码。
- `status` 为 `neutral/success/warning/danger`，默认 `neutral`，只表达实际状态。
- URL 只接受完整 HTTP(S) 地址。

## Text and structure

| type | 必填 | 可选与默认值 |
| --- | --- | --- |
| `prose` | `text`：Markdown 正文 | 支持段落、强调、列表、代码和公式；原始 HTML 转义、图片语法不加载图片；不要传 `rendered` |
| `text` | `text`：纯文字 | `variant`：`body`（默认）、`lead`、`muted`、`small` |
| `heading` | `text`：纯文字 | 独立分区标题 |
| `code` | `text`：代码原文 | 静态代码块 |
| `mermaid` | `text`：Mermaid 源码 | 不嵌入 HTML 或交互 |
| `section` | `children` | `title`、`eyebrow`、`description`；无边框分区 |
| `card` | `children` | `title`、`eyebrow`、`description`、`footer`（200）；`variant`：`outline`（默认）、`muted`、`ghost`；`color`：`neutral`（默认）、`blue/emerald/violet/amber/rose/cyan` |
| `row` / `column` | `children` | `gap`：`sm/md/lg`（默认 `md`）；row 自动换行 |
| `grid` | `children` | `columns`：1–3，默认 2；`gap`：`sm/md/lg` |
| `separator` | 无 | `label`：80 字符，可省略 |

`section` 是内容组织；`card` 是视觉分组。卡片标题与描述在 header 中，children 为正文，footer 为辅助信息。
`row/column` 不能传 columns。文字层级是受控变体，不能自定义字号、颜色或 CSS。

```json
{"title":"主题","description":"可选的一句话说明","children":[{"type":"prose","text":"直接答案。**关键依据**放在自然的段落里。"},{"type":"section","title":"原因","children":[{"type":"text","text":"必要的解释。"}]}]}
```

## Lists and facts

`list`：必填 `items`，1–20 个对象；每项 `title` 必填（200），`description` 可选（2000），`meta` 可选（80）。
`variant` 为 `plain`（默认，无框）、`divided`（细分隔线）或 `outline`（独立描边条目）。

`steps`：必填 `items`，1–20 项，每项可为纯文字（2000）、与 list 相同的 title/description/meta 对象，或 `{"type":"prose","text":"Markdown 正文"}`。自动编号；prose 项支持代码、段落等 Markdown，计入组件数量和深度。

`facts`：必填 `items`，1–20 项，每项 `label`（80）、`value`（2000）必填；可选 `columns` 为 1（默认）或 2。适合同一对象的属性，默认不加卡片。

```json
{"type":"list","variant":"divided","items":[{"title":"要点","description":"解释要点","meta":"可选辅助信息"}]}
```

## Evidence and status

| type | 必填 | 可选与默认值 |
| --- | --- | --- |
| `alert` | `text`（2000） | `title`（200）、`status`；旧 `callout` 写法仍可读取，新内容使用 alert |
| `badge` | `text`（80） | `status`；`variant` 为 `secondary`（默认）、`outline`、`solid` |
| `quote` | `text`（2000） | `attribution`（200）；仅用于真实引文 |
| `link` | `label`（80）、`url` | 完整 HTTP(S) URL 会显示出来 |
| `sources` | `items`：1–12 项 | 每项 `label`（200）、`url` 必填，`description`（200）可选 |
| `progress` | `label`（80）、`value`：0–100 的有限数值 | `detail`（200）；仅用于真实的已知百分比 |

来源的标题、URL 和说明都是文字，不用伪装成可点击按钮。引用或来源为空时，省略整个组件。

## Data and tables

`table`：必填 `columns`（1–8 个列名，每个 80 字符），`rows`（1–50 行，每个单元格最多 200 字符）。每行的列数必须匹配。
可选 `caption`（200），`column_widths`（每列一个 1–12 的整数权重）。默认自动分配列宽；只有明确需要控制比例时使用权重，例如两列 `[2, 8]`。

`chart/stats/timeline`：必填 `config`，契约见 [数据组件](data.md)。不要把配置字段直接放在组件根上。

```json
{"type":"table","caption":"共同维度","columns":["维度","方案 A","方案 B"],"rows":[["维护","自行维护","服务方维护"]]}
```

`image/map/iframe` 是独立媒体组件，可以直接放在根 children 或 section 中。契约见 [媒体组件](media.md)。
