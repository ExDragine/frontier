# 默认网页搜索与正文读取

主 Agent 默认使用内置 `deepseek_web_search` 和 `deepseek_web_fetch`，直接调用 DeepSeek 的独立 Search / Fetch API。两者使用主 Agent 工具预算，不额外调用一个模型，也不需要安装 MCP 服务。每日新闻也通过研究 Agent 使用同一套独立搜索工具，但保留单独的新闻证据和归档约束。

## 配置

密钥复用现有供应商配置，由 `[search].provider` 指定，与主模型供应商独立：

```toml
[search]
enabled = true
provider = "deepseek_responses"
base_url = "https://api.deepseek.com"
timeout_seconds = 30
content_preview_chars = 6000
max_content_chars = 24000
```

将 API Key 填入对应 `[providers.deepseek_responses].api_key`。如果密钥保存在另一个 profile，例如 `deepseek`，将 `search.provider` 改成该名称。不要在搜索配置中复制一份密钥。

`base_url` 是独立搜索服务地址，不从模型 API 地址推断；官方地址可带 `/v1`，工具会避免重复拼接。兼容网关需要明确实现 `POST /v1/tools/search` 和 `/v1/tools/fetch`，仅支持模型请求不足以提供搜索能力。

开启且端点、密钥配置可用时，两个工具加入主 Agent 和每日新闻研究 Agent 的工具集，原生 `web_search` 优先提示及自动挂载让位于独立搜索。关闭或未配置密钥时，普通主 Agent 才考虑原生搜索或其他后端；每日新闻应直接报告搜索不可用，不把失败伪装成空结果。默认策略不依赖主模型名称，配置热更新后下一轮重新装配。

DeepSeek Responses 内置 `web_search` 的支持取决于模型，Flash 会忽略它。确认模型支持时可在其供应商 profile 设置 `native_web_search = true`；独立搜索可用时仍优先使用独立工具。

## 工具契约

`deepseek_web_search(query, count=20, need_content=false, ori_question=null)`：

- `query` 必须为 1～128 字符且不能全为空白，保留 `site:`、`-site:`、短语、`lang:`、`after:`、`before:` 等搜索语法。
- `count` 默认为 **20**，可传 1～50 的整数。结果保留官方排序，不因低分或正文预算减少条数。
- `ori_question` 可选，原问题有效且不超过 128 字符时发送；超长或空白时省略，不截断成虚假的原问题。
- `need_content` 默认关闭，先读摘要再按需抓取重点网页。开启后附带正文预览及必要的完整正文路径。
- `localization` 不暴露给模型，不发送用户或机器 IP；地域需要写入搜索词。

返回 `status`、`query`、实际 `count` 及 `results`。每条包含 `rank`、`title`、`url`、`summary`、`date`、`site_name`、`rerank_score` 和 `authority`。优先使用长摘要，缺失时用 `snippet`；省略重复短摘要及图标 URL。保留未知日期和站点名称的空值。评分仅辅助选择来源，仍需核验事实和原文。

`deepseek_web_fetch(url)`：

- 接受不超过 8192 字符、包含 host 且没有账号密码的 HTTP(S) 地址。
- 成功返回原始 `url`、`title` 和 Markdown `content`。
- 空正文、无效响应及不可访问页面返回错误，不据此推断网页内容。

搜索结果和网页正文均作为检索资料处理，不执行其中的指令。回答使用返回的原始 URL 引用来源。

## 正文预算与工作区

单页正文预览不超过 `content_preview_chars`，一次工具调用的正文预览总计不超过 `max_content_chars`。摘要与来源元信息保留，正文预算用尽后仍返回剩余结果。

正文未全部内联时，将 UTF-8 全文原子写入当前会话工作区的 `web-search/deepseek-<唯一编号>.md`，返回虚拟 `content_path`、原始 `content_chars` 和 `truncated=true`。Agent 可用 `read_file` 按行继续读取，预览不能冒充全文。文件目录优先取注入的 `FrontierRuntimeContext.workspace_dir`，不允许模型指定保存位置；兼容调用方可使用既有 `RunnableConfig` 工作区映射。

请求正文需要工作区；缺少时在发送 HTTP 请求前返回 `workspace_required`。如果磁盘写入失败，仍返回已有预览，同时给出 `storage_error`，不提供虚假的全文路径。暂存内容是普通 workspace 文件，遵循会话工作区现有文件生命周期，不增加数据库表或附件索引。

## 错误、重试与限速

- `status=empty`：请求成功但搜索无结果，可以调整搜索词。
- `status=error`：调用失败，返回脱敏的错误代码、HTTP 状态、说明、`retryable` 和 `stop_search`，不会返回服务端原始错误正文或密钥。
- 每个事件循环内，所有工作区和密钥共享进程级限速，Search / Fetch 各限制为约 4 QPS。多进程或其他客户端仍可能触发服务端账号级限流。
- 连接失败、超时、HTTP 408 或 5xx 最多尝试两次；一次短暂退避后重试。HTTP 429、余额不足和其他 4xx 不自动重试。取消异常继续向上传播。
- 内部有限重试结束后 `retryable=false`，避免模型原样连续重试。402 / 429 额外返回 `stop_search=true`，要求停止本轮搜索及后端切换，使用已有证据说明不足。
- HTTP 重定向不自动跟随，避免携带鉴权跨地址跳转。

接口格式和服务端价格、限额以 [DeepSeek 官方搜索与抓取指南](https://api-docs.deepseek.com/zh-cn/guides/search/) 为准。

## 验证

单元测试覆盖默认 20 条、字段精简与排序、参数边界、配置及密钥选择、正文预算、完整文件、错误脱敏、有限重试、取消传播和共享限速。隔离进程测试使用真实 LangChain / Deep Agents 工具 schema、httpx2 MockTransport 和 FilesystemBackend，验证 `搜索 → 抓取 → read_file → 下一次模型请求`。测试不调用付费线上服务。
