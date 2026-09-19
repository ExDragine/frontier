# Agent Guidelines

## Project Overview

Frontier 是一个基于 NoneBot2 + Milky 适配器的 AI QQ 聊天机器人。核心路径是：Milky 消息事件进入 NoneBot 插件，经过消息归一化、存储、门控和内容安全检查后，由 `deepagents.create_deep_agent()` 驱动对话、工具调用、文件系统后端和媒体工件回复。

**技术栈**: Python 3.14+、NoneBot2/FastAPI、nonebot-adapter-milky、nonebot_plugin_alconna、LangChain/LangGraph/deepagents、SQLModel/SQLite FTS、APScheduler、Playwright、Pillow。

**配置入口**: `env.toml` 是应用配置源，`utils/configs.py` 在模块 import 时读取并暴露 `EnvConfig`。测试会在临时目录生成自己的 `env.toml`。

**运行入口**: `pyproject.toml` 声明 `plugins/` 为 NoneBot 插件目录；`run.sh` / `run.ps1` 最终通过 `uv run nb run` 启动。

---

## Request Lifecycle

一条普通 QQ 消息的主要路径在 `plugins/agent/handlers.py`：

```
Milky MessageEvent → NoneBot on_message(priority=10)
  │
  ├─ Phase 1: 快速提取文本和结构化消息段
  │    message_extract → normalize_segments → reply_context
  │    只收集 lazy 媒体下载器和文件信息，不下载图片/视频
  │
  ├─ Phase 2: 消息存储 + 回复网关
  │    MessageDatabase.insert / replace_derived_messages
  │    prepare_message 构造历史上下文
  │    message_gateway 判断黑白名单、to_me、唤醒词、Signal LLM 辅助回复
  │    网关不通过 → common.finish()
  │
  ├─ Phase 3: 媒体下载和附件索引
  │    download_media 并行解析 lazy 媒体
  │    insert_images 将图片写入 cache/sandbox/memory/{workspace}/images
  │
  ├─ Phase 4: 内容安全和群反应
  │    message_check 返回 Safe / Controversial / Unsafe
  │
  └─ Agent 执行
       run_serialized(delivery:workspace) 按群/私聊排队，覆盖执行与发送
       _process_agent_request → FrontierAgentRuntime.run → FrontierCognitive.chat_agent
       managed_agent_turn 在 workspace 锁内管理初始化、超时、取消和结果
       create_deep_agent → 工具调用 → extract_uni_messages → send_artifacts/send_messages
```

关键边界：
- 网关在媒体下载前执行，避免未触发回复的图片/视频下载成本。
- 当前消息写入 DB 后再准备历史，但 `prepare_message(..., before_time=msg_time)` 会排除当前消息，只把历史作为上下文。
- 同一群的不同成员共享 workspace 锁；不同群和不同私聊可并发。QQ 锁顺序是 `delivery:` → `workspace:`，不可反向嵌套。
- 平台消息按机器人和会话去重；当前消息/引用/历史分别分配媒体预算，当前输入优先。
- QQ 最终文本确认发送成功后才写入 assistant 历史；队列与投递失败规则见 `docs/message_flow.md`。
- 私聊会消费 Agent progress 事件并发送“正在思考/调用工具”等进度消息；群聊不发进度消息。

---

## Module Map

### `plugins/` — NoneBot 事件入口

| 模块 | 职责 |
|------|------|
| `plugins/agent` | 核心对话入口：消息提取、引用上下文、文件暂存、DB 写入、回复门控、内容安全、Agent 调度、回复发送 |
| `plugins/clockwork` | APScheduler 定时任务系统：内置任务、用户自动任务、任务命令、执行历史 |
| `plugins/dashboard` | FastAPI Dashboard：`/api/dashboard/*` API、`/dashboard` 静态前端、JWT 鉴权、状态/消息/设置/任务管理 |
| `plugins/playground` | `/paint`、`/video` 命令和戳一戳响应；直接调用共享图片/视频服务 |
| `plugins/toolbox` | 管理命令：`/update`、`/restart`、`/model`、`/set wake`、`/vehelp`，以及技能沙箱初始化 |

`plugins/agent` 的 `handlers.py` 负责事件编排；`message_normalizer.py`、`reply_context.py`、
`chat_context.py`、`gateway.py`、`attachments.py` 分别负责归一化、引用、媒体预算、回复门控和附件暂存。
`plugins/toolbox` 分为 `settings.py`、`update.py`、`menu.py`，专属菜单位于其 `templates/`。
`plugins/clockwork` 的日报模板和提示词位于插件自己的 `templates/`、`prompts/`。
插件包入口只在 NoneBot 加载时注册事件；引用纯组件不应触发注册。

### `utils/` — 共享基础设施

| 文件 | 职责 |
|------|------|
| `agents/` | Agent 包：主 Deep Agent 编排、轻量 Agent、输入适配、进度流、Prompt、workspace、运行时与 Subagent |
| `database.py` | SQLite/SQLModel、消息/附件/群设置模型、WAL/FTS/索引、历史上下文构造、检索和维护 |
| `agents/execution.py` / `agents/runtime_gateway.py` | 内置 Agent 的统一请求/结果、运行 ID、超时和取消边界 |
| `delivery.py` | 不可变投递结果 |
| `agents/sessions.py` / `agents/checkpoints.py` / `agents/session_context.py` | QQ 进程级有界会话、投递租约、官方 saver 适配与跨轮历史预算，默认关闭 |
| `message.py` | 共享消息段提取、媒体下载、内容安全、Markdown/图片回复渲染和投递 |
| `configs.py` | `EnvConfig`：从 `env.toml` 读取模型、端点、密钥、功能开关、Dashboard、内容安全配置 |
| `llm_factory.py` | OpenAI-compatible / Google / Anthropic / DeepSeek 模型路由，供应商 profile，能力判断 |
| `signal_llm.py` | 轻量结构化 LLM 调用，用于回复门控、浏览器捕获意图等判断 |
| `markdown_render.py` | Markdown → 图片，使用本地 Mermaid/ECharts/KaTeX/Prism 渲染增强内容，适配 QQ 文本/图片发送 |
| `browser_capture.py` | Playwright 截图/录屏/页面数据提取，带浏览器重启和超时处理 |
| `paint_service.py` / `video_service.py` | 共享图片和视频生成服务，供命令和 Agent 工具复用 |
| `milky_tools.py` | Milky API 参数解析、路径/URL/base64 输入处理、结果格式化 |
| `http_client.py` | 命名 httpx2 AsyncClient 注册表，统一关闭生命周期 |
| `tool_helpers.py` | LangChain tool state/config 解析，提取用户、群、图片/视频输入 |
| `ens_gate.py` | ENS 气象工具上下文门控 |

### `tools/` — Agent 可调用工具

`tools/__init__.py` 会扫描 `tools/*.py` 中的 LangChain `BaseTool` 对象。当前源码静态统计约 125 个 `@tool` 入口，按模块分到以下组：

| 分组 | 代表模块 | 说明 |
|------|----------|------|
| `main` | `adapter`, `milky_*`, `paint`, `video`, `reminder`, `scheduled_task`, `deepseek_balance`, `NRC*`, `typhoon` | QQ 平台操作、媒体生成、提醒/自动任务、游戏/业务工具 |
| `astro` | `aurora`, `comet`, `heavens_above`, `rocket`, `satellite`, `space_weather` | 天文、卫星、空间天气 |
| `earth` | `earthquake`, `radar`, `weather` | 地震、雷达、天气 |
| `memory` | `memory` | 当前会话最近对话、聊天记录搜索和平台历史读取，由主 Agent 按需调用 |
| `divination` | `iching`, `tarot` | 易经、塔罗 |
| `restricted` | `ens_normal`, `ens_professional`, `webpage_screenshot`, `webpage_recording` | 受控工具：ENS 在 Agent 中显式追加；网页截图/录屏需 Signal LLM 判断用户明确要求 |
| `external` | MCP tools | `mcp.json` 定义的外部工具，首次 Agent 执行通过 `agent_tools.initialize()` 异步加载 |

工具注册约定：
- 新工具模块要放在 `tools/` 下，用 `@tool` 装饰函数。
- 如需指定分组，更新 `tools/__init__.py` 的 `_TOOL_MODULE_GROUPS`。
- `response_format="content_and_artifact"` 的工具可返回 `UniMessage` 工件，最终由 `extract_uni_messages()` 和 `send_artifacts()` 发送。

---

## Agent Construction

`FrontierCognitive.chat_agent()` 的关键行为：
- 构造函数不创建模型或连接 MCP。首轮初始化组件，`EnvConfig.REVISION` 变化后在下一轮重建。
- QQ、用户定时任务和内置 ACP 服务经 `FrontierAgentRuntime.run()` 调用；`chat_agent()` 保留兼容入口。
- 使用 `EnvConfig.ADVAN_MODEL` 创建主对话模型；`assistant_agent()` 默认使用 `EnvConfig.BASIC_MODEL`，Signal 判断使用 `EnvConfig.SIGNAL_MODEL`。
- 当模型引用的供应商 `api_mode` 为 `responses` 时，主 Agent 会传 `reasoning_effort` 和 `verbosity`；其他协议路径会跳过这些参数。
- 根据模型自身的 `capabilities` 判断是否保留视觉输入；不支持 vision 时会移除图片并追加“图片已省略”提示。
- 主 Agent 默认接收当前消息以及 `[storage].query_message_numbers` 控制的最近历史，并直接持有当前会话的最近对话、聊天搜索和平台历史工具；超出窗口的前文按需调用工具获取。Exa / Tavily 联网搜索、网页读取和多来源核验由主 Agent 直接执行并共享主图调用预算，`document-agent` 继承当前 backend 并仅读分析 workspace / memory 文件。一次性本地/API 只读查询工具通过 PTC 交给主 Agent，联网搜索、媒体工件与平台写操作保留为主 Agent 直接工具。
- 文档子代理定义位于 `utils/agents/subagents/`，以声明式配置继承当前 backend，只读访问 workspace / memory 文件；不反向依赖工具注册器。
- Frontier 为四类模型 provider 注册统一 Harness Profile，关闭 Deep Agents 自动添加且工具面重复的 `general-purpose` subagent。
- 模型目录会转换为 LangChain `ModelProfile` 注入模型实例，为 Deep Agents 提供上下文窗口、输出上限和能力元数据；目录外模型继续按未知模型降级。
- 请求身份、群权限和 workspace 使用冻结的 `FrontierRuntimeContext`；媒体等会话数据保留在继承 `DeepAgentState` 的图状态中。
- 构建 `CompositeBackend`：
  - default: `cache/sandbox/workspaces/{workspace_key}`，只提供文件操作的 `FilesystemBackend`
  - `/skills/`: 仓库内置 `skills/`，Agent 只读
  - `/memory/{workspace_key}/`: `cache/sandbox/memory/{workspace_key}`
- 对每个 workspace，如果缺少 memory `SOUL.md`，会创建零字节空文件；群聊按 `group_id` 共享，私聊按 `user_id` 隔离。
- 核心 middleware 顺序是 `PII → ToolRetry → ToolError → ModelCallLimit → ToolCallLimit → ModelRetry → FilesystemFileSearch → CodeInterpreter → Memory`，随后按需追加静默回复、工具搜索和原生网页搜索。
- 主模型 SDK 重试关闭，由 ModelRetry 控制模型重试。图工具错误由 ToolError 统一处理；PTC 直接调用工具，使用独立的异常脱敏包装。平台写操作或未分类工具异常会结束当前轮次，不自动重复。
- 主图模型/工具预算与单次 PTC 脚本预算由 `[limits].agent_model_call_limit / agent_tool_call_limit / agent_ptc_call_limit` 控制；子代理保留独立预算。
- QQ 的 `[sessions]` 开关开启后，同一机器人同一群共享 checkpoint，图仍按请求构建；配置修订不兼容、快照冲突、过期或容量轮换后从 DB 重建。ACP 和定时任务不接入该缓存。运行与投递租约不能被清理器回收，最终内容按实际送达文本校准；媒体轮次结算后释放整代。详见 `docs/agent-sessions.md`。
- QuickJS 使用 `agents/code_interpreter.py` 的 turn 生命周期适配；v3 stream 退出先 abort，再清理进度与解释器，取消时不能遗留后台写入。
- `managed_agent_turn` 收集 LangChain 用量，成功/失败返回 `usage`，取消也保留进程内统计；Dashboard `/api/dashboard/status/usage` 返回最近 100 轮无正文记录。详见 `docs/agent-execution-controls.md`。
- 内置 skills 路径通过 FilesystemPermission 禁止写入。

Prompt 加载链：
- `FrontierCognitive.load_system_prompt()` 组合 `env.toml` 的 `[bot].system_prompt` 与 `prompts/AGENTS.md` 始终适用的全局操作规范；基础人设中的 `{name}` 会按当前唤醒词注入。
- 自定义 `MemoryMiddleware` 从当前 workspace 的 `/memory/{workspace_key}/SOUL.md` 注入动态人设，并同时提供 SOUL 的写入边界与优先级约束。
- 完整的图表、指标卡和时间线渲染契约位于只读内置 Skill `/skills/rich-markdown/SKILL.md`，仅在需要增强 Markdown 时按需加载。
- `plugins/agent/prompts/reply_check.md` 用于群聊是否应主动回复的 Signal LLM 判断。
- `plugins/clockwork/prompts/daily_news.md` 用于每日新闻任务。
- ENS 详细工作流位于只读内置 Skill `/skills/ens-weather/SKILL.md`；主提示词只保留加载入口。

---

## Data & Persistence

默认数据库是 `sqlite:///frontier.db`。`utils/database.py` 会：
- 开启 SQLite WAL、busy timeout、cache/mmap、FTS5 支持和面向查询形状的索引。
- 将同步 DB 操作包进 `asyncio.to_thread()`，避免阻塞事件循环；内存库例外。
- 存储普通消息、合并转发 derived messages、图片/附件索引、群级 key-value 设置。
- `Message.id` 是独立主键，`time` 仅表示时间；附件、转发和 FTS 使用 ID 关联。`insert()` 返回 `MessageInsertResult(message_id, time, inserted)`。
- 启动时检查已有消息表的必要列和主键，只初始化新库并维护索引/FTS，不再迁移旧库；结构要求见 `docs/database-identity-migration.md`。
- 通过 `prepare_message()` 将历史消息格式化为 JSON metadata + content，并把可用历史图片重新注入为 `image_url`。

附件和 Agent 文件路径：
- 消息图片和上传文件保存在 `cache/sandbox/memory/{workspace_key}/...`。
- workspace 动态人设保存在 `cache/sandbox/memory/{workspace_key}/SOUL.md`。
- Agent 默认工作区在 `cache/sandbox/workspaces/{workspace_key}`。
- 工具和回复里暴露给 Agent 的虚拟路径通常是 `/memory/{workspace_key}/...` 或 `/skills/...`。

---

## Config Notes

`env.toml.example` 是配置项参考；仅接受显式 `config_version = 2`，旧配置分区、provider 别名、`use_responses_api` 和绘图尺寸迁移已移除。代码中不要硬编码模型名、provider、base URL 或 API key，使用 `EnvConfig`。

模型路由规则：
- 显式 `*_model_provider` 优先。
- 所有 `*_model_provider`（包括 paint/video）均指向 `[providers.<name>]`；供应商 profile 用 `type` 管理 LangChain 适配器、用 `api_mode` 管理协议，并统一保存 base URL 和 API key。Signal 的结构化策略由可选 `structured_output_method` 指定，默认 `auto`。
- Paint/Video 服务使用 OpenAI-compatible Images/Videos API，因此对应 provider 的 `type` 必须为 `openai`。
- 官方 OpenAI / DeepSeek Responses 路由会自动启用服务端 `web_search`；兼容代理只有在确认支持该托管工具后，才可在 provider profile 中显式设置 `native_web_search = true`。
- 没有显式 provider 时，`llm_factory.py` 会根据模型名前缀推断：`deepseek*`、`gemini-*`、`claude-*`，其余走 OpenAI-compatible。

Dashboard 配置：
- 默认密码和默认 JWT secret 会在启动时打印安全警告。
- Dashboard settings API 会对敏感值做 mask，并在 masked value 未修改时保留原值。
- 保存配置使用串行事务、独立临时文件和原子替换，失败会回滚；成功 reload 才递增 `EnvConfig.REVISION`。`.env` 和 `mcp.json` 变更仍需重启。

---

## Key Patterns & Conventions

### 延迟 import 避免循环依赖

`utils/agents/cognitive.py` 会 import `tools.agent_tools`，而部分工具需要调用 `assistant_agent()`。这类回引必须放在函数体内：

```python
from utils.agents import assistant_agent  # 放在函数内，避免循环依赖
```

不要在 `utils/agents/cognitive.py` 顶层 import 具体 tool 模块。

### UniMessage 延迟加载

Agent 提取工件时延迟从 `utils.alconna` 加载 `UniMessage`，只接受真实 `UniMessage` 工件；MCP 返回的普通字典不进入 QQ 发送器。测试中经常 monkeypatch `nonebot.require`，不要把 alconna 加载提前到不必要的模块顶层。

### Agent 返回值约定

`chat_agent()` 返回：

```python
{
    "response": {"messages": [AIMessage(...)]},
    "total_time": float,
    "uni_messages": list[UniMessage],
    "should_reply": bool,
    "status": "success" | "silent" | "failed" | "timeout",
    "run_id": str,
    "error": str | None,  # 仅错误路径
}
```

`_process_agent_request()` 负责内容安全清洗、发送媒体工件和最终文本/图片回复，并在最终回复发送成功后落库。发送函数返回 `DeliveryResult`，生成成功和送达成功分别判断。

### 输出发送规则

- 短文本优先走 QQ 文本。
- 长文本、Markdown 表格、LaTeX、Mermaid，以及 `chart`/`stats`/`timeline` 增强块走 Markdown → 图片。
- 文本发送失败时会尝试图片回退。
- 多段媒体工件会拆分并串行发送，避免 QQ 消息顺序混乱。

### 权限与高影响操作

Milky 群管理工具会读取 `RunnableConfig.configurable.group_member_role` 做权限判断。新增群管或平台写操作时，需要复用现有权限/上下文解析模式，不要只靠模型自觉。

---

## Gotchas

1. `utils/database.py` 仍包含索引、FTS、附件文件、derived messages 和线程调度；历史迁移已移除，启动时检查当前表结构。修改前先读相关测试，避免破坏历史注入和搜索性能。

2. `EnvConfig` 在 import 时读取 `env.toml`。运行时 Dashboard 能调用 `EnvConfig.reload()` 更新部分配置，但普通代码不要假设配置文件变更会自动生效。

3. `message_gateway()` 在媒体下载前运行。不要在网关前引入必须下载媒体的逻辑。

4. Browser capture 工具不是普通兜底工具。`webpage_screenshot` / `webpage_recording` 只有在 Signal LLM 判断用户明确要求网页外观/录屏时才暴露。

5. 提示词分为常驻层和按需层：`env.toml` 基本人设与 `prompts/AGENTS.md` 全局规范常驻，workspace `SOUL.md` 由 Memory middleware 注入，详细工作流与渲染契约保存在 Skills 中按需加载。修改前先确认目标层级。

6. 测试依赖 monkeypatch 和第三方 stub。插件测试通常先 patch `nonebot.require`，再延迟 import `plugins.agent.handlers`。

7. 本地可能存在真实 `env.toml`、`.env`、`frontier.db`、`cache/`。做文档或代码变更时不要读取或泄露其中的密钥和私聊数据，除非用户明确要求。

---

## Testing

优先使用项目自己的 uv 环境：

```bash
uv sync --locked --group dev
uv run --locked pytest test/ -x -v
uv run --locked pytest test/utils/agents_test.py -x
uv run --locked pytest --collect-only -q
uv run --locked ruff check .
```

测试规模以 `--collect-only` 输出为准，覆盖：
- Agent 消息主流程和图片/文件记忆
- `FrontierCognitive`、LLM 路由、进度事件
- 消息提取、网关、内容安全、Markdown 渲染
- SQLite schema、索引、FTS、附件清理、历史检索
- Milky 平台工具、媒体工具、ENS/天气/天文/占卜工具
- clockwork 定时任务和 Dashboard API
- 独立进程中的真实 LangChain/Deep Agents/MCP 契约、取消/超时、旧结构拒绝启动、消息身份和投递失败

写测试时的惯例：
- 使用 `nonebug` 的 `App.test_matcher()` 模拟 NoneBot 事件。
- 使用 `monkeypatch` 替换模块级对象，如 `f_cognitive`、`messages_db`、`run_serialized`。
- 测试收集阶段和每项测试均使用临时目录与 v2 `env.toml`，不要依赖仓库根目录的真实配置。

---

## Engineering Practice

- 先读周围代码和相关测试，再改。
- 变更范围限定在请求行为内，避免无关重构和格式化 churn。
- 新增工具优先复用 `utils/milky_tools.py`、`utils/tool_helpers.py`、`utils/http_client.py` 的既有模式。
- 行为变更要补针对性测试；共享工具、消息主流程、DB schema、权限逻辑尤其需要测试。
- 完成前运行最窄有效测试或 lint；没跑的命令要说明。
- 保留用户或同事已有的工作区修改，不要未经要求 revert。
