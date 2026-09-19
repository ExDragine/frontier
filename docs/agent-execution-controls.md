# Agent 执行控制

## 调用预算

在 `env.toml` 的 `[limits]` 中配置，均为大于等于 1 的整数：

| 字段 | 默认值 | 计数范围 |
| --- | --- | --- |
| `agent_model_call_limit` | 20 | 一轮主 Agent 图中的模型轮数 |
| `agent_tool_call_limit` | 40 | 一轮主图的工具调用，包含子代理委托和 PTC 脚本执行 |
| `agent_ptc_call_limit` | 20 | 每次 PTC 脚本内部的工具桥接调用 |

这些不是全系统共享额度。Exa / Tavily 搜索和网页读取直接消耗主图工具预算；文档子代理保留每次委托 6 轮模型、8 次工具的独立预算。模型中间件重试不消耗额外主图轮数，但实际 LangChain 调用会记入用量。服务端原生工具不属于图工具计数。单次模型/整轮任务的超时配置继续生效。

主图预算耗尽时停止继续执行，返回 `status="failed"`、`error_code="budget_exceeded"` 和明确中文提示，不重新运行整个任务。此前已完成的外部操作不会回滚。PTC 脚本内部超过桥接预算会返回解释器错误，后续仍受主图预算约束。

## 用量统计

`AgentResult.usage` 包含：

- `model_calls`、`model_errors`：LangChain 模型调用及失败次数。
- `input_tokens`、`output_tokens`、`total_tokens`。
- `cache_read_tokens`、`reasoning_tokens`：分别是输入和输出 token 的明细，不应再次加到总 token。
- `usage_reported_calls`、`usage_missing_calls`：有/无供应商用量回报的调用数。
- `tool_calls`、`tool_errors`：实际触发回调的工具调用，包含子代理和 PTC 内部调用；因此不等同于主图工具预算计数。
- `models`：按模型及 `main / document / assistant / signal / other` 分项统计。

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
| `auto` | Google 使用 JSON Schema；声明支持原生结构化输出的官方 OpenAI/Anthropic 路由使用 JSON Schema；DeepSeek 路由（`type = "deepseek"` 或官方 Responses/Anthropic 端点）改用 `text_json`，因为思考模式默认开启、只接受 `tool_choice: auto`，且官方模型别名可能没有能力卡片；Anthropic 或声明支持工具调用的其他模型使用 function calling；其余 OpenAI-compatible 路由回退 JSON 模式 |
| `json_schema` | 显式使用供应商 schema 能力，OpenAI 适配器同时设置 `strict=True` |
| `function_calling` | 使用工具参数 schema |
| `json_mode` | 提示词附完整 JSON Schema，并请求供应商的 JSON 模式；返回值由 Pydantic 校验 |
| `text_json` | 提示词附完整 JSON Schema，不注册工具、也不设置 `response_format`，按普通文本解析后由 Pydantic 校验；用于思考模式等拒绝强制 `tool_choice` 的路由 |

调用方显式指定 `method` 的优先级高于 provider 配置。兼容代理不会仅因模型名就自动启用原生 schema；可按实际协议支持显式指定。DeepSeek 自动选择不设置 strict，不切换到 beta endpoint；DeepSeek 路由在 `auto` 下只把 schema 放进提示词，不再强制工具调用，需要强制工具 schema 时显式设置 `structured_output_method = "function_calling"`（思考模式关闭后可用）。

每个 `[providers.<name>]` 还可设置 `signal_extra_body`（默认空表）：其中的键合并进 Signal 请求的 `extra_body`，用于传递供应商侧的推理开关等参数，例如 DeepSeek 的 `{"thinking": {"type": "disabled"}}`（思考模式默认开启，effort 默认 `high`）。它只作用于 Signal 轻量调用，不进入主 Agent；调用点显式传入的 `extra_body` 覆盖同名键。该字段经 OpenAI-compatible 与 DeepSeek 适配器透传，Messages 路由不接收此参数；关闭思考后如需回到强制工具 schema，可再显式设置 `structured_output_method = "function_calling"`。

无论采用哪种策略，Signal 均校验最终 Pydantic 结果。解析失败或供应商拒绝后不会自行再发一次请求来切换协议。轻量 Agent 的 `response_format` 继续使用 LangChain 原有的结构化策略。
