# Data component contracts

既可以独立使用 `chart/stats/timeline` fenced block，也可以在 `ui` 中用 `{"type":"chart","config":{...}}` 的形式组合。
数据必须有依据。默认使用安静的中性色；状态色只表达实际状态，不作为装饰。

## Chart

柱状图/折线图：`type` 为 `bar/line`，`labels` 必填（1–200 项），`series` 必填（1–8 项）；每项 `name`（80）、`values`（有限数值）必填，点数与 labels 一致。
饼图：`type` 为 `pie`，`data` 必填（1–12 项），每项 `name`（80）、`value`（非负数）必填，至少一个值大于零。不混用 labels/series。
通用可选字段：`title`（200）、`unit`（80）、`show_legend`（默认 true）。不能传颜色、函数、任意 option。

```json
{"type":"bar","title":"示例数据","labels":["A","B"],"series":[{"name":"次数","values":[12,8]}]}
```

不同量纲、差距悬殊或内容很多的数据拆成独立图表。缺少数值时用文字或表格，不编造数字。

## Stats

必填 `items`（1–12 项）；每项 `label`（80）、`value`（文字，200）必填，`unit`（80）、`detail`（200）、`status` 可选。
可选 `title`（200）、`columns`（1–4，默认 3）、`variant`：`plain`（默认，无框指标组）或 `cards`（独立指标卡）。

```json
{"columns":2,"variant":"plain","items":[{"label":"示例指标 A","value":"12","unit":"项"},{"label":"示例指标 B","value":"8","unit":"项"}]}
```

`value` 不一定是数字，但 stats 用于需要突出数值/结果的摘要；一般属性用 facts。

## Timeline

必填 `items`（1–50 项）；每项 `time`（80）、`title`（200）必填，`content`（2000）、`status` 可选；顶层 `title`（200）可选。
`status` 为 `neutral/success/warning/danger`，默认 neutral。用于真实事件顺序；待执行指南优先用 steps。

```json
{"items":[{"time":"09:00","title":"开始构建","status":"success"},{"time":"09:12","title":"进入验证","content":"等待检查结果"}]}
```
