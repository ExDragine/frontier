# Frontier

Frontier 是一个基于 [NoneBot2](https://nonebot.dev/) 与 Milky 适配器的 AI QQ 聊天机器人。QQ 消息经归一化、存储、回复门控和内容安全检查后，交给 LangGraph/deepagents 驱动的 Deep Agent 执行，支持多模型路由、工具调用、文件系统工作区、图片/视频生成、聊天记录检索、定时任务、ACP 子代理和 Web 管理面板。

维护入口：[贡献指南](CONTRIBUTING.md) · [安全策略](SECURITY.md) · [变更记录](CHANGELOG.md) · [文档索引](docs/README.md)。设计文档描述当前边界或历史决策；具体行为以代码和测试为准。

## 能力概览

- **QQ 主链路**：群聊与私聊的文本、图片、语音、视频、文件、引用和合并转发；回复网关在媒体下载前完成黑白名单、@、唤醒词和 Decision LLM 判断。
- **Deep Agent**：主模型驱动工具调用、文件系统 workspace、memory、子代理和内置 Skill；主 Agent 直接持有聊天历史检索、联网搜索、媒体生成与平台写操作工具。
- **富文本回复**：Markdown 正文与轻量组件按需渲染成长图，支持卡片、分区、步骤、表格、图表、公式、Mermaid、地图与网页快照；本地资源不依赖 CDN。
- **多模型路由**：OpenAI-compatible、Google Gemini、Anthropic Claude、DeepSeek 统一由供应商 profile 管理，模型目录提供上下文窗口与能力元数据。
- **工具与集成**：`tools/` 下约 128 个 `@tool` 入口，覆盖平台操作、媒体生成、搜索、天文/地球、占卜、提醒与自动任务；MCP 工具通过 `mcp.json` 接入，ACP Agent 通过 `acp.json` 接入。
- **运维能力**：FastAPI Dashboard、APScheduler 定时任务、独立新闻管线、Milky 申请事件处理、Wolfx 地震预警、会话缓存与执行用量统计。

## 内置插件

`plugins/` 下由 NoneBot 加载 9 个插件包。管理命令中 `/update`、`/restart`、`/news` 和 `/acp` 仅超级用户可用；`/model` 向所有用户开放以查看当前模型配置；`/task` 在 handler 内按超级用户或任务属主判断。

| 插件 | 功能 |
| --- | --- |
| `plugins/agent` | 核心对话入口：消息提取、引用上下文、DB 写入、回复门控、内容安全、Agent 调度与回复发送 |
| `plugins/acp` | ACP v1/v2 客户端与服务端、`/acp` 命令、子代理桥接和进程维护 |
| `plugins/clockwork` | APScheduler 定时任务：内置任务、用户自动任务、任务命令和执行历史；`daily_news` 只注册任务，处理器位于 `plugins/news` |
| `plugins/dashboard` | FastAPI Dashboard：JWT 鉴权、状态/消息/设置/任务管理 API 与 `/dashboard` 静态前端 |
| `plugins/events` | Milky 申请事件：独立持久化收件箱、规则/受限决策、执行校验与恢复；默认只记录，`/events` 仅超级用户私聊管理 |
| `plugins/news` | 独立新闻管线：Exa MCP 或 Exa/Tavily REST 检索 → 证据约束编辑 → `news.db` 归档 → 渲染 → 逐目标投递 |
| `plugins/playground` | `/paint`、`/video` 命令和戳一戳响应，复用共享图片/视频服务 |
| `plugins/toolbox` | `/update`、`/restart`、`/model`、`/set wake`、`/vehelp` 等管理命令 |
| `plugins/wolfx` | Wolfx CENC 地震预警：WebSocket 长连接、事件去重、渲染与推送 |

## 核心架构

```text
QQ / Milky MessageEvent
  ↓
plugins/agent on_message(priority=10)
  ↓
消息段提取 → 归一化 → 引用上下文 → DB 存储
  ↓
message_gateway 门控（黑白名单 / @ / 唤醒词 / Decision LLM）
  ↓
媒体下载 + 内容安全检查
  ↓
ConversationOrchestrator（平台中性编排）
  ↓
FrontierAgentCore → FrontierAgentRuntime.run → FrontierCognitive.chat_agent()
  ↓
deepagents.create_deep_agent() → 工具调用 / 文件系统后端 / memory
  ↓
UniMessage 文本、图片、视频或文件回复
```

关键边界：

- 先存储、后门控、再下载媒体，未触发回复的图片和视频不会被下载。
- QQ 使用两级命名锁：`delivery:{workspace_key}` 覆盖生成、工件发送、最终回复和送达落库，`workspace:{workspace_key}` 覆盖同一 workspace 的 Agent 执行；顺序固定为 delivery → workspace。
- 群聊按 `group-{group_id}` 共享 workspace 与 memory，私聊按 `dm-{user_id}` 隔离。
- 工具返回的 `UniMessage` 工件会被提取并直接发送，多媒体工件拆分后串行发送。

完整消息路径、历史边界与投递语义见 [消息、上下文与投递边界](docs/message_flow.md)。

## Agent 工具能力

`tools/` 下的 LangChain 工具会被自动发现并按组注册，当前源码约有 128 个 `@tool` 入口：

| 类别 | 代表能力 |
| --- | --- |
| 平台操作 | 发送消息/图片/视频/文件，好友、群组、群文件、公告、精华、反应、戳一戳 |
| 历史记忆 | 当前会话最近对话、聊天记录搜索、平台分页历史、按消息读取附件 |
| 子代理 | `document-agent` 只读分析本地文档；`expose_as_subagent` 的 ACP Agent 以 `acp-<名称>` 注册 |
| 媒体生成 | AI 绘图、图片编辑、AI 视频 |
| 自动任务 | 创建、列出、暂停、恢复、取消用户自动任务 |
| 网络与资料 | 独立 DeepSeek 搜索（默认 20 条）与正文抓取，保留原生搜索和 Exa / Tavily |
| 天文空间 | 极光、彗星、卫星图、火箭发射、空间天气 |
| 地球与天气 | 地震、雷达、风场、台风和 ENS 气象媒体 |
| 游戏/业务工具 | NRC 远行商人、精灵蛋、活动日历等 |
| 占卜 | 易经、塔罗 |

部分工具是受限工具：网页截图/录屏只有在用户明确要求查看网页外观或录制页面时才暴露；ENS 专业气象工具有独立前缀和门控规则。调用预算、用量统计和错误处理约定见 [Agent 执行控制](docs/agent-execution-controls.md)。MCP 外部工具在首轮 Agent 执行时异步发现，单个服务故障不会使全部工具失效。

## 技术栈

| 层面 | 技术 |
| --- | --- |
| 运行时 | Python 3.14+、uv |
| Bot 框架 | NoneBot2、FastAPI driver、nonebot-adapter-milky、nonebot_plugin_alconna |
| Agent | LangChain、LangGraph、deepagents |
| 模型 | OpenAI-compatible、Google Gemini、Anthropic Claude、DeepSeek |
| 存储 | SQLite、SQLModel、FTS5、WAL |
| 渲染/浏览器 | Playwright、markdown-it-py、Mermaid、Apache ECharts、KaTeX、Prism |
| 定时任务 | APScheduler / nonebot-plugin-apscheduler |
| 部署 | Docker、docker compose、uv |

## 快速开始

### 环境要求

- Python 3.14+ 与 [uv](https://docs.astral.sh/uv/)
- Playwright 浏览器依赖
- 可用的 Milky 服务和对应 NoneBot 配置
- 至少一个可用 LLM API key

### 安装

```bash
uv sync
uv run playwright install
```

语音识别和语音合成的 Python 依赖已包含在默认 `uv sync` 安装中，无需安装 extras。
启用 `[speech_recognition]` / `[speech_synthesis]` 后，首次使用会自动下载并校验对应模型；
Windows x64 的 SenseVoice 运行器也会自动准备。下载按需进行，未启用的功能不下载模型。
需要提前准备或离线部署时，可运行 `uv run --locked python scripts/setup_speech.py` 一次安装两套资源。
配置与平台限制见 [本地语音识别](docs/local-speech.md) 和 [本地语音合成](docs/local-tts.md)。

项目已将腾讯云 PyPI 镜像设为 uv 默认源；CPU 版 PyTorch 使用上海交通大学的 wheel 镜像，`.env.example` 和启动脚本默认把 `HF_ENDPOINT` 设为 `https://hf-mirror.com`。内容检查模型依赖随项目默认安装，启用 `[content_check]` 后首次检查会按配置下载模型和 tokenizer。

### 配置

```bash
cp .env.example .env
cp env.toml.example env.toml
```

在 `.env` 中设置 `NICKNAME`、`SUPERUSERS`、`HOST`/`PORT` 等 NoneBot 参数；在 `env.toml` 中配置人设、模型、供应商 profile 与功能开关。配置必须显式声明 `config_version = 2`。需要 MCP 工具或 ACP Agent 时再复制：

```bash
cp mcp.json.example mcp.json
cp plugins/acp/acp.json.example acp.json
```

字段说明见 [配置参考](docs/configuration.md)，ACP 用法见 [ACP 接入](docs/acp.md)。真实配置文件包含密钥与聊天数据，不要提交。

### 启动

```bash
bash run.sh
```

Windows 使用 `.\run.ps1`。两个脚本都会设置默认 `HF_ENDPOINT`，然后循环执行 `uv run nb run`，进程退出 5 秒后自动重启。

### Docker

```bash
docker compose up -d
```

镜像默认包含 Torch 和内容检查模型依赖，容器把 Hugging Face 与 Torch 缓存写入 `frontier_cache` volume。首次部署前准备 `.env`、`env.toml`、`mcp.json` 和 `frontier.db`；`.dockerignore` 排除这些运行时文件，compose 通过 `env_file` 或 volume 在运行时提供它们，因此不会进入镜像层。启用 ACP 时还需准备 `acp.json`：compose 未挂载该文件，需要在构建前放入仓库根目录（会随镜像复制），或自行在 compose 中增加只读挂载。compose 默认把容器 `8080` 映射到宿主 `3000`，Dashboard 位于 `http://localhost:3000/dashboard`。

## 配置概览

| 文件 | 用途 |
| --- | --- |
| `.env` | NoneBot 环境变量；`NICKNAME` 管理机器人全局名称和别名 |
| `env.toml` | Frontier 应用配置：system prompt、模型与供应商、功能开关、策略、限额、Dashboard、内容检查 |
| `mcp.json` | MCP 外部工具服务器定义 |
| `acp.json` | ACP Agent 子进程、权限策略和超时 |

`env.toml` 的要点：

- `[bot]`、`[models]`、`[providers.*]`、`[search]`、`[key]`、`[features]`、`[agent]`、`[limits]`、`[storage]`、`[dashboard]`、`[content_check]` 等配置段覆盖人设、模型角色、供应商协议、搜索、开关与限额。
- `*_model_provider` 填写 `[providers.<name>]` 的名称而不是 URL；`type` 选择 LangChain 适配器，`api_mode` 选择接口协议，密钥和 base URL 保存在 profile。
- 绘画和视频 provider 的 `type` 必须为 `openai`；绘画协议跟随 `api_mode`，视频使用 Videos API。
- `[agent_policy]` / `[auto_reply_policy]` / `[paint_policy]` 控制响应名单、主动回复和媒体生成权限。
- Dashboard 保存会原子重载配置，同时返回 `changed_fields`、`config_revision`、`activation` 和 `restart_required`；`.env` 和 `mcp.json` 修改仍需重启。

逐字段说明、模型路由规则、provider 协议矩阵、访问策略语义和重载细节见 [配置参考](docs/configuration.md)。

## Dashboard

启动后 Dashboard 挂载到：

```text
http://localhost:8080/dashboard
```

API 前缀为 `/api/dashboard`，现有分组包括 auth、status、tasks、messages 和 settings。首次部署请修改默认密码并设置随机 JWT secret；配置保存与重载语义见 [配置参考](docs/configuration.md)。

## 项目结构

```text
frontier/
├── plugins/
│   ├── agent/          # QQ 事件、引用、归一化、门控、附件和上下文
│   ├── acp/            # ACP 客户端、v1/v2 服务端、QQ 命令与子代理桥接
│   ├── clockwork/      # 定时任务系统（daily_news 处理器位于 plugins/news）
│   ├── dashboard/      # FastAPI Dashboard 和静态前端
│   ├── events/         # Milky 申请事件的收件箱、规则/决策与执行恢复
│   ├── news/           # 独立新闻检索、编辑、归档和投递
│   ├── playground/     # /paint 和 /video
│   ├── toolbox/        # 管理命令
│   └── wolfx/          # CENC 地震预警 WebSocket 监听与推送
├── tools/              # LangChain Agent 工具
├── utils/              # agents/ 包、agent_protocol/、消息、DB、LLM、渲染、HTTP、Milky helper
├── models/             # 供应商模型目录与 lobehub 名称表
├── skills/             # 只读内置 Skill，运行时挂载到 /skills
├── prompts/            # 共享 Agent 提示词；插件专属提示词随插件保存
├── renderer/           # Markdown 本地图表/公式/代码高亮前端源码
├── templates/          # 共享渲染模板；插件专属模板随插件保存
├── data/               # 易经、塔罗等静态数据
├── scripts/            # 维护脚本
├── test/               # pytest / nonebug 测试
├── docs/               # 设计文档、配置参考、文档索引与历史归档
├── cache/              # 运行时缓存和 sandbox
├── frontier.db         # 默认 SQLite 数据库
├── env.toml.example
├── mcp.json.example
└── pyproject.toml
```

## 测试与维护

```bash
uv sync --locked --group dev
uv run --locked pytest --collect-only -q
uv run --locked pytest test/ -q
uv run --locked ruff check .
uv run --locked python scripts/check_local_links.py
uv run python scripts/database_maintenance.py diagnose
```

测试使用 nonebug、pytest-asyncio 和第三方 stub；fixture 会生成临时 `env.toml`，不依赖本地真实配置。修改消息主流程、数据库 schema、工具权限、Agent backend 或 LLM 路由时应补针对性测试。CI 按 `uv.lock` 安装相同依赖，执行全量测试、Ruff、本地链接检查和渲染器资源校验；类型检查范围见 [贡献指南](CONTRIBUTING.md)。

## 文档导航

- [文档索引](docs/README.md)：按入门、架构与运行时、平台与集成、存储与运维、历史归档分类的全部文档。
- 常用入口：[配置参考](docs/configuration.md)、[ACP 接入](docs/acp.md)、[消息投递边界](docs/message_flow.md)、[Agent 执行控制](docs/agent-execution-controls.md)、[QQ 会话缓存](docs/agent-sessions.md)。
- 插件、渲染器、模型目录与内置 Skill 的说明见各自目录下的 README/SKILL.md（已汇总到 [文档索引](docs/README.md)）；历史设计计划与审查记录保存在 [docs/archive/](docs/archive/README.md)，不作为当前行为依据。

## 开发提示

- 新工具：在 `tools/xxx.py` 中添加 `@tool`，必要时在 `tools/__init__.py` 的 `_TOOL_MODULE_GROUPS` 注册分组。
- 新插件：放入 `plugins/`，NoneBot 会按 `pyproject.toml` 的 `plugin_dirs` 加载。
- 不要在 `utils/agents/cognitive.py` 顶层 import 具体工具模块，容易触发循环依赖；`UniMessage` 等 alconna import 尽量延迟到 NoneBot 环境就绪后。
- 涉及消息主流程、DB schema、工具权限、Agent backend、LLM 路由的改动需要补测试，更多约定见 [AGENTS.md](AGENTS.md)。

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
