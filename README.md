# Frontier

基于 [NoneBot2](https://nonebot.dev/) 的 AI 驱动 QQ 聊天机器人，具备人格化对话、深度 Agent 推理、多模态交互和长期记忆能力。

## 核心架构

```
消息 → message_gateway（门控）→ FrontierCognitive Deep Agent → 工具调用 → 回复生成
         │                        │
         ├─ 访问控制（黑白名单）
         ├─ @提及 / 机器人名触发    ├─ 文件系统后端（代码执行/数据分析）
         ├─ reply_check 规则匹配    └─ 多工具调用（33 个工具）
         └─ Signal LLM 辅助决策
```

- **消息门控**：基于访问控制、@提及、关键词匹配和 Signal LLM 辅助决策，判断是否触发 Agent 回复
- **Deep Agent**：基于 LangGraph `deepagents`，具备文件系统后端、技能加载和长期记忆
- **内容安全**：文本 + 图片审核，Safe/Controversial/Unsafe 三级分级，通过表情反应标识
- **多模型路由**：[`llm_factory.py`](utils/llm_factory.py) 根据模型名自动识别 provider（OpenAI / Google Gemini / Anthropic Claude / DeepSeek）

## 功能模块

### 插件系统

| 插件 | 功能 |
|------|------|
| `agent` | 核心对话引擎：消息门控、Agent 调度、内容安全检测、回复渲染（文本/图片） |
| `clockwork` | 定时任务：提醒、每日新闻、APOD 天文图片、地震预警、新闻摘要 |
| `dashboard` | Web 管理面板：消息浏览、配置管理、任务管理、JWT 鉴权 |
| `toolbox` | 管理命令：`/update` 热更新、`/model` 查看模型配置、技能沙箱初始化 |
| `playground` | 媒体生成：`/paint` AI 绘图、`/video` AI 视频、戳一戳回复 |

### Agent 工具能力（33 个）

| 类别 | 工具 |
|------|------|
| **平台操作** | 消息发送、文件上传、好友/群组管理、系统信息 |
| **网络检索** | Tavily 网页搜索、Wikipedia、ArXiv 论文、Bilibili 视频、网页爬取 |
| **天文空间** | 极光、彗星、卫星过境、火箭发射、空间天气 |
| **地球信息** | 地震速报、雷达云图、天气预报 |
| **记忆** | 聊天记录语义搜索 + 全文检索 |
| **占卜** | 易经、塔罗牌 |
| **媒体** | AI 图像生成、AI 视频生成 |
| **扩展** | MCP 协议动态加载外部工具 |

## 技术栈

| 层面 | 技术 |
|------|------|
| **运行时** | Python 3.14+ / Node.js（Playwright MCP） |
| **框架** | NoneBot2 + FastAPI / milky 适配器（QQ 协议） |
| **Agent** | LangChain + LangGraph / deepagents / 多模型路由 |
| **向量** | sentence-transformers + Chroma / 本地 embedding |
| **存储** | SQLite（SQLModel + FTS 全文搜索）+ Chroma 向量库 |
| **渲染** | Playwright 无头浏览器 / markdown-it-py / Pillow |
| **任务** | APScheduler |
| **部署** | Docker / uv 包管理 |

## 快速开始

### 环境要求

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) 包管理器
- Node.js（如需 npx 方式的 MCP 工具）
- Playwright 浏览器（Markdown 渲染和网页爬取）

### 安装步骤

```bash
# 1. 安装依赖
uv sync

# 2. 激活虚拟环境
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate.ps1  # Windows

# 3. 安装 Playwright 浏览器
playwright install

# 4. 配置
cp .env.example .env        # NoneBot 环境变量
cp env.toml.example env.toml  # 应用配置（API Key 等）

# 5. 启动
bash run.sh  # Linux / macOS
# ./run.ps1  # Windows
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

详细配置项参考 `.env.example` 和 `env.toml.example`。

## 项目结构

```
frontier/
├── plugins/            # NoneBot2 插件
│   ├── agent/          #   核心对话 Agent
│   ├── clockwork/      #   定时任务
│   ├── dashboard/      #   Web 管理面板
│   ├── toolbox/        #   管理命令
│   └── playground/     #   媒体生成
├── tools/              # LangChain 工具（33 个）
├── utils/              # 核心工具库
│   ├── agents.py       #   FrontierCognitive Agent
│   ├── message.py      #   消息门控与处理管道
│   ├── database.py     #   SQLite 数据库（SQLModel + FTS）
│   ├── message_vector_index.py  #   Chroma 向量索引
│   ├── llm_factory.py  #   多模型路由工厂
│   ├── signal_llm.py   #   轻量 Signal LLM 封装
│   ├── configs.py      #   配置加载
│   └── ...
├── templates/          # HTML/CSS 消息模板
├── prompts/            # Agent 系统提示词
├── data/               # 静态数据（易经、塔罗牌）
├── scripts/            # 维护脚本
├── test/               # 测试套件
├── docs/               # 设计文档
└── sandbox/            # Agent 技能与文件系统沙箱
```
