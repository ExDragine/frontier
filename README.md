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
- **文件系统工作区**：每个私聊或群聊拥有独立 `cache/sandbox/workspaces/{id}` 和 `/memory/{id}`。
- **分层提示词**：`env.toml` 定义基础人设，`prompts/AGENTS.md` 定义全局操作规范，`prompts/rendering.md` 定义渲染规范，workspace `SOUL.md` 保存动态人设与长期偏好。
- **媒体工件直发**：工具返回的 `UniMessage` artifact 会被提取并直接发送到 QQ。

## 功能模块

| 插件 | 功能 |
|------|------|
| `plugins/agent` | 核心对话引擎：消息处理、回复门控、内容安全、Deep Agent 调度、回复渲染 |
| `plugins/clockwork` | APScheduler 定时任务：提醒、用户自动任务、每日新闻、APOD、地震/NRC 等推送 |
| `plugins/dashboard` | Web 管理面板：JWT 登录、状态、消息浏览、配置管理、任务管理 |
| `plugins/playground` | `/paint` 图片生成、`/video` 视频生成、戳一戳响应 |
| `plugins/toolbox` | `/update`、`/restart`、`/model`、`/set wake`、`/vehelp` 等管理命令 |

## Agent 工具能力

`tools/` 下的 LangChain 工具会被自动发现并按组注册。当前源码约有 125 个 `@tool` 入口，覆盖：

| 类别 | 示例 |
|------|------|
| 平台操作 | 发送消息/图片/视频/文件，好友、群组、群文件、公告、精华、反应、戳一戳 |
| 记忆检索 | `memory-agent` 隔离检索当前会话，并按需总结与引用证据 |
| 媒体生成 | AI 绘图、图片编辑、AI 视频 |
| 自动任务 | 创建、列出、暂停、恢复、取消用户自动任务 |
| 网络与资料 | MCP 外部工具 |
| 天文空间 | 极光、彗星、卫星图、火箭发射、空间天气 |
| 地球与天气 | `earth-data-agent` 隔离纯文本查询；主 Agent 处理雷达、风场图、台风和 ENS 媒体 |
| 游戏/业务工具 | NRC 远行商人、精灵蛋、活动日历等 |
| 占卜 | 易经、塔罗 |

部分工具是受限工具：网页截图/录屏只有在用户明确要求查看网页外观或录制页面时才暴露；ENS 专业气象工具有独立前缀和门控规则。

仓库内置工作流位于 `skills/`，运行时以只读方式挂载到 `/skills`，按描述渐进加载；Agent 不再拥有宿主 Shell，也不会在启动时从远端下载 Skill。

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
`.env`、`env.toml`、`mcp.json` 和 `frontier.db`；这些运行时文件不会复制进镜像层。
如果曾用旧 Dockerfile 构建过镜像，建议删除旧镜像并轮换本地配置中的外部服务凭据。

## 配置

| 文件 | 用途 |
|------|------|
| `.env` | NoneBot 环境变量，以及由 `NICKNAME` 管理的机器人全局名称和别名 |
| `env.toml` | Frontier 应用配置：system prompt、模型、API key、功能开关、速率限制、任务群组、Dashboard |
| `mcp.json` | MCP 外部工具服务器定义 |

`env.toml` 的关键部分：
- `[bot]`: 主 system prompt；不再保存机器人名称。
- `[models]`: 对话、绘图和视频模型 ID、供应商 profile 引用及模型能力。
- `[providers.*]`: 供应商协议类型、base URL、可选 API key 和 Responses API 开关。
- `[key]`: NASA、GitHub 等非模型服务密钥；模型密钥统一放在供应商 profile。
- `[features]` / `[agent]`: 功能开关和 Agent 推理等级。
- `[agent_policy]` / `[auto_reply_policy]` / `[paint_policy]`: 访问策略。
- `[limits]` / `[notifications]` / `[storage]`: 限流超时、定时推送群和存储设置。
- `[dashboard]`: 管理面板密码、JWT secret、过期时间。
- `[content_check]`: 文本/图片内容安全开关。

`config_version = 2` 使用上述结构。旧版 `information/endpoint/function/message/database`
配置仍可读取，便于渐进迁移。`utils/configs.py` 会先校验完整配置，再原子切换运行时快照；
Dashboard 保存前也会执行相同校验。

`*_model_provider` 填写供应商 profile 名称，而不是重复填写 URL。例如
`advanced_model_provider = "openrouter"` 会读取 `[providers.openrouter]`；其中 `type = "openai"`
决定底层协议。`paint_model_provider` 和 `video_model_provider` 使用相同规则；模型能力只配置在
`[models]`，base URL、API key 和 `use_responses_api` 只配置在供应商 profile。绘图调用
OpenAI-compatible Images API，视频调用 OpenAI-compatible Videos API。

机器人名称只来自 `.env` 的 `NICKNAME`。数组第一项作为默认显示名称，全部非空项都可
作为全局唤醒词；某个群在数据库中配置了自定义唤醒词后，以该群的数据库配置为准。

每个群聊按 `group_id` 共享 `cache/sandbox/memory/{id}/SOUL.md`，每个私聊按 `user_id`
维护独立 SOUL。新文件为空，由 Agent 按稳定互动逐步记录局部人设和长期偏好；全局安全、
权限和工具规范不会写入 SOUL。

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
│   ├── clockwork/      # 定时任务系统
│   ├── dashboard/      # FastAPI Dashboard
│   ├── playground/     # /paint 和 /video
│   └── toolbox/        # 管理命令
├── tools/              # LangChain Agent 工具
├── utils/              # Agent、消息、DB、LLM、渲染、HTTP、Milky helper
├── prompts/            # 全局操作、渲染和任务 prompt
├── renderer/           # Markdown 本地图表/公式/代码高亮前端源码
├── templates/          # HTML/CSS 渲染模板
├── data/               # 易经、塔罗等静态数据
├── scripts/            # 维护脚本
├── test/               # pytest / nonebug 测试
├── docs/               # 设计文档和实现计划
├── cache/              # 运行时缓存和 sandbox
├── frontier.db         # 默认 SQLite 数据库
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
- 不要在 `utils/agents.py` 顶层 import 具体工具模块，容易触发循环依赖。
- `UniMessage` 和 alconna 相关 import 尽量延迟到 NoneBot 环境就绪后。
- 涉及消息主流程、DB schema、工具权限、Agent backend、LLM 路由的改动需要补针对性测试。
