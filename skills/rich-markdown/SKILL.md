---
name: rich-markdown
description: Compose expressive QQ replies with ordinary Markdown and small static component markers. Use for long explanations, comparisons, practical guides, research summaries and verified data or media; keep short chat and copyable replies as text.
---

# Write content first

先回答核心问题，再沿原因、依据或操作展开。以自然 Markdown 段落、小标题、列表和表格为基础；当组件能让关系、比较、步骤、数据、位置或空间结构更容易理解时，主动加入 1–2 个最合适的组件。直接输出内容，不把整篇回答包进 JSON 或代码围栏。短聊天、简单事实和明确要求复制的内容用文字。普通文字默认达到 500 字符也会转图；QQ 用户可点开、放大查看完整细节，不为凑长图增加字数。

## Use the small component syntax

组件打开行为 `::名称{属性}`，结束行为独立的 `::`，正文直接写 Markdown。文字属性加引号，数字直接写；无属性时省略花括号。

```markdown
::card{title="核心判断" color="blue"}
这里写 **重点** 和自然段落，不需要填写 type/children/text。
::
```

`card` 默认柔和底色，可选 color：neutral/blue/emerald/violet/amber/rose/cyan；variant：muted/outline/ghost。`section` 是无边框分区，可填 title；`grid{columns=2}` 放两列短内容，窄图自动纵向排列。组件可嵌套，每个打开行都要有对应关闭行。基本卡片和分区按上述写法直接输出，无需先读取额外文件。

## Match information relationships

- **解释概念或原因**：沿因果写连贯正文，按机制与应用分区；关键判断可用单张卡片强调，关系确实需要图时加 Mermaid。
- **比较对象**：短概览用 grid 内的卡片，各对象使用不同且一致的颜色；共同维度用普通 Markdown 表格，选择依据写在正文。
- **给出方法**：使用有序列表，步骤较完整时用 `::steps`；每步包含操作、预期结果或检查方法，命令保留 Markdown 代码块。
- **属性、来源和引文**：优先使用 Markdown 列表、链接和引用；确保引用和网址来自实际使用的材料。
- **数据与事件**：确有依据才使用 chart/stats/timeline 的 JSON 代码块，可以放在分区内部。没有数值时用正文或表格，不编造比例、指标或进度。
- **位置与素材**：使用独立整行的 map/image/iframe/three/flow；地图只填写查证过的 WGS84 坐标，Turf.js 分析、地图图层、三维对象和流程图使用声明式字段，最终网页仍输出静态快照。
- **组件数量**：一段较完整的解释通常选一个重点组件；比较、流程或同时存在两种结构时最多选两个。组件必须承载真实信息，不为了装饰把每段文字都放进卡片。

不要为所有回答规定同一套模块或顺序。段落承担完整论证，卡片承载独立对象或重点，不包住每段文字。让标题说明信息关系，避免空泛的“概述／详情／总结”。长说明、宽表格、步骤和媒体纵向占整行，两列只放短内容。颜色用于区分主题，不暗示不存在的好坏。

## Read details only when needed

本技能已在 QQ 主回复前加载，不要重复读取 SKILL.md。以下路径相对 `/skills/rich-markdown/`：

- 复杂嵌套、完整属性或 `steps` 写法：读取 [组件契约](references/components.md)。
- chart/stats/timeline：读取 [数据契约](references/data.md)。
- map/image/iframe/three/flow：读取 [媒体契约](references/media.md)。
- 组合拿不准时选读 [解释](examples/article.md)、[比较](examples/comparison.md) 或 [指南](examples/guide.md)，只参考结构，不复制事实或固定顺序。
- 旧 `ui` JSON 及其中独有组件按需读取 [旧契约](references/legacy-ui.md)，新回复优先用 Markdown 组件。

只使用列出的组件与字面量属性，不写原始 HTML、CSS、JavaScript、表达式、事件或交互控件；Leaflet 和 Three.js 通过受控声明式字段驱动。检查正文完整、组件配对、颜色含义与来源；格式出错可能退回普通正文。用户明确要求纯文本或原样复制时按全局规则使用 send_plain_text，成功后不重复发送。完成后直接发送内容，不描述排版过程。

默认禁止把整篇回答写成 `ui` 代码围栏中的 JSON：不要手写 `type`、`children`、`rendered` 组成的旧信封。`chart`、`stats`、`timeline` 等独立数据代码块仍按各自契约使用；只有用户明确要求旧格式、需要旧契约独有组件，或必须兼容既有调用方时，才读取 [旧契约](references/legacy-ui.md) 并使用 `ui` JSON。
