# Agent Guidelines

## Project Overview

Frontier 是一个基于 NoneBot2 + Milky 适配器的 AI QQ 聊天机器人。核心路径是：Milky 消息事件进入 NoneBot 插件，经过消息归一化、存储、门控和内容安全检查后，由 `deepagents.create_deep_agent()` 驱动对话、工具调用、文件系统后端和媒体工件回复。

**技术栈**: Python 3.14+、NoneBot2/FastAPI、nonebot-adapter-milky、nonebot_plugin_alconna、LangChain/LangGraph/deepagents、SQLModel/SQLite FTS、APScheduler、Playwright、Pillow。

**配置入口**: `env.toml` 是应用配置源，`utils/configs.py` 在模块 import 时读取并暴露 `EnvConfig`。测试会在临时目录生成自己的 `env.toml`。

**运行入口**: `pyproject.toml` 声明 `plugins/` 为 NoneBot 插件目录；`run.sh` / `run.ps1` 最终通过 `uv run nb run` 启动。

---

## Request Lifecycle

一条普通 QQ 消息的主要路径在 `plugins/agent/__init__.py`：

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
       run_serialized(thread_id) 按会话互斥
       _process_agent_request → FrontierCognitive.chat_agent
       create_deep_agent → 工具调用 → extract_uni_messages → send_artifacts/send_messages
```

关键边界：
- 网关在媒体下载前执行，避免未触发回复的图片/视频下载成本。
- 当前消息写入 DB 后再准备历史，但 `prepare_message(..., before_time=msg_time)` 会排除当前消息，只把历史作为上下文。
- 同一 `(user_id, group_id)` 对话通过 `asyncio.Lock` 串行执行，不同会话可并发。
- 私聊会消费 Agent progress 事件并发送“正在思考/调用工具”等进度消息；群聊不发进度消息。

---

## Module Map

### `plugins/` — NoneBot 事件入口

| 模块 | 职责 |
|------|------|
| `plugins/agent` | 核心对话入口：消息提取、引用上下文、文件暂存、DB 写入、回复门控、内容安全、Agent 调度、回复发送 |
| `plugins/clockwork` | APScheduler 定时任务系统：内置任务、用户自动任务、提醒迁移、任务命令、执行历史 |
| `plugins/dashboard` | FastAPI Dashboard：`/api/dashboard/*` API、`/dashboard` 静态前端、JWT 鉴权、状态/消息/设置/任务管理 |
| `plugins/playground` | `/paint`、`/video` 命令和戳一戳响应；直接调用共享图片/视频服务 |
| `plugins/toolbox` | 管理命令：`/update`、`/restart`、`/model`、`/set wake`、`/vehelp`，以及技能沙箱初始化 |

### `utils/` — 共享基础设施

| 文件 | 职责 |
|------|------|
| `agents.py` | `assistant_agent()`、`FrontierCognitive`、Deep Agent backend/middleware/tools 组装、进度事件、会话锁 |
| `database.py` | SQLite/SQLModel、消息/附件/群设置模型、WAL/FTS/索引、历史上下文构造、检索和维护 |
| `message.py` | 消息段提取、文件暂存、媒体下载、回复网关、内容安全、Markdown/图片回复渲染 |
| `configs.py` | `EnvConfig`：从 `env.toml` 读取模型、端点、密钥、功能开关、Dashboard、内容安全配置 |
| `llm_factory.py` | OpenAI-compatible / Google / Anthropic / DeepSeek 模型路由，供应商 profile，能力判断 |
| `signal_llm.py` | 轻量结构化 LLM 调用，用于回复门控、浏览器捕获意图等判断 |
| `reply_context.py` | 引用消息解析、Milky 原消息获取、引用图片下载、转发消息重建 |
| `message_normalizer.py` | 消息段归一化，展开合并转发 derived messages |
| `staged_artifacts.py` | 将工具产出的媒体工件暂存到 `cache/staged_artifacts` 并支持 ID 回传 |
| `markdown_render.py` | Markdown/HTML → 图片，普通文本降级，适配 QQ 文本/图片发送 |
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
| `memory` | `memory` | 聊天记录搜索和总结 |
| `divination` | `iching`, `tarot` | 易经、塔罗 |
| `restricted` | `ens_normal`, `ens_professional`, `webpage_screenshot`, `webpage_recording` | 受控工具：ENS 在 Agent 中显式追加；网页截图/录屏需 Signal LLM 判断用户明确要求 |
| `external` | MCP tools | `mcp.json` 定义的外部工具，首次访问 `agent_tools.mcp_tools` 时懒加载 |

工具注册约定：
- 新工具模块要放在 `tools/` 下，用 `@tool` 装饰函数。
- 如需指定分组，更新 `tools/__init__.py` 的 `_TOOL_MODULE_GROUPS`。
- `response_format="content_and_artifact"` 的工具可返回 `UniMessage` 工件，最终由 `extract_uni_messages()` 和 `send_artifacts()` 发送。
- `artifact_bridge.py` 被自动扫描排除，不要误以为所有测试工具都会暴露给主 Agent。

---

## Agent Construction

`FrontierCognitive.chat_agent()` 的关键行为：
- 使用 `EnvConfig.ADVAN_MODEL` 创建主对话模型；`assistant_agent()` 默认使用 `EnvConfig.BASIC_MODEL`，Signal 判断使用 `EnvConfig.SIGNAL_MODEL`。
- 当模型引用的供应商 `use_responses_api` 为 true 时，主 Agent 会传 `reasoning_effort` 和 `verbosity`；Chat Completions 路径会跳过这些参数。
- 根据模型自身的 `capabilities` 判断是否保留视觉输入；不支持 vision 时会移除图片并追加“图片已省略”提示。
- 构建 `CompositeBackend`：
  - default: `cache/sandbox/workspaces/{workspace_key}`，`LocalShellBackend`
  - `/skills/`: `cache/sandbox/skills`
  - `/memory/{workspace_key}/`: `cache/sandbox/memory/{workspace_key}`
- 对每个 workspace，如果缺少 memory `AGENTS.md`，会从 `prompts/AGENTS.md` 初始化一份。
- middleware 顺序是 `PII → ToolRetry → ModelRetry → FilesystemFileSearch → CodeInterpreter`。
- `interrupt_on` 对 read/write/edit/execute 均关闭，Agent 工具执行不走人工确认。

Prompt 加载链：
- 主 system prompt 来自 `env.toml` 的 `[bot].system_prompt`（旧 `[information]` 仍兼容），由 `FrontierCognitive.load_system_prompt()` 用 `{name}` 注入名称；全局名称/别名来自 `.env` 的 `NICKNAME`，群级数据库唤醒词优先。
- `prompts/AGENTS.md` 是每个 Agent memory workspace 的基础操作规范模板，不是主对话 system prompt。
- `prompts/reply_check.md` 用于群聊是否应主动回复的 Signal LLM 判断。
- `prompts/daily_news.md` 用于每日新闻任务。
- ENS 规则在 `utils/agents.py` 中有硬编码追加，并与 `prompts/ens_rules.md` 同步维护。

---

## Data & Persistence

默认数据库是 `sqlite:///frontier.db`。`utils/database.py` 会：
- 开启 SQLite WAL、busy timeout、cache/mmap、FTS5 支持和面向查询形状的索引。
- 将同步 DB 操作包进 `asyncio.to_thread()`，避免阻塞事件循环；内存库例外。
- 存储普通消息、合并转发 derived messages、图片/附件索引、群级 key-value 设置。
- 通过 `prepare_message()` 将历史消息格式化为 JSON metadata + content，并把可用历史图片重新注入为 `image_url`。

附件和 Agent 文件路径：
- 消息图片和上传文件保存在 `cache/sandbox/memory/{workspace_key}/...`。
- Agent 默认工作区在 `cache/sandbox/workspaces/{workspace_key}`。
- 工具和回复里暴露给 Agent 的虚拟路径通常是 `/memory/{workspace_key}/...` 或 `/skills/...`。

---

## Config Notes

`env.toml.example` 是配置项参考。代码中不要硬编码模型名、provider、base URL 或 API key，使用 `EnvConfig`。

模型路由规则：
- 显式 `*_model_provider` 优先。
- 所有 `*_model_provider`（包括 paint/video）均指向 `[providers.<name>]`；供应商 profile 管理协议类型、base URL、API key 和 Responses API 开关。
- Paint/Video 服务使用 OpenAI-compatible Images/Videos API，因此对应 provider 的 `type` 必须为 `openai`。
- 没有显式 provider 时，`llm_factory.py` 会根据模型名前缀推断：`deepseek*`、`gemini-*`、`claude-*`，其余走 OpenAI-compatible。

Dashboard 配置：
- 默认密码和默认 JWT secret 会在启动时打印安全警告。
- Dashboard settings API 会对敏感值做 mask，并在 masked value 未修改时保留原值。

---

## Key Patterns & Conventions

### 延迟 import 避免循环依赖

`utils/agents.py` 会 import `tools.agent_tools`，而部分工具需要调用 `assistant_agent()`。这类回引必须放在函数体内：

```python
from utils.agents import assistant_agent  # 放在函数内，避免循环依赖
```

不要在 `utils/agents.py` 顶层 import 具体 tool 模块。

### UniMessage 延迟加载

`FrontierCognitive._uni_message_cls()` 用 `require("nonebot_plugin_alconna")` 延迟加载 `UniMessage`。测试中经常 monkeypatch `nonebot.require`，不要把 alconna 加载提前到不必要的模块顶层。

### Agent 返回值约定

`chat_agent()` 返回：

```python
{
    "response": {"messages": [AIMessage(...)]},
    "total_time": float,
    "uni_messages": list[UniMessage],
    "error": str | None,  # 仅错误路径
}
```

`_process_agent_request()` 负责落库 assistant 回复、内容安全清洗、发送媒体工件和最终文本/图片回复。

### 输出发送规则

- 短文本优先走 QQ 文本。
- 长文本、Markdown 表格、LaTeX、Mermaid 等难以纯文本表达的内容走 Markdown → 图片。
- 文本发送失败时会尝试图片回退。
- 多段媒体工件会拆分并串行发送，避免 QQ 消息顺序混乱。

### 权限与高影响操作

Milky 群管理工具会读取 `RunnableConfig.configurable.group_member_role` 做权限判断。新增群管或平台写操作时，需要复用现有权限/上下文解析模式，不要只靠模型自觉。

---

## Gotchas

1. `utils/database.py` 耦合了 schema migration、索引、FTS、附件文件、derived messages 和线程调度。修改前先读相关测试，避免破坏历史注入和搜索性能。

2. `EnvConfig` 在 import 时读取 `env.toml`。运行时 Dashboard 能调用 `EnvConfig.reload()` 更新部分配置，但普通代码不要假设配置文件变更会自动生效。

3. `message_gateway()` 在媒体下载前运行。不要在网关前引入必须下载媒体的逻辑。

4. Browser capture 工具不是普通兜底工具。`webpage_screenshot` / `webpage_recording` 只有在 Signal LLM 判断用户明确要求网页外观/录屏时才暴露。

5. `prompts/AGENTS.md` 是 memory 模板；主 system prompt 在 `env.toml`。更新角色行为时先确认要改的是哪一层。

6. 测试依赖 monkeypatch 和第三方 stub。插件测试通常先 patch `nonebot.require`，再延迟 import `plugins.agent`。

7. 本地可能存在真实 `env.toml`、`.env`、`frontier.db`、`cache/`。做文档或代码变更时不要读取或泄露其中的密钥和私聊数据，除非用户明确要求。

---

## Testing

优先使用项目自己的 uv 环境：

```bash
uv run pytest test/ -x -v
uv run pytest test/utils/agents_test.py -x
uv run pytest --collect-only -q
uv run ruff check .
```

当前测试收集规模约 444 个测试，覆盖：
- Agent 消息主流程和图片/文件记忆
- `FrontierCognitive`、LLM 路由、进度事件
- 消息提取、网关、内容安全、Markdown 渲染
- SQLite schema、索引、FTS、附件清理、历史检索
- Milky 平台工具、媒体工具、ENS/天气/天文/占卜工具
- clockwork 定时任务和 Dashboard API

写测试时的惯例：
- 使用 `nonebug` 的 `App.test_matcher()` 模拟 NoneBot 事件。
- 使用 `monkeypatch` 替换模块级对象，如 `f_cognitive`、`messages_db`、`run_serialized`。
- 测试 fixture 会生成临时 `env.toml`，不要依赖仓库根目录的真实配置。

---

## Engineering Practice

- 先读周围代码和相关测试，再改。
- 变更范围限定在请求行为内，避免无关重构和格式化 churn。
- 新增工具优先复用 `utils/milky_tools.py`、`utils/tool_helpers.py`、`utils/http_client.py` 的既有模式。
- 行为变更要补针对性测试；共享工具、消息主流程、DB schema、权限逻辑尤其需要测试。
- 完成前运行最窄有效测试或 lint；没跑的命令要说明。
- 保留用户或同事已有的工作区修改，不要未经要求 revert。
