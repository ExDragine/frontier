# 配置参考

Frontier 的配置分为四类文件：NoneBot 启动参数在 `.env`，Frontier 应用配置在 `env.toml`，MCP 外部工具在 `mcp.json`，外部 ACP Agent 在 `acp.json`。可提交的示例文件是配置形状的权威来源：[`.env.example`](../.env.example)、[`env.toml.example`](../env.toml.example)、[`mcp.json.example`](../mcp.json.example)、[`plugins/acp/acp.json.example`](../plugins/acp/acp.json.example)。真实配置文件含密钥，不进入版本库。

本页描述当前实现；字段校验以 `utils/configs.py` 为准，能力与路由以 `utils/llm_factory.py` 和各服务代码为准。

## 配置文件

| 文件 | 职责 | 生效方式 |
| --- | --- | --- |
| `.env` | NoneBot 环境变量：`HOST`、`PORT`、`DRIVER`、`SUPERUSERS`、`NICKNAME` 等 | 进程启动时读取，修改后重启 |
| `env.toml` | Frontier 应用配置：人设、模型、供应商、密钥、功能开关、策略、限额、存储、Dashboard、内容检查 | 启动时校验；Dashboard 保存后原子重载，后续请求/任务读取新值；手工编辑需重启 |
| `mcp.json` | MCP 外部工具服务器定义 | 修改后重启 |
| `acp.json` | 外部 ACP Agent 子进程、权限策略与超时 | 每个新连接重新读取；配置指纹变化时下次调用重建连接 |

`env.toml` 的路径可由环境变量 `FRONTIER_CONFIG` 覆盖，默认是工作目录下的 `env.toml`。机器人名称只来自 `.env` 的 `NICKNAME`：数组第一项是非空项中的默认显示名，全部非空项都作为全局唤醒词；某个群在数据库中配置了自定义唤醒词后，以该群配置为准。

`mcp.json` 每项必须提供 HTTP(S) `url`，`transport` 默认 `http`，也接受 `streamable_http`；支持 5–300 秒的 `startup_timeout_seconds` 和字符串 `headers`。旧的 stdio/SSE 接入以及 `command`、`args`、`env` 字段不再接受。

## 配置版本与校验

- 必须显式声明 `config_version = 2`，且只能是整数 `2`；其他值、缺失值或旧版分区会直接报错。
- 已退役的配置段：`[information]`、`[endpoint]`、`[llm_endpoints]`、`[function]`、`[message]`、`[database]`、`[image_memory]`、`[memory]`。
- 已移除的字段：`[models]` 下的 `*_model_endpoint`、`*_model_use_responses_api`、`paint_base_url`、`video_base_url`；`[key]` 下的模型 API key；`[providers.*]` 下的 `capabilities`、`provider` 和 `use_responses_api`。模型 endpoint、协议和密钥应配置在对应供应商 profile。
- 旧配置中的 `signal_model` / `signal_model_provider` / `signal_model_capabilities` 会映射为 `decision_*`，但新配置应直接使用 `decision_*`；同名新旧字段不能同时出现。
- 模型角色和其余配置段拒绝未知字段；供应商 profile 允许保留额外键。
- 启动时 `utils/configs.py` 校验成功后才替换运行时快照；校验失败不会用半成品配置继续运行。Dashboard 保存失败时会回滚旧文件并重新加载旧配置。

## 配置段总览

| 配置段 | 用途 | 详见 |
| --- | --- | --- |
| `[bot]` | 主 system prompt；`{name}` 会替换为当前唤醒词 | 本页 |
| `[models]` / `[providers.*]` | 模型角色、供应商 profile、密钥和协议 | 本页 |
| `[search]` | 独立 DeepSeek 网页搜索与正文读取 | [DeepSeek 网页搜索](deepseek-web-search.md) |
| `[key]` | NASA、GitHub 等非模型服务密钥 | 本页 |
| `[features]` | 功能开关与可选 Laya 候选预筛 | 本页 |
| `[platforms.feishu]` | 飞书接入的非敏感配置（生产入口默认关闭） | 本页 |
| `[agent]` | 推理等级、长文转图阈值、Fake-IP 媒体回退 | [消息媒体网络](message-media-network.md) |
| `[speech_recognition]` | 本地 SenseVoice 语音识别 | [本地语音识别](local-speech.md) |
| `[speech_synthesis]` | 本地 MOSS-TTS-Nano 语音合成 | [本地语音合成](local-tts.md) |
| `[agent_policy]` / `[auto_reply_policy]` / `[paint_policy]` | 访问名单与主动回复、绘画权限 | 本页 |
| `[limits]` | 调用预算、超时、限流 | [Agent 执行控制](agent-execution-controls.md) |
| `[sessions]` | QQ 跨轮会话缓存 | [QQ 会话缓存](agent-sessions.md) |
| `[events]` | Milky 申请事件处理 | [Milky 申请事件](platform-events.md) |
| `[notifications]` | 内置任务与通知的初始目标群 | 本页 |
| `[storage]` | 历史查询窗口、图片与媒体 TTL | 本页 |
| `[debug]` | Agent 调试开关 | 本页 |
| `[dashboard]` | 管理面板密码与 JWT | 本页 |
| `[content_check]` | 文本/图片内容安全检查 | 本页 |

## 模型与供应商

### 模型角色

`[models]` 按角色声明模型、供应商 profile 和模型能力，字段名为 `<角色>_model`、`<角色>_model_provider`、`<角色>_model_capabilities`：

| 角色 | 用途 |
| --- | --- |
| `basic` | 轻量辅助任务（如文档子代理、辅助 Agent） |
| `decision` | 回复门控、浏览器捕获意图等结构化判断 |
| `advanced` | 主对话 Agent；未配置时主 Agent 无法执行 |
| `daily_news` | 每日新闻的编辑与复核模型 |
| `paint` | 绘画模型，另有 `paint_size`、`paint_quality` |
| `video` | 视频模型，另有 `video_size`、`video_seconds` |

`*_model_capabilities` 描述该模型实际支持的多模态输入，可选值与别名：`text`、`vision`（别名 `image`）、`audio`、`video`、`file`（别名 `pdf`、`attachment`）。能力只配置在模型角色上，不能写在供应商 profile 里；供应商只描述接口。

`paint_size` 仍会被解析（默认 `"auto"`），但当前绘图请求固定使用 `size="auto"`，由图片模型结合提示词和参考图选择尺寸；`paint_quality` 会传给绘图接口。`video_size` 和 `video_seconds` 会传给视频接口。

### 供应商 profile

每个 `*_model_provider` 填写 `[providers.<name>]` 的名称。profile 的 `type` 决定底层 LangChain 适配器，`api_mode` 决定接口协议：

| `type` | 可用 `api_mode` | 说明 |
| --- | --- | --- |
| `openai` | `chat_completions`、`responses` | OpenAI-compatible 代理 |
| `google` | `generate_content` | Google Gemini |
| `anthropic` | `messages` | Anthropic Messages |
| `deepseek` | `chat_completions` | DeepSeek 专用适配器 |

省略 `api_mode` 时，新建 profile 按 `type` 回退默认协议（`openai` → `chat_completions`，`google` → `generate_content`，`anthropic` → `messages`，`deepseek` → `chat_completions`）；与内置同名 profile 未写 `api_mode` 时沿用内置值，例如 `[providers.openai]` 仍是 `responses`。内置 profile 名称始终可用：`openai`（默认 `responses`）、`google`、`anthropic`、`deepseek`、`deepseek_responses`（`openai + responses`，默认地址 `https://api.deepseek.com`）、`deepseek_anthropic`（`anthropic + messages`，默认地址 `https://api.deepseek.com/anthropic`）；同名 `[providers.<name>]` 覆盖默认值。

profile 常用字段：

- `base_url`、`api_key`：地址与密钥；模型 API key 不再放在 `[key]`。
- `native_web_search`：确认上游实现内置 `web_search` 后设为 `true`；官方 OpenAI Responses 会自动启用，DeepSeek Flash 会忽略该工具。
- `structured_output_method`：Decision 结构化策略，`auto`、`json_schema`、`function_calling`、`json_mode`、`text_json`，默认 `auto`。
- `decision_extra_body`：只作用于 decision 请求的 `extra_body`，例如关闭 DeepSeek 思考模式；旧字段 `signal_extra_body` 仍可读取，不能与 `decision_extra_body` 配置不同内容。

DeepSeek 可分别配置为 `deepseek + chat_completions`、`openai + responses`、`anthropic + messages`。使用官方地址和 DeepSeek 模型时，Frontier 会在三种协议中发送不含聊天正文的稳定 scope ID，用于服务端 KV cache、内容安全和调度隔离；兼容代理不会收到该扩展字段。图片和文件输入目前不应交给这些 DeepSeek profile。

### 模型路由

- 显式 `*_model_provider` 优先；没有显式 provider 时按模型名前缀推断：`deepseek*`、`gemini-*`、`claude-*`，其余走 OpenAI-compatible。
- 供应商 profile 名称必须存在；未声明的内置名称按上表默认值可用，未知名称报错。
- `models/` 模型目录为命中的模型卡注入上下文窗口、输出上限和能力元数据；目录外模型按未知模型降级。
- 绘画和视频的 provider `type` 必须为 `openai`。绘画协议跟随 provider 的 `api_mode`：`chat_completions` 调用 Images API（`/images/generations`，带参考图时用 `/images/edits`），`responses` 保留依赖 sub2api 重写顶层模型的 Responses `image_generation` 路径；请求失败不会切换协议重试。视频使用 OpenAI-compatible Videos API，不读取 `api_mode`。
- 每日新闻使用独立的 `daily_news_model` / `daily_news_model_provider`；检索来源与运行语义见 [新闻插件运维](news-plugin.md)。

## 其余配置段

### `[bot]`

`system_prompt` 是基础人设，与 `prompts/AGENTS.md` 中始终适用的全局操作规范组合后进入系统提示词；`{name}` 会按当前唤醒词注入。机器人名称不写在这里。

### `[features]`

`agent_enabled`、`paint_enabled`、`video_enabled` 控制对应入口；`qq_text_canary_enabled` 仅为旧配置兼容字段，不再控制路由；`laya_candidate_*` 控制可选的 Laya 候选预筛（默认关闭，详见 [Laya 决策 Provider](laya-decision-provider.md)）。`LAYA_API_KEY` 只从进程环境读取。

### `[key]`

仅保存非模型服务密钥：`nasa_api_key`（默认 `DEMO_KEY`）、`github_pat`。模型密钥放在对应供应商 profile；飞书凭据和 `LAYA_API_KEY` 等连接器密钥只从进程环境读取。

### `[platforms.feishu]`

飞书接入的非敏感字段：`enabled`、`app_id`、`bot_open_id`、`path`。`FEISHU_APP_SECRET`、`FEISHU_VERIFICATION_TOKEN`、`FEISHU_ENCRYPT_KEY` 只从进程环境读取。当前 QQ 插件不会自动注册飞书 lifecycle；飞书方案见 [Agent 与平台解耦设计](agent-platform-separation.md)。

### `[agent]`

`reasoning_effort`（`low` / `medium` / `high` / `xhigh`）在供应商 profile 的 `api_mode = "responses"` 时传给主模型；`message_image_text_threshold` 控制普通文字转长图的字符阈值（默认 500）；`message_media_fake_ip_fallback` 控制 Clash TUN Fake-IP DNS 回退，详见 [消息媒体网络](message-media-network.md)。

### `[speech_recognition]`

默认关闭，依赖包含在默认 `uv sync` 中。启用后首次使用自动安装默认 Windows x64 运行器、Q8 权重和 VAD；可通过 `auto_download = false` 关闭自动下载，资源准备单独受 `download_timeout_seconds`（默认 600）约束。路径是本机运维配置，不作为工具输入；自定义路径由运维管理。安装、复测与消息行为见 [本地语音识别](local-speech.md)。

### `[speech_synthesis]`

默认关闭，依赖包含在默认 `uv sync` 中。使用原生 PyTorch MOSS-TTS-Nano，首次使用自动安装固定修订并校验的本地模型；`auto_download = false` 用于预装资源离线运行，资源准备单独受 `download_timeout_seconds`（默认 600）约束。默认 4 个逻辑 CPU、单次 300 字、60 秒音频、180 秒推理总超时；与本地识别共用推理锁。`get_speech` 返回自动发送的 SILK 语音工件，共用 `[paint_policy]` 权限，另有本节的独立用户频率限制。两套资源可通过 `uv run --locked python scripts/setup_speech.py` 统一预下载。安装、试听与参数见 [本地语音合成](local-tts.md)。

### 访问策略

- `[agent_policy]`：决定是否响应 QQ 消息（`/acp` 也会二次校验）。`whitelist_mode = true` 时，非零群必须在 `whitelist_group_list` 中，且用户必须在 `whitelist_person_list` 中；个人和群黑名单优先，且黑名单在白名单模式关闭时仍然生效。
- `[auto_reply_policy]`：控制群聊中未被 @/唤醒时是否走主动回复判断；`whitelist_mode = true` 时仅 `whitelist_group_list` 中的群参与，`blacklist_group_list` 优先。
- `[paint_policy]`：绘画、视频和本地语音合成共用，覆盖 `/paint`、`/video` 命令和聊天 Agent 的媒体生成工具。黑名单优先；`whitelist_mode = true` 时用户号在 `whitelist_person_list` 中或群号在 `whitelist_group_list` 中即可使用，两份名单均为空时全部拒绝。可在 Dashboard 的“绘画与视频权限”中修改，保存后对后续调用生效。

### `[limits]`

绘画/视频限流与轮询、Agent 单轮超时、总任务超时、主图模型与工具调用预算。字段默认值与计数范围见 [Agent 执行控制](agent-execution-controls.md)。

### `[notifications]`

保存内置任务与通知的初始目标群。任务管理页的数据库映射在启动时会覆盖对应任务的推送群（`apod_everyday`、`earth_now`、`eq_usgs`、`daily_news`、`nrc_merchant_alert`），因此需要持久修改现有任务的接收群时应使用任务管理页。`announce_group_id` 用于更新完成后的重启通知；`earthquake_group_id` 也供 Wolfx 地震预警读取；`test_group_id` 仍会被解析，但当前没有读取者。

### `[storage]`

`query_message_numbers` 限制回复网关判断和历史准备时查询的近期消息数，这些近期历史会作为背景随当前请求交给主 Agent（编排层再截取最近 50 条）；`image_enabled`、`image_ttl_days`、`media_ttl_days`、`max_inline_images`、`max_inline_media_bytes`、`image_auto_cleanup` 控制附件缓存、内联媒体预算和清理。附件与历史语义见 [消息、上下文与投递边界](message_flow.md)，数据库结构见 [数据库说明](database-identity-migration.md)。

### `[debug]`

`agent_debug_mode` 打开 Agent 调试输出；生产环境保持关闭。

### `[dashboard]`

`password`、`jwt_secret`、`jwt_expire_hours`。默认密码和默认 JWT secret 会在启动时打印安全警告；未配置 JWT secret 时会生成仅保存在 `cache/.runtime_jwt_secret` 的运行时密钥。首次部署必须修改默认密码并设置随机 JWT secret。

### `[content_check]`

`enabled` 打开文本/图片内容安全检查。依赖随项目默认安装；首次检查会下载并加载对应 Hugging Face 模型和 tokenizer。

## Dashboard 保存与重载

Dashboard 设置页通过 `/api/dashboard/settings/*` 读写 `env.toml`：

- 保存串行处理并发更新，使用独立临时文件和原子替换；备份只保留最近 10 份。
- 敏感值在读取时脱敏；提交仍是脱敏值时保留原密钥。无实际变更时不创建备份。
- 保存后调用 `EnvConfig.reload()`，成功才递增 `EnvConfig.REVISION` 并切换运行时快照；失败时原子恢复旧文件并重新加载旧配置。
- 响应包含 `changed_fields`、`config_revision`、`activation` 和 `restart_required`。`env.toml` 管理的配置在后续请求/任务读取时生效，无需重启；模型相关子代理在下一轮按配置版本重建，已经开始的模型调用不会重新执行。
- `.env` 中的 NoneBot 启动参数和 `mcp.json` 的服务器列表仍需重启。
- `[sessions]` 段不存在时，Dashboard 保存会在文件中创建该段。

## 会话、工作区与 SOUL

- 每个群聊按 `group_id` 共享 `cache/sandbox/memory/group-{group_id}/SOUL.md`，每个私聊按 `user_id` 使用 `cache/sandbox/memory/dm-{user_id}/SOUL.md`。文件缺失时创建零字节文件，由 Agent 按稳定互动逐步记录局部人设和长期偏好；全局安全、权限和工具规范不会写入 SOUL。
- Agent 默认工作区是 `cache/sandbox/workspaces/{workspace_key}`；`/memory/{workspace_key}/` 映射到 memory 目录，`/skills/` 映射到仓库内置只读 Skill。
- 消息图片和上传文件保存在 `cache/sandbox/memory/{workspace_key}/...`；历史图片可重新注入为模型输入。
- 当前版本使用带 `group-` / `dm-` 前缀的会话目录；启动不会移动历史裸 `{id}` 目录，旧部署需先用包含迁移工具的历史版本完成升级。
- 主 Agent 默认接收当前请求和最近的聊天历史作为背景，但只回应当前请求；需要更早的前文时调用聊天历史工具。聊天原文仍作为可检索的权威数据保存并按群聊/私聊隔离。`[sessions]` 开启后的缓存行为见 [QQ 会话缓存](agent-sessions.md)。

## 诊断

配置错误会在启动或 Dashboard 保存时明确报错。常用检查：

```bash
uv run --locked python -c "from utils.configs import EnvConfig; print(EnvConfig.REVISION, EnvConfig.ADVAN_MODEL)"
uv run --locked pytest test/utils/configs_test.py -q
```

`[events]`、`[limits]`、`[sessions]` 的行为分别以对应专题文档和代码为准；修改配置前先阅读该段说明，不要依赖历史部署的旧字段。
