# Agent 流式进度事件设计

> 2026-06-11 · 状态：设计完成，待用户审阅

## 目标

将 `chat_agent()` 内部从 `agent.ainvoke()` 迁移到 `agent.astream_events(version="v3")`，让私聊用户在执行期间看到 Agent 正在做什么（思考中、调用工具、启动子代理），消除"干等几十秒无反馈"的体验问题。

非目标：群聊不改；定时任务不改；不引入逐 token 流式文本输出。

## 方案选择

**方案 A：回调式 ProgressReporter**（采用）

- `chat_agent()` 新增可选参数 `progress_reporter: Callable[[ProgressEvent], Awaitable[None]] | None`
- agent 内部用 `astream_events` 双路消费：一路收集进度事件回调 reporter，一路等 `stream.output` 拿最终结果
- 私聊传入 reporter；群聊和定时任务不传，行为与当前完全一致
- 返回值结构不变（dict），向后兼容

## 事件模型

### ProgressEvent

```python
@dataclass
class ProgressEvent:
    type: Literal[
        "thinking",         # Agent 开始思考
        "tool_call",        # 正在调用工具
        "tool_result",      # 工具执行完成
        "subagent_start",   # 子代理启动
        "subagent_done",    # 子代理完成
        "text_delta",       # 文本增量（预留，暂不消费）
        "done",             # 执行完成/出错
    ]
    message: str            # 中文描述
    detail: dict | None     # 结构化附加信息
```

### 事件映射规则（agent 层 _collect_progress）

| 底层投影 | 触发条件 | 生成的 ProgressEvent |
|---|---|---|
| `stream.messages` (首个) | 第一次收到 LLM 消息 | `thinking` |
| `stream.tool_calls` | 每个工具调用开始 | `tool_call`（含 tool_name） |
| `stream.tool_calls` | 每个工具调用完成 | `tool_result` |
| `stream.subagents` | 子代理状态变为 started | `subagent_start`（含 subagent_name） |
| `stream.subagents` | 子代理状态变为 completed/failed | `subagent_done` |
| `stream.messages` (text_delta) | 段落级累积（`\n\n` 切分） | `text_delta`（预留，暂不消费） |
| 执行完成/异常 | gather 完成或 catch | `done` |

### 节流策略

- 工具调用/子代理事件：不做节流，每个事件都发（本身频率低）
- `text_delta`：按 `\n\n`（段落分隔）切分后发送，不做时间聚合
- `text_delta` 代码保留但 reporter 层暂不消费（markdown 有结构，拆开发送会破坏格式）

## 架构

```
chat_agent() 内部:

    stream = agent.astream_events(input_data, config=config, version="v3")

    progress_task = asyncio.create_task(_collect_progress(stream, reporter))
    output_task   = asyncio.create_task(_collect_output(stream))

    final_state = await output_task       # output 优先，不因 progress 异常卡住
    await progress_task                   # 确保 cleanup

    return final_state  # 结构与 ainvoke 完全一致
```

- `_collect_progress`：遍历 stream 的 projections，将底层事件翻译为 ProgressEvent 并调用 reporter；reporter 为 None 时直接跳过
- `_collect_output`：等待 `stream.output`，同时收集 artifact（从 tool message 提取 UniMessage），返回 dict

## 异常处理

```
try:
    ...astream_events + gather...
except asyncio.TimeoutError:
    → reporter("⏰ 思考超时") → raise（外层现有 except 块兜底）
except Exception:
    → reporter("💥 执行出错") → raise
```

- reporter 自身异常用 try/except 包裹，log warning 后继续执行，不中断 agent
- output_task 完成后才 await progress_task，避免 progress 异常阻塞结果收集

## 私聊 Reporter 实现

在 `_process_agent_request` 中，`group_id is None` 时构造：

```python
async def _private_chat_reporter(event: ProgressEvent) -> None:
    match event.type:
        case "thinking":
            await UniMessage.text("🤔 正在思考…").send()
        case "subagent_start":
            await UniMessage.text(f"🔍 {event.message}").send()
        case "tool_call":
            await UniMessage.text(f"🔧 {event.message}").send()
        case "subagent_done" | "tool_result" | "text_delta" | "done":
            pass  # 静默
```

- `subagent_done` / `tool_result`：不发送，避免冗余和内部数据泄露
- `text_delta`：不发送，markdown 结构不能拆
- `done`：不发送，最终结果由现有 `send_messages` 流程处理

## 涉及文件

| 文件 | 改动 |
|---|---|
| `utils/agents.py` | ProgressEvent 定义；`_collect_progress` / `_collect_output`；`chat_agent()` 新增 `progress_reporter` 参数 |
| `plugins/agent/__init__.py` | `_process_agent_request` 中当 `group_id is None` 时构造并传入 `_private_chat_reporter` |

## 向后兼容

- `chat_agent()` 返回值 dict 结构不变
- 不传 `progress_reporter` 时行为与 `ainvoke` 时期完全一致
- 现有测试无需修改
- `assistant_agent()` 和 `SignalLLM` 不做改动
