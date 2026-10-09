# Markdown component contract

## Contents

- Writing and nesting
- Cards, sections and layouts
- Steps
- Media and data
- Limits and compatibility

## Writing and nesting

直接输出 Markdown，在需要的地方插入组件；不要给整条回复加代码围栏。组件打开行是 `::名称{属性}`，关闭行是单独的 `::`；无属性时省略花括号。正文直接写 Markdown，不填写 type/children/text，不转义整篇内容。

```markdown
先回答核心问题，再展开解释。

::card{title="关键机制" color="blue"}
这里写 **重点**、段落、列表、表格或代码。
::

后续解释继续使用普通正文。
```

属性使用字面量 `key=value`，多个属性以空格分隔；文字值加引号，数字和布尔值直接写。属性中不写 Markdown、动态绑定、表达式、HTML、CSS、JavaScript 或事件。普通 HTML 仍按文字处理。需要介绍组件语法时，放进普通代码块，示例不会执行。

嵌套时每个打开行都对应一个关闭行，不需要改变冒号数量：

```markdown
::grid{columns=2}
::card{title="方案 A" color="blue"}
简短说明。
::
::card{title="方案 B" color="violet"}
另一方案。
::
::
```

## Cards, sections and layouts

| 名称 | 属性 | 正文 |
| --- | --- | --- |
| `card` | `title/description/eyebrow/footer`；`color` 默认 neutral；`variant` 默认 muted | Markdown 和嵌套组件 |
| `section` | 可选 `title/description/eyebrow` | Markdown 和嵌套组件，无边框分区 |
| `grid` | `columns` 为 1–3，默认 2；`gap` 为 sm/md/lg，默认 md | 短内容适合并列，窄图自动纵向排列 |
| `row` / `column` | `gap` 为 sm/md/lg，默认 md | 自动换行的横向布局／纵向布局，不传 columns |

颜色可用 neutral/blue/emerald/violet/amber/rose/cyan；variant 为 muted（柔和底色）、outline（描边强调）、ghost（弱化边框）。颜色区分对象或主题，不暗示不存在的好坏。

段落、标题、表格、引文、链接和公式优先使用原生 Markdown；需要独立彩色分组时才用 card。长解释、完整步骤、宽表格和媒体纵向占整行。不要把每段正文装进卡片。

## Steps

`::steps` 没有属性，正文必须是一组 Markdown 有序列表，1–20 步。每步可以有粗体、解释、嵌套列表和代码块；续行按普通 Markdown 列表缩进。其他组件放在步骤外，不嵌入列表项。

````markdown
## 验证服务

::steps
1. **启动**

   ```sh
   python app.py
   ```

   检查日志，确认服务启动。
2. **验证**
   发出一个请求，确认收到预期回答。
::
````

## Media and data

`image/map/iframe` 是独立组件，正文留空，仍用 `::` 关闭。使用前读取 [媒体契约](media.md)，填写查证过的公开地址或 WGS84 坐标。

`chart/stats/timeline` 仍使用原有 JSON 代码块，可以单独出现，也可以放在 card/section 的正文中；Mermaid 同样使用自己的代码块。使用数据组件前读取 [数据契约](data.md)。普通比较表直接写 Markdown 表格。

## Limits and compatibility

每个组件块最多 50,000 字符。每组 children 为 1–12 个组件，每棵树最多 80 个、深度最多 6 层；一段连续 Markdown 正文计为一个 prose，步骤的正文也计入组件数与深度。文字属性：title/footer 最多 200 字符、eyebrow 80、description 2000。需要更多内容时拆为多个分区或独立组件块。

格式或属性不合法时尽量保留该块正文；其他有效组件继续展示。缺少关闭行、超限或错误媒体字段可能失去该模块的展示，所以发送前检查每个 `::` 配对和属性。

旧 `ui` JSON 仍支持，字段和额外组件见 [旧 UI 契约](legacy-ui.md)。新回复不要混用两套正文写法；复杂数据使用其独立 JSON 代码块即可。
