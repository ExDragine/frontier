---
name: rich-markdown
description: Compose readable QQ long-image replies for explanations, comparisons, practical guides, research summaries and data. Choose typography, sections, lists and focused visual components according to the reader's question. Skip ordinary short chat.
---

# Compose a readable reply

先把回答写对，再选择表达结构。使用同一套组件语言，生成适合当前内容的阅读版式。

## Decide the reading path

1. 明确读者最想解决的问题，把直接答案或关键判断放在前面。
2. 按信息关系分组：解释沿因果展开，比较围绕同一组维度，指南沿操作与验证展开，数据围绕指标含义展开。
3. 选择最少的组件表达这些关系。正文和无边框分区是正常选择；卡片用于独立对象、并列方案或需要明显分组的内容。
4. 从上到下检查阅读顺序：每个标题都应说明下面是什么，每个视觉强调都应有信息理由。

不要为所有回答规定同一套模块或顺序。不要默认添加“先看结论”、统计卡、警告框或来源区；没有数据就没有统计，没有具体风险就没有警告，没有引文就没有引用块。不要为了填满版式编造数字、排名、状态、来源或推荐标签。

## Choose a composition

| 内容关系 | 合适的表达 |
| --- | --- |
| 连贯解释、分析、背景 | `prose` 正文配 `section`，必要时使用 `lead` 引导句 |
| 同一对象的属性 | `facts`；多对象的共同维度用 `table` |
| 独立的并列方案 | `grid` + `card`，把选择依据放在正文里 |
| 若干概念、发现或建议 | `list`，用标题、描述和可选辅助信息组织 |
| 有先后关系的操作 | `steps`，写清执行内容和如何验证 |
| 真实的数量、趋势或事件 | `stats`、`chart`、`timeline` |
| 必须单独注意的异常或限制 | `alert`；状态标签用 `badge` |
| 需要原样摘录的真实文字 | `quote`，注明出处，不把自己的摘要伪装成引文 |
| 真实已知的完成比例 | `progress`，未知进度直接写未知 |
| 多个主要话题之间的分界 | `separator`；不要在每两段之间都插线 |
| 用于查证的链接 | `sources`，只列实际使用过的来源；单个链接用 `link` |

在同一回复里可以混用正文、分区、少量卡片和表格。完整解释不必总在卡片里；普通段落不必每段都加标题。短回复直接发普通 Markdown，不为装饰强制转图。

## Compose with the renderer

- 输出普通 Markdown，或一个 `ui` fenced block。`ui` 使用严格 JSON；顶层可用 `title`、`eyebrow`、`description` 和 `children`，元信息按需要填写。
- 使用组件内置的变体改变呈现：正文 `body/lead/muted/small`，卡片 `outline/muted/ghost`，列表 `plain/divided/outline`，标签 `secondary/outline/solid`，指标 `plain/cards`。根据内容的主次选择，不要全都使用高强调变体。
- 长文优先纵向展开。两列用于真正可并列阅读的短内容；长说明、图表和步骤通常占整行。窄屏会自动折叠列，不要依赖横向滚动。
- 用 `prose` 写需要段落、强调、列表、行内代码或公式的 Markdown；其他组件的文字字段是纯文字。不要在纯文字字段中留下 `**` 或 HTML。
- 不输出原始 HTML、CSS、JavaScript、任意图表 option、按钮、输入框、折叠区或依赖交互才能读到的内容。QQ 最终收到的是可点开、放大的静态长图。
- 保留必要细节，不要为缩略图删减论证，也不要为做成长图补充空话。普通文字默认达到 500 字符也会转图。
- 需要复制的代码、链接或用户明确要求纯文本时，按全局提示词使用 `send_plain_text`；媒体使用已有媒体工具。

生成 `ui` 前读取 [组件契约](references/components.md)。只在使用数据图表时再读 [数据契约](references/data.md)。不确定组件格式时，使用普通 Markdown。

参考不同内容的组合方式，不要照抄其中的内容、模块顺序或来源：

- [概念解释](examples/article.json)：无边框正文与分区。
- [方案比较](examples/comparison.json)：少量卡片、共同维度与选择依据。
- [操作说明](examples/guide.json)：步骤、代码与验证信息。

## Check before sending

检查问题是否已回答、信息是否有依据、分组是否清楚、强调是否有必要、文字是否完整。检查 JSON 字段与容量，确认没有原始 HTML、假交互或未展开内容。完成检查后直接发送正文，不讲述排版过程。
