---
name: rich-markdown
description: Choose and compose expressive QQ replies for long explanations, comparisons, practical guides, research summaries and data. Match sections, colored cards, tables, steps and media to information relationships; keep short chat and copyable replies as text.
---

# Compose the reading path

先回答读者最关心的问题，再用结构表达依据。长解释、比较、指南与研究总结默认用 `ui` 组织；日常短聊天、简单事实、需要原样复制或明确要求纯文本的回答直接用文字。按内容需要展开，不为凑长图增加字数。普通文字默认达到 500 字符也会转图；QQ 用户可以点开、放大查看完整细节。

## Match the relationship

- **解释原因或概念**：用 `prose` 写连贯论证，用 `section` 划分原因、机制或应用；重要判断用粗体或 `text` 的 `lead` 变体。需要展示关系时加 Mermaid，不把因果拆成孤立的标签。
- **比较多个对象**：短概览用 `grid` + `card`，同一组维度用 `table`，选择依据放在正文。为并列对象选不同的 `color`，在同一回答中保持对应一致。
- **给出操作方法**：用 `steps`，每一步说明操作、预期结果或检查方法；需要复制的命令保留完整代码，背景与例外放在步骤前后。
- **列出属性或要点**：同一对象的属性用 `facts`；有标题和解释的要点用 `list`，根据分组需要选 `plain/divided/outline`。
- **说明数据或事件**：确有数值才用 `stats/chart`，真实事件顺序用 `timeline`。缺少数据时用正文或表格，不编造指标、比例或进度。
- **展示位置或素材**：用独立整行的 `map/image/iframe`，只用查证过的坐标与确实用于回答的公开 URL。网页只能展示静态快照。

不要为所有回答规定同一套模块或顺序。正文与无边框分区承担完整解释；卡片承载独立对象、并列方案或需要强调的分组，不包住每段文字。`alert` 只强调实际异常或限制，`badge` 只标记真实状态，`quote/sources` 只引用实际使用过的内容和来源。

## Compose with restraint

让标题说明信息关系，避免连续使用“概述／详情／总结”这类空泛标签。先选最能帮助理解的结构，再添加必要的视觉强调；不要把整篇解释塞进一个 `prose`。

卡片颜色可用 `neutral/blue/emerald/violet/amber/rose/cyan`；`muted` 提供柔和底色，`outline` 提供描边与顶部强调，`ghost` 弱化边框。让颜色区分主题或对象，不凭颜色暗示不存在的好坏。长说明、表格、图表和步骤纵向占整行，两列只放适合并列阅读的短内容。

`prose.text` 支持 Markdown 段落、强调、列表、代码和公式，其他文字字段按纯文字填写。输出一个或多个严格 JSON 的 `ui` 代码块；不输出原始 HTML、CSS、JavaScript、按钮或依赖交互才能阅读的内容。遵守字段与容量限制，必要时拆为多个分区或 `ui` 块。素材不足时省略对应模块，保留其他已有内容。

## Load only the needed contracts

本技能正文已在 QQ 主回复中预先加载；不要重复读取 SKILL.md。以下路径相对 `/skills/rich-markdown/`：

- **生成任何 `ui` 前**读取 [组件契约](references/components.md)，核对字段与限制。
- 使用 `chart/stats/timeline` 时读取 [数据契约](references/data.md)。
- 使用 `map/image/iframe` 时读取 [媒体契约](references/media.md)。
- 对组合方式拿不准时选读 [概念解释](examples/article.json)、[方案比较](examples/comparison.json) 或 [操作说明](examples/guide.json)；只参考结构，不复制示例事实、来源或固定顺序。

检查直接答案、完整论证、分组与颜色的含义、严格 JSON 和容量。用户需要原样复制或明确要求纯文本时，按全局规则使用 `send_plain_text`；成功后不重复发送正文。完成后直接发送内容，不讲述排版过程。
