# Agent 执行控制

## 调用预算

在 `env.toml` 的 `[limits]` 中配置，均为大于等于 1 的整数：

| 字段 | 默认值 | 计数范围 |
| --- | --- | --- |
| `agent_model_call_limit` | 20 | 一轮主 Agent 图中的模型轮数 |
| `agent_tool_call_limit` | 40 | 一轮主图的工具调用，包含子代理委托和 PTC 脚本执行 |
| `agent_ptc_call_limit` | 20 | 每次 PTC 脚本内部的工具桥接调用 |

这些不是全系统共享额度。研究子代理仍为每次委托最多 5 轮模型、6 次工具；文档子代理仍为 6 轮模型、8 次工具。模型中间件重试不消耗额外主图轮数，但实际 LangChain 调用会记入用量。服务端原生工具不属于图工具计数。单次模型/整轮任务的超时配置继续生效。

主图预算耗尽时停止继续执行，返回 `status="failed"`、`error_code="budget_exceeded"` 和明确中文提示，不重新运行整个任务。此前已完成的外部操作不会回滚。PTC 脚本内部超过桥接预算会返回解释器错误，后续仍受主图预算约束。

## 用量统计

`AgentResult.usage` 包含：

- `model_calls`、`model_errors`：LangChain 模型调用及失败次数。
- `input_tokens`、`output_tokens`、`total_tokens`。
- `cache_read_tokens`、`reasoning_tokens`：分别是输入和输出 token 的明细，不应再次加到总 token。
- `usage_reported_calls`、`usage_missing_calls`：有/无供应商用量回报的调用数。
- `tool_calls`、`tool_errors`：实际触发回调的工具调用，包含子代理和 PTC 内部调用；因此不等同于主图工具预算计数。
- `models`：按模型及 `main / research / document / assistant / signal / other` 分项统计。

统计作用域是 `managed_agent_turn`，跨并发会话隔离，覆盖该轮内的 LangChain 子调用、模型中间件重试和摘要调用。成功、失败、超时均返回已有用量；取消继续传播 `CancelledError`，同时保留截至取消时的统计。

不包含进入该轮之前的独立网关判断、外部 ACP 进程的模型消耗、独立图片/视频 SDK 费用。SDK 内部 HTTP 重试不会单独触发 LangChain 模型开始事件。供应商未返回的 token 不估算为已知用量，也不据此估算账单金额。

Dashboard 总览显示累计数据，认证后的 `GET /api/dashboard/status/usage` 返回累计值和最近 100 轮明细。统计保存在当前进程内，重启清零；日志亦按 `run_id` 记录每轮用量。明细不存聊天正文、工具参数、QQ 身份或异常原始响应。

## 工具错误

- 已确认只读工具：异常转换为脱敏的错误结果，模型可依据已有证据继续；限流时明确停止重复查询和切换搜索后端。
- 写操作或未分类工具：异常结束当前轮次，返回 `tool_execution_uncertain`，提示核实此前操作是否生效；不自动重试或邀请模型重复执行。
- 取消、中断和预算异常保持控制流语义，不转换成普通查询失败。
- 参数绑定错误继续由 LangChain 的工具校验处理；已有工具主动返回的业务提示保持原样。
- PTC 工具通过 QuickJS 直接调用 `arun`，不经过图中间件。注册给 PTC 的工具会复制并包装同步/异步入口，避免原始异常文本进入解释器结果；原工具对象不被修改。

## Signal 结构化输出

每个 `[providers.<name>]` 可设置 `structured_output_method`：

| 值 | 行为 |
| --- | --- |
| `auto` | Google 使用 JSON Schema；声明支持原生结构化输出的官方 OpenAI/Anthropic 路由使用 JSON Schema；DeepSeek、Anthropic 或声明支持工具调用的模型使用 function calling；其他 OpenAI-compatible 路由回退 JSON 模式 |
| `json_schema` | 显式使用供应商 schema 能力，OpenAI 适配器同时设置 `strict=True` |
| `function_calling` | 使用工具参数 schema |
| `json_mode` | 提示词附完整 JSON Schema，并由 Pydantic 校验返回值 |

调用方显式指定 `method` 的优先级高于 provider 配置。兼容代理不会仅因模型名就自动启用原生 schema；可按实际协议支持显式指定。DeepSeek 自动选择不设置 strict，不切换到 beta endpoint。

无论采用哪种策略，Signal 均校验最终 Pydantic 结果。解析失败或供应商拒绝后不会自行再发一次请求来切换协议。轻量 Agent 的 `response_format` 继续使用 LangChain 原有的结构化策略。
