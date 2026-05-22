# Frontier

基于 [NoneBot2](https://nonebot.dev/) 的 AI 驱动 QQ 聊天机器人，具备人格化对话、深度 Agent 推理、多模态交互和长期记忆能力。

## 核心架构

```
消息 → Signal LLM（门控决策）→ Deep Agent（复杂推理）→ 工具调用 → 回复生成
                                ↘ 快速人格回复（简单对话）
```

- **两级决策系统**：轻量 Signal 模型负责判断是否回复及回复策略；对于复杂请求，交由 LangGraph 深度 Agent 执行多步推理和工具调用
- **多模型路由**：支持 OpenAI、Google Gemini、Anthropic Claude、DeepSeek，根据模型名自动识别 provider
- **长期记忆**：SQLite 存储结构化消息 + Chroma 向量数据库实现语义搜索
- **文件系统后端**：Agent 可读写文件，支持代码执行、数据分析等持久化操作

## 功能模块

### 插件系统

| 插件 | 功能 |
|------|------|
| `agent` | 核心对话引擎：消息拦截、门控决策、Agent 调度、内容安全检测、回复渲染 |
| `clockwork` | 定时任务：提醒、每日新闻、天文图片、地震预警、新闻摘要 |
| `dashboard` | Web 管理面板：消息浏览、配置管理、任务管理、JWT 鉴权 |
| `toolbox` | 管理命令：`/update` 热更新、`/model` 查看模型配置 |
| `playground` | 媒体生成：`/paint` AI 绘图、`/video` AI 视频、戳一戳回复 |

### Agent 工具能力（33 个工具）

| 类别 | 工具 |
|------|------|
| **平台操作** | 发送消息、文件上传、好友/群组管理、系统信息 |
| **网络检索** | Tavily 网页搜索、Wikipedia、ArXiv 论文、Bilibili 视频、网页爬取 |
| **天文空间** | 极光、彗星、卫星过境、火箭发射、空间天气、Heavens Above |
| **地球信息** | 地震速报、雷达云图、天气预报 |
| **记忆** | 聊天记录语义搜索 + 全文检索 |
| **占卜** | 易经、塔罗牌 |
| **媒体** | AI 图像生成、AI 视频生成 |
| **扩展** | MCP 协议动态加载外部工具 |

## 技术栈

- **框架**：Python 3.14+ / NoneBot2 + FastAPI / milky 适配器（QQ 协议）
- **AI**：LangChain + LangGraph / deepagents / 多模型路由（OpenAI / Gemini / Claude / DeepSeek）
- **向量**：sentence-transformers + Chroma / 本地 embedding 模型
- **存储**：SQLite（SQLModel/SQLAlchemy）+ Chroma 向量库
- **渲染**：Playwright 无头浏览器 / markdown-it-py / Pillow
- **任务**：APScheduler / httpx（HTTP/2）
- **部署**：Docker / uv 包管理

## 快速开始

### 环境要求

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) 包管理器
- Node.js（如需使用 npx 方式的 MCP 工具）
- Playwright 浏览器（用于 Markdown 渲染和网页爬取）

### 安装步骤

```bash
# 1. 安装依赖
uv sync

# 2. 激活虚拟环境
source .venv/bin/activate  # Linux
# 或 .venv\Scripts\activate.ps1  # Windows

# 3. 安装 Playwright 浏览器
playwright install

# 4. 配置文件
# 将 .env.example 复制为 .env 并填写 NoneBot 配置
# 将 env.toml.example 复制为 env.toml 并填写 API Key 等功能配置

# 5. 启动
bash run.sh  # Linux
# 或 ./run.ps1  # Windows
```

### Docker 部署

```bash
docker compose up -d
```

## 配置说明

| 文件 | 用途 |
|------|------|
| `.env` | NoneBot2 环境变量（驱动、端口、超级用户等） |
| `env.toml` | 应用配置（LLM 端点、API Key、功能开关、速率限制等） |
| `mcp.json` | MCP 服务器定义（Agent 外部工具扩展） |

详细配置项请参考 `.env.example` 和 `env.toml.example` 中的注释。

## 项目结构

```
frontier/
├── plugins/          # NoneBot2 插件模块
│   ├── agent/        #   核心对话 Agent
│   ├── clockwork/    #   定时任务
│   ├── dashboard/    #   Web 管理面板
│   ├── toolbox/      #   管理命令
│   └── playground/   #   媒体生成
├── tools/            # LangChain 工具（33个）
├── utils/            # 核心工具库
│   ├── agents.py     #   Agent 创建与编排
│   ├── database.py   #   SQLite 数据库
│   ├── message.py    #   消息处理管道
│   ├── llm_factory.py#   多模型路由
│   └── ...
├── templates/        # HTML 消息模板
├── prompts/          # Agent 系统提示词
├── data/             # 静态数据（易经、塔罗牌等）
├── scripts/          # 维护脚本
├── test/             # 测试套件
├── docs/             # 设计文档
└── sandbox/          # Agent 技能沙箱
```
