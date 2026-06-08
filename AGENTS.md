# Agent Guidelines

## Project Overview

Frontier 是基于 NoneBot2 + Milky 适配器的 AI QQ 聊天机器人。核心能力：Deep Agent（LangGraph `create_deep_agent`）驱动对话，文件系统后端执行代码，33+ 工具收发消息、检索网络、生成媒体，长期记忆和定时任务。

**技术栈**: NoneBot2 → Milky 事件 → deepagents (LangGraph) → 工具调用 → UniMessage 回复
**配置**: 所有配置集中在 `env.toml`，通过 `utils/configs.py` 的 `EnvConfig` 数据类读取。

---

## Request Lifecycle（一条消息的完整路径）

```
QQ 消息 → NoneBot2 on_message(priority=10)
  │
  ├─ Phase 1: 文本提取 (message_extract → normalize_segments → reply_context)
  │    不下载媒体，只解析文本 + 引用上下文 + 文件路径
  │
  ├─ Phase 2: 消息存储 + 网关 (messages_db.insert → message_gateway)
  │    先存 DB，再判断是否触发 Agent 回复（黑/白名单、关键词、Signal LLM）
  │    网关不通过 → common.finish()，后续阶段不执行
  │
  ├─ Phase 3: 媒体下载 (download_media)
  │    只有网关通过才下载，避免浪费带宽
  │
  ├─ Phase 4: 内容安全 (message_check → risk_check → 表情反应)
  │    文本 + 图片审核，Safe / Controversial / Unsafe 三级
  │
  └─ Agent 执行 (agent_queue.submit → _process_agent_request → chat_agent)
        AgentQueueManager 限制并发（maxsize=5），按 (user_id, group_id) 排队
        chat_agent → create_deep_agent → 工具调用 → extract_uni_messages → send_messages
```

关键边界：
- 网关在消息存储**之后**、媒体下载**之前**，减少重试下载的成本
- Agent 在独立线程执行（`agent_queue.submit`），主流程不等待
- `UniMessage` 是 nonebot_plugin_alconna 的通用消息类型，延迟加载（`require()`）

---

## Module Map

### plugins/ — NoneBot2 插件（事件入口）

| 模块 | 文件数 | 职责 |
|------|--------|------|
| `plugins/agent` | 1 (`__init__.py` 360行) | 核心对话引擎：消息处理、网关、Agent 调度、回复渲染。项目的中枢 |
| `plugins/clockwork` | 7 文件 | 定时任务：提醒、每日新闻、天文图片、地震预警。基于 task_manager 的 cron/interval/date 调度 |
| `plugins/dashboard` | 7 文件 | Web 管理面板：JWT 鉴权、消息浏览、配置、任务管理。FastAPI 集成 |
| `plugins/playground` | 1 (`__init__.py`) | 媒体生成入口：`/paint` AI 绘图、`/video` AI 视频、戳一戳回复 |
| `plugins/toolbox` | 1 (`__init__.py`) | 管理命令：`/update` 热更新、`/model` 查看模型、技能沙箱初始化 |

### utils/ — 共享基础设施

| 文件 | 行数 | 职责 |
|------|------|------|
| `agents.py` | 498 | **心脏**：`FrontierCognitive` 类 + `assistant_agent()` + 模型路由。创建 Deep Agent、组装 backend/middleware/tools |
| `database.py` | 1470 | **巨兽**：SQLite 消息存储、FTS 全文搜索、附件管理、Session 工具。`MessageDatabase` + `async_session_scope` |
| `message.py` | 734 | 消息提取/网管/安全/发送。`message_extract`, `message_gateway`, `message_check`, `send_messages` |
| `configs.py` | 322 | `EnvConfig`：从 `env.toml` 读取所有配置、模型端点、API keys |
| `llm_factory.py` | 177 | 多模型路由：自动识别 provider (OpenAI/Google/Anthropic/DeepSeek)，`create_llm()` + `model_supports()` |
| `reply_context.py` | 323 | 构建回复引用上下文 |
| `staged_artifacts.py` | 316 | 暂存生成媒体（图片/视频），支持 ID 引用 |
| `markdown_render.py` | 268 | Markdown → Pil 图片渲染，兼容 QQ 的最低渲染 |
| `milky_tools.py` | 244 | Milky 协议专用工具（底层 API 封装） |
| `paint_service.py` | 227 | AI 绘图服务（对接 `/paint` 后端） |
| `video_service.py` | 249 | AI 视频服务 |
| `agent_queue.py` | 135 | 并发控制：每个 (user, group) 最多 1 个活跃 Agent，全局 5 并发 |
| `user_profile.py` | 216 | 长期用户画像：静默提取 → 积累 → 注入 system prompt |
| `signal_llm.py` | 102 | 轻量 LLM 辅助决策调用 |
| `message_normalizer.py` | 142 | 长消息拆分/归一化 |
| `message_vector_index.py` | 210 | 消息向量索引（语义搜索） |
| `http_client.py` | 40 | httpx 单例客户端池 |
| `context_check.py` | 61 | 内容安全检查封装 |

### tools/ — Agent 可调用工具

每个 `.py` 文件是一个或多个 `@tool` 装饰的 LangChain BaseTool。`tools/__init__.py` 自动扫描注册。

| 分组 | 工具 | 说明 |
|------|------|------|
| **main** | `adapter`, `calculator`, `milky_*`, `paint`, `video`, `memory`, `reminder`, `scheduled_task`, `deepseek_balance` | 平台操作、媒体生成、记忆、定时任务 |
| **research** | `tavily`, `wikipedia`, `arxiv`, `bilibili` | 网络搜索与学术检索 |
| **astro** | `aurora`, `comet`, `heavens_above`, `rocket`, `satellite`, `space_weather` | 星空/天文/卫星/火箭 |
| **earth** | `earthquake`, `radar`, `weather` | 地震、雷达、天气 |
| **memory** | `memory` | 长期记忆读写 |
| **divination** | `iching` (825行), `tarot` (341行) | 易经占卜、塔罗牌 |

工具注册约定：
- 每个 `tools/*.py` 模块中，用 `@tool` 装饰的函数自动被 `_discover_tools()` 收集
- `_TOOL_MODULE_GROUPS` 字典控制模块 → 分组映射
- 新工具只需：创建 `tools/xxx.py` → 用 `@tool` 装饰 → 在 `_TOOL_MODULE_GROUPS` 注册

### prompts/ — Agent 行为指令

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | **活跃的 Agent system prompt 模板**。加载时通过 `{name}` 注入 bot 名称/唤醒词 |

System prompt 加载链：`FrontierCognitive.load_system_prompt()` → 读取 `env.toml` 的 `information.system_prompt` → 用 `{name}` 格式化 → 注入长期用户画像 → 传给 `create_deep_agent()`

### test/ — 测试

| 文件/目录 | 覆盖范围 |
|-----------|----------|
| `plugins/agent_image_memory_test.py` | 核心 Agent 消息处理全流程（~60 个测试） |
| `utils/agents_test.py` | `FrontierCognitive`, `assistant_agent`, `chat_agent` |
| `utils/message_test.py` | 消息提取、网关、回复检查 |
| `tools/` | 各工具模块单元测试 |
| `plugins/clockwork_test.py` | 定时任务 |
| `stubs/dummies.py` | 共享 mock 工具 |

---

## Key Patterns & Conventions

### 延迟 import 避免循环依赖
`tools/memory.py` 和 `plugins/agent/__init__.py` 中有模式的延迟 import：
```python
from utils.agents import assistant_agent  # 延迟导入避免循环依赖
```
因为 `utils/agents.py` → `tools/` → `tools/memory.py` → 回引 `utils/agents.py` 会循环。**不要在 utils/agents.py 层 import tools 层的东西。**

### UniMessage 延迟加载
`FrontierCognitive._uni_message_cls()` 用 `require("nonebot_plugin_alconna")` 延迟加载，因为加载在 NoneBot 事件循环启动之前会失败。

### Agent 返回值约定
`chat_agent()` 返回 `dict`：
```python
{
    "response": {"messages": [AIMessage(...)]},  # 回复消息列表
    "total_time": float,                         # 处理耗时（秒）
    "uni_messages": list[UniMessage],            # 媒体工件（图片/视频）
}
```
`_process_agent_request()` 返回 `bool`：`True` 表示已发送回复（总是 True——Agent 不再有沉默路径）。

### 工具输出 → UniMessage 传递
媒体生成工具（`get_paint`, `get_video`）通过 agent 响应的 `artifact` 属性返回 UniMessage，再经由 `extract_uni_messages()` 提取 → `send_artifacts()` 发送。

### 文件系统后端
`_build_agent_backend()` 创建三层 CompositeBackend：
- **default** (`workspaces/`): 每个用户/群聊的独立工作区，代码执行沙箱
- `/skills`: 共享技能目录（只读）
- `/memory/{key}/`: 群聊/用户独享的长期记忆（AGENTS.md 自动生成）

---

## Gotchas

1. **`utils/database.py` 是 1470 行的巨兽**。修改时要小心：SQLite FTS 表、消息归一化的 derived_messages 机制、线程池调度（`_run_in_thread`）都耦合在这里。不要在没有充分理解的情况下重构。

2. **`env.toml` 是唯一配置源**。`EnvConfig` 在模块加载时立即读取，所以配置变更需要重启。不要在代码里硬编码 model/provider 名——走 `EnvConfig.*`。

3. **Middlewares 顺序敏感**。`chat_agent()` 中 middleware 按 `PII → ToolRetry → ModelRetry → FilesystemFileSearch → CodeInterpreter` 的顺序执行。修改顺序可能破坏重试行为。

4. **Model route 逻辑在 `_configured_model_route()`**。`BASIC_MODEL` 用于 `assistant_agent`（工具类调用），`ADVAN_MODEL` 用于 `chat_agent`（对话），`SIGNAL_MODEL` 用于网关辅助决策。

5. **测试用 monkeypatch + Dummy**。测试模式是 monkeypatch 替换模块级对象（`f_cognitive`, `messages_db`, `agent_queue`）然后用 `nonebug.App.test_matcher()` 模拟事件。

6. **循环依赖禁区**: `utils/agents.py` 和 `tools/` 包之间不能直接 import。`tools/memory.py` 里 `from utils.agents import assistant_agent` 是函数内延迟 import，不要把它提到模块顶部。

---

## Testing

```bash
pytest test/ -x -v                    # 全部测试，首个失败停
pytest test/utils/agents_test.py -x   # 单文件
```

测试基础架构：
- **nonebug**: NoneBot 的 pytest 插件，提供 `App.test_matcher()` 模拟消息事件
- **monkeypatch**: 替换模块级依赖（agent_queue, f_cognitive, messages_db）
- **IncomingMessage + MessageEvent**: 构造模拟 QQ 消息

写测试时的惯例：
- 使用 `monkeypatch.setattr(nonebot, "require", lambda *args, **kwargs: None)` 绕过 alconna 加载
- 在测试函数内 `from plugins import agent` 做延迟 import，确保 monkeypatch 先生效
- Dummy 类模拟外部依赖（DummyCognitive, DummyMessagesDb, DummyBot）

---

## Engineering Practice

- 读周围代码再改。遵循项目已有的模式、helpers、测试和模块边界
- 代码保持 Pythonic：清晰命名、直接控制流、内聚函数、惯用 stdlib
- 不要创建很多琐碎的 helper 函数。只在复用、隔离真实复杂度、代表有意义的领域边界、或实质提升可测试性时才抽 helper
- 简单的逻辑保持内联，抽走只会让读者跳转却不减少复杂度
- 变更范围限定在请求的行为内。避免无关重构、格式化 churn 或 API 变更
- 保留同事已在工作区中的修改，不要未经要求 revert

## Verification

- 行为变更时添加/更新针对性测试，尤其是共享工具、Agent 连接、工具注册、用户面向的流程
- 完成前运行最窄有效的 lint 和测试命令。注明未运行的命令
- 警告和 flaky 失败不是噪音，是需要调查的证据
