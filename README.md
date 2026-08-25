# Frontier

Frontier 是一个基于 [NoneBot2](https://nonebot.dev/) 和 Milky 适配器的 AI QQ 聊天机器人。它把 QQ 消息接入 LangGraph/deepagents 驱动的 Deep Agent，支持多模型路由、工具调用、文件系统工作区、图片/视频生成、聊天记录检索、定时任务和 Web 管理面板。

## 核心架构

```
QQ / Milky MessageEvent
  ↓
plugins/agent on_message(priority=10)
  ↓
文本/消息段提取 → 消息归一化 → 引用上下文 → DB 存储
  ↓
message_gateway 门控（黑白名单 / @ / 唤醒词 / Signal LLM）
  ↓
媒体下载 + 内容安全检查
  ↓
FrontierCognitive.chat_agent()
  ↓
deepagents.create_deep_agent()
  ↓
工具调用 / 文件系统后端 / memory / code interpreter
  ↓
UniMessage 文本、图片、视频或文件回复
```

主要设计点：
- **先存储、后门控、再下载媒体**：未触发回复的图片/视频不会被下载。
- **会话串行**：同一用户/群聊线程通过 `asyncio.Lock` 串行执行，不同线程可并发。
- **多模型路由**：OpenAI-compatible、Google Gemini、Anthropic Claude、DeepSeek 统一由 `utils/llm_factory.py` 创建。
- **文件系统工作区**：群聊使用 `group-{group_id}`、私聊使用 `dm-{user_id}`，同一个裸数字不会共享 workspace 或 memory。
- **分层提示词**：`env.toml` 定义基础人设，`prompts/AGENTS.md` 定义全局操作规范，`prompts/rendering.md` 定义渲染规范，workspace `SOUL.md` 保存动态人设与长期偏好。
- **媒体工件直发**：工具返回的 `UniMessage` artifact 会被提取并直接发送到 QQ。

## 功能模块

| 插件 | 功能 |
|------|------|
| `plugins/agent` | 核心对话引擎：消息处理、回复门控、内容安全、Deep Agent 调度、回复渲染 |
| `plugins/acp` | `/acp` 外部 ACP Agent 桥接 |
| `plugins/clockwork` | APScheduler 定时任务：提醒、用户自动任务、每日新闻、APOD、地震/NRC 等推送 |
| `plugins/dashboard` | Web 管理面板：JWT 登录、状态、消息浏览、配置管理、任务管理 |
| `plugins/playground` | `/paint` 图片生成、`/video` 视频生成、戳一戳响应 |
| `plugins/toolbox` | `/update`、`/restart`、`/model`、`/set wake`、`/vehelp` 等管理命令 |

## Agent 工具能力

`tools/` 下的 LangChain 工具会被自动发现并按组注册。当前源码约有 125 个 `@tool` 入口，覆盖：

| 类别 | 示例 |
|------|------|
| 平台操作 | 发送消息/图片/视频/文件，好友、群组、群文件、公告、精华、反应、戳一戳 |
| 子代理 | `memory-agent` 检索历史，`research-agent` 核验网络资料，`document-agent` 只读分析本地文档 |
| 媒体生成 | AI 绘图、图片编辑、AI 视频 |
| 自动任务 | 创建、列出、暂停、恢复、取消用户自动任务 |
| 网络与资料 | MCP 外部工具 |
| 天文空间 | 极光、彗星、卫星图、火箭发射、空间天气 |
| 地球与天气 | 主 Agent 通过 PTC 执行纯文本查询；雷达、风场图、台风和 ENS 媒体保留直接工具 |
| 游戏/业务工具 | NRC 远行商人、精灵蛋、活动日历等 |
| 占卜 | 易经、塔罗 |

部分工具是受限工具：网页截图/录屏只有在用户明确要求查看网页外观或录制页面时才暴露；ENS 专业气象工具有独立前缀和门控规则。
工具执行分为三层：媒体工件、平台写操作和未分类 MCP 工具由主 Agent 直接调用；一次性只读查询仅通过 PTC 暴露；需要多轮检索与压缩上下文的任务交给有严格工具与模型调用预算的专用子代理。

仓库内置工作流位于 `skills/`，运行时以只读方式挂载到 `/skills`，按描述渐进加载；Agent 不再拥有宿主 Shell，也不会在启动时从远端下载 Skill。
`memory-agent`、`research-agent` 和 `document-agent` 定义位于 `utils/agents/subagents/`，
主 Agent 只向它们注入各自所需的最小能力集。文档代理继承当前会话 backend，但全局禁止写入。

## 技术栈

| 层面 | 技术 |
|------|------|
| 运行时 | Python 3.14+、uv |
| Bot 框架 | NoneBot2、FastAPI driver、nonebot-adapter-milky、nonebot_plugin_alconna |
| Agent | LangChain、LangGraph、deepagents、langchain-quickjs |
| 模型 | OpenAI-compatible、Google Gemini、Anthropic Claude、DeepSeek |
| 存储 | SQLite、SQLModel、FTS5、WAL |
| 渲染/浏览器 | Playwright、markdown-it-py、Mermaid、Apache ECharts、KaTeX、Prism |
| 定时任务 | nonebot-plugin-apscheduler / APScheduler |
| 部署 | Docker、docker compose、uv |

## 快速开始

### 环境要求

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Playwright 浏览器依赖
- 可用的 Milky 服务和对应 NoneBot 配置
- 至少一个可用 LLM API key

### 安装

```bash
uv sync
uv run playwright install

cp .env.example .env
cp env.toml.example env.toml
```

内容检查模型默认不安装。需要在本机启用 `[content_check]` 时，安装 CPU-only 可选依赖：

```bash
uv sync --extra content-check
```

[Agent Client Protocol (ACP)](https://agentclientprotocol.com/) 是 Frontier 的内置能力。
复制配置后即可接入一个或多个外部 ACP Agent：

```bash
cp acp.json.example acp.json
```

在 `acp.json` 中配置一个或多个通过 stdio 提供 ACP v1 的 Agent 后，可使用
`/acp <任务>`，或通过 `/acp --agent <名称> <任务>` 选择 Agent。`/acp --list`、
`/acp --cancel` 和 `/acp --reset` 分别用于查看、取消当前 turn 和重建会话；命令访问
沿用 `env.toml` 的 `[agent_policy]`。
每个群聊或私聊 scope 使用 `cache/acp/workspaces/` 下的独立工作区。ACP Agent 是本地
子进程，工作区并非操作系统 sandbox；它仍可能访问 Frontier 进程有权限读取的其他路径。
`permission_policy` 默认为 `deny`，只有明确将其改为 `allow_once` 或 `allow_always` 时，
Frontier 才会自动批准 Agent 的工具权限请求。需要 ACP 协议认证的 Agent 可通过
`auth_method` 指定其在初始化阶段公布的认证方式 ID。`inherit_env` 是显式环境变量白名单，
只会把列出的宿主变量传给对应子进程；缺少任何一项都会拒绝启动。每日缓存维护会关闭闲置
ACP 进程并删除其 workspace；正在执行的 scope 不受影响。

将某个 Agent 的 `expose_as_subagent` 设为 `true` 后，它会以 `acp-<名称>` 注册为
DeepAgents 子代理，主 Agent 可以按 `description` 将任务委托给它。子代理返回的媒体会保存到
当前 Frontier workspace 的 `/acp-artifacts/`，不会把大段 base64 直接塞回模型上下文。
该开关默认关闭，避免仅用于 `/acp` 的进程被模型意外调用。

Frontier 自身也提供 ACP v1 stdio server，可供 ACP 客户端（包括日后的独立前端或其他
Agent）启动：

```bash
uv run python scripts/frontier_acp.py
```

这个入口复用同一个 `FrontierCognitive` 执行链，支持文本、图片和音频输入，并把已清洗的
进度、工具状态、最终文本及内联媒体映射为 ACP 更新。每个 ACP session 使用独立的内部
身份、thread 和 sandbox workspace；客户端传入的 `cwd` 只作为协议元数据，不会成为文件
访问授权。为防止权限继承和 Agent 环路，ACP 入站会话不暴露 QQ 平台工具、聊天记忆和
ACP 子代理，只保留隔离 workspace、文档分析及模型原生能力。

当前 Python SDK 的稳定协议是 ACP v1，因此 server 与 client 以 v1 为兼容基线；ACP v2
仍处于草案阶段，后续会在 SDK 提供稳定协商支持后并行增加 v2 turn/state 生命周期，而不
破坏现有 v1 配置。

DeepSeek Harness 不再使用 Frontier 内置的 SDK/JSON-RPC 适配层，而是作为普通 ACP Agent
接入。官方仓库提供 `pnpm run demo:acp` 的 JSON-RPC stdio server；`acp.json.example`
已包含对应配置。使用前克隆并构建
[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)，将示例中的绝对路径替换为
本机 checkout，并在 Frontier 进程环境中设置 `DEEPSEEK_API_KEY`，然后使用
`/acp --agent dsh <任务>`。DSH 仍处于
developer preview，建议将 checkout 固定到经过验证的 commit。

DSH 当前的官方 ACP 自动化接口只发送已提交的 assistant 文本/图片，不公开推理、工具活动、
计划等实时进度；因此 Frontier 能收到最终结果和权限请求，但不会复现原 `/dsh` 的专用进度事件。
DSH 的模型、供应商、会话和工具配置均由 DSH 自己管理，不再读取 `env.toml` 的专用 `[dsh]` 段。

编辑 `.env` 和 `env.toml` 后启动：

```bash
bash run.sh
```

Windows:

```powershell
.\run.ps1
```

`run.sh` 会设置默认 `HF_ENDPOINT`，然后循环执行 `uv run nb run`。

Markdown 渲染所需的 Mermaid、ECharts、KaTeX 和 Prism 已预构建到
`templates/markdown_assets/`，普通安装和启动不需要 Node.js，也不会在运行时访问 CDN。
修改 `renderer/` 后需要使用 Node.js 24 重新生成资源：

```bash
npm ci --prefix renderer
npm run build --prefix renderer
```

### Docker

默认镜像不包含 Torch 和内容检查模型依赖：

```bash
docker compose up -d
```

需要启用 CPU 内容检查时，选择对应构建目标，并在 `env.toml` 中设置
`[content_check].enabled = true`：

```bash
FRONTIER_DOCKER_TARGET=runtime-content-check docker compose up -d --build
```

容器会把 Hugging Face 和 Torch 缓存写入 `frontier_cache` volume。首次部署前需要准备
`.env`、`env.toml`、`mcp.json` 和 `frontier.db`；启用 ACP 时还需准备 `acp.json`。
这些运行时文件不会复制进镜像层。
如果曾用旧 Dockerfile 构建过镜像，建议删除旧镜像并轮换本地配置中的外部服务凭据。

## 配置

| 文件 | 用途 |
|------|------|
| `.env` | NoneBot 环境变量，以及由 `NICKNAME` 管理的机器人全局名称和别名 |
| `env.toml` | Frontier 应用配置：system prompt、模型、API key、功能开关、速率限制、任务群组、Dashboard |
| `mcp.json` | MCP 外部工具服务器定义 |
| `acp.json` | ACP Agent 子进程、权限策略和超时定义 |

`env.toml` 的关键部分：
- `[bot]`: 主 system prompt；不再保存机器人名称。
- `[models]`: 对话、绘图和视频模型 ID、供应商 profile 引用及模型能力。
- `[providers.*]`: LangChain 适配器类型、API 协议、base URL 和可选 API key。
- `[key]`: NASA、GitHub 等非模型服务密钥；模型密钥统一放在供应商 profile。
- `[features]` / `[agent]`: 功能开关和 Agent 推理等级。
- `[conversation_memory]`: 自动会话压缩开关和动态上下文绝对上限。
- `[agent_policy]` / `[auto_reply_policy]` / `[paint_policy]`: 访问策略。
- `[limits]` / `[notifications]` / `[storage]`: 限流超时、定时推送群和存储设置。
- `[dashboard]`: 管理面板密码、JWT secret、过期时间。
- `[content_check]`: 文本/图片内容安全开关。

`config_version = 2` 使用上述结构。旧版 `information/endpoint/function/message/database`
配置仍可读取，便于渐进迁移。`utils/configs.py` 会先校验完整配置，再原子切换运行时快照；
Dashboard 保存前也会执行相同校验。

`*_model_provider` 填写供应商 profile 名称，而不是重复填写 URL。例如
`advanced_model_provider = "openrouter"` 会读取 `[providers.openrouter]`；其中 `type = "openai"`
决定底层 LangChain 适配器。`paint_model_provider` 和 `video_model_provider` 使用相同规则；模型能力只配置在
`[models]`，base URL、API key 和 `api_mode` 只配置在供应商 profile。绘图通过
OpenAI-compatible Responses API 的 `image_generation` 工具调用，视频调用
OpenAI-compatible Videos API。

供应商 profile 名称标识具体服务，`type` 选择 LangChain 适配器，`api_mode` 选择接口协议。
DeepSeek 可分别配置为 `deepseek + chat_completions`、`openai + responses` 和
`anthropic + messages`；后两种接口的官方地址分别为 `https://api.deepseek.com` 和
`https://api.deepseek.com/anthropic`。使用官方地址和 DeepSeek 模型时，Frontier 会在三种协议中
自动发送不含 QQ 明文的稳定 scope ID，用于服务端 KV cache、内容安全和调度隔离；兼容代理不会
收到这一扩展字段。图片和文件输入目前不应交给这些 DeepSeek profile。
旧版 `use_responses_api` 和短暂使用过的 `type = "deepseek_responses"` 会自动迁移。
每日新闻使用独立的 `daily_news_model` / `daily_news_model_provider` 配置，默认通过
DeepSeek V4 的官方 Responses API 直接调用服务端 `web_search`，不再依赖 Exa MCP。
如果替换日报模型，该模型目录和 provider 协议也必须声明支持 Responses 原生联网搜索。

机器人名称只来自 `.env` 的 `NICKNAME`。数组第一项作为默认显示名称，全部非空项都可
作为全局唤醒词；某个群在数据库中配置了自定义唤醒词后，以该群的数据库配置为准。

每个群聊按 `group_id` 共享 `cache/sandbox/memory/group-{group_id}/SOUL.md`，每个私聊按
`user_id` 使用 `cache/sandbox/memory/dm-{user_id}/SOUL.md`。新文件为空，由 Agent 按稳定互动
逐步记录局部人设和长期偏好；全局安全、权限和工具规范不会写入 SOUL。

从裸 `{id}` workspace 升级时，数据库已索引的附件会按其群聊/私聊记录迁移到带类型的新目录，
提交新索引后删除旧媒体副本，避免绕过附件 TTL。SQL 历史只能匹配一种 scope 时，旧
`memory/{id}/SOUL.md` 与 `workspaces/{id}` 也会自动、非覆盖地迁移；若群号和 QQ 号同值且两种
scope 都存在，原目录会保留并打印警告，管理员核实来源后再人工合并到对应的 `group-{id}` 或
`dm-{id}` 目录。

会话上下文与 SOUL 分开管理。启用 `[conversation_memory]` 后，主 Agent 按当前模型窗口和
实际工具集合动态载入“版本化 SQL 摘要 + token 预算内的近期原文 + 当前消息”。超过高水位的
旧消息由后台任务分批压缩；压缩使用任务开始执行时冻结的 60 秒安全截止点，只处理连续稳定前缀，
写入摘要前还会原子复验源消息版本和所依赖的基摘要，因此不会越过仍可能变化的消息，也不会阻塞
本轮回复。原始
`Message` 记录仍作为可检索的权威数据保留；若已覆盖的旧消息后来因引用归一化、附件写入或 TTL
清理而改变，相关摘要会保留作审计但立即标记失效，后续从最后一个有效版本重建。群聊摘要按
`group_id` 隔离，私聊摘要按 `user_id` 隔离。私聊上下文会包含该用户自己在群聊中的历史发言，
但不会带入群 workspace 附件或被引用的其他群成员原文。`storage.query_message_numbers` 继续用于
回复网关，不再限制主 Agent 的上下文长度。

模型上下文中的每条 QQ 消息使用独立的 `frontier.qq_message.v1` JSON 信封，不会把连续群成员
合并成同一个对话轮次。身份以稳定的 `sender.user_id` 为准，群内显示名优先采用群名片并保留
昵称；引用消息通过结构化 `reply_to` 关联。信封使用未转义的 UTF-8 JSON，中文不会变成
`\\uXXXX`。纯文本统一使用各 provider 都支持的字符串 content；当前消息在附件落库后定稿，
使其下一轮作为历史载入时保持相同的文本信封与附件引用。工具、子代理和受控工具也按稳定顺序
发送，以减少 provider 前缀缓存抖动。摘要格式升级时，旧格式摘要会保留在 SQL 中供审计，
但新版本会从原始消息重建。每轮装配得到的真实 raw-history token 预算会复用到后台压缩调度；
没有本轮预算时，fallback 会预留固定 system/tool 前缀、安全余量和摘要空间，避免近期原文先
发生滑窗、下一轮才开始压缩。

从旧版 memory `AGENTS.md` 升级时不做自动迁移。如需按新规则重置旧记忆，可在项目根目录
执行一次以下命令；它只删除 workspace 目录中的旧 `AGENTS.md`：

```bash
find cache/sandbox/memory -mindepth 2 -maxdepth 2 -type f -name AGENTS.md -delete
```

## Dashboard

启动后 Dashboard 挂载到：

```text
http://localhost:8080/dashboard
```

API 前缀：

```text
/api/dashboard
```

现有 API 分组包括 auth、status、tasks、messages、settings。首次部署请修改 Dashboard 默认密码和 JWT secret。

## 项目结构

```
frontier/
├── plugins/
│   ├── agent/          # 核心消息入口和 Agent 调度
│   ├── acp/            # /acp 外部 Agent 桥接
│   ├── clockwork/      # 定时任务系统
│   ├── dashboard/      # FastAPI Dashboard
│   ├── playground/     # /paint 和 /video
│   └── toolbox/        # 管理命令
├── tools/              # LangChain Agent 工具
├── utils/              # agents/ 包、消息、DB、LLM、渲染、HTTP、Milky helper
├── prompts/            # 全局操作、渲染和任务 prompt
├── renderer/           # Markdown 本地图表/公式/代码高亮前端源码
├── templates/          # HTML/CSS 渲染模板
├── data/               # 易经、塔罗等静态数据
├── scripts/            # 维护脚本
├── test/               # pytest / nonebug 测试
├── docs/               # 设计文档和实现计划
├── cache/              # 运行时缓存和 sandbox
├── frontier.db         # 默认 SQLite 数据库
├── acp.json.example
├── env.toml.example
├── mcp.json.example
└── pyproject.toml
```

## 测试与维护

```bash
uv run pytest --collect-only -q
uv run pytest test/ -x -v
uv run pytest test/utils/agents_test.py -x
uv run ruff check .
```

数据库维护脚本：

```bash
uv run python scripts/database_maintenance.py
```

测试使用 nonebug、pytest-asyncio 和第三方 stub；测试 fixture 会生成临时 `env.toml`，不依赖本地真实配置。

## 开发提示

- 新工具：在 `tools/xxx.py` 中添加 `@tool`，必要时在 `tools/__init__.py` 的 `_TOOL_MODULE_GROUPS` 注册分组。
- 新插件：放入 `plugins/`，NoneBot 会按 `pyproject.toml` 的 `plugin_dirs` 加载。
- 不要在 `utils/agents/cognitive.py` 顶层 import 具体工具模块，容易触发循环依赖。
- `UniMessage` 和 alconna 相关 import 尽量延迟到 NoneBot 环境就绪后。
- 涉及消息主流程、DB schema、工具权限、Agent backend、LLM 路由的改动需要补针对性测试。
