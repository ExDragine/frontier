# 新闻模块、Exa MCP 与日志检查

检查日期：2026-09-20。初次检查基线：`5f6830c`。下文保留原始问题及复现证据；这些问题已在后续分支合并修复中处理。

## 合并后的修复

已合并 `feat/news-plugin-reliability` 和 `fix/exa-mcp-startup`。新闻分支内容此前已压缩进入主分支，本次补齐合并关系；MCP 分支提供单服务发现超时配置和 Exa 直连示例。

额外修复了下面四项新闻问题，以及生成次数上限、归档清理、长任务租约被缩短、期次时间缺失和投递失败误记 success。MCP 增加失败服务退避重发现、工具注册表和 Agent 组件刷新，以及 HTTP/SSE 认证头传递。日志占位符修复同时保留。

回归测试位于 `test/news/test_reliability.py`、`test/plugins/clockwork_test.py`、`test/tools/basic_info_tools_test.py`、`test/utils/agents_test.py` 和 `test/utils/mcp_test.py`。具体运行语义见 [新闻运维说明](news-plugin.md) 和 [架构说明](architecture.md)。以下“待修复”及测试数量描述均属于初次检查记录。

合并修复后的全量回归为 **897 passed**（3 条既有第三方警告），ruff、CI 指定类型检查、`git diff --check` 均通过。使用合并后代码连接 Exa 官方 HTTP MCP，再次成功发现 `web_search_exa`、`web_fetch_exa`。没有执行真实 QQ 投递或付费搜索／模型生成。

## 结论

新闻生产已经独立到 `plugins/news`，Clockwork 会将原任务处理器切换过去并保留既有时间、启停状态和目标群。检索使用 Exa/Tavily REST API，编辑与复核使用独立结构化模型调用，归档使用 `news.db`，不再通过主聊天 Agent 生成新闻。

但是失败恢复与投递边界还不能认为完成。下面四项已在临时 SQLite 库、合成证据、模拟模型与模拟发送器中复现，未调用真实 QQ 发送或收费搜索／模型接口。

## 新闻模块待修复问题

### P1：送达后的数据库异常会导致重复补发

位置：[delivery.py](../plugins/news/delivery.py#L24)。同一个 `try` 同时包住平台发送和 `finish_delivery(..., "sent")`。平台已发送成功、落库失败时，通用异常分支将记录写成 `failed`，此后补发会再次发送。

复现：模拟发送成功，再使 `sent` 状态更新抛出 `OSError`，记录变成 `failed`；显式重试后发送计数为 **2**。建议分开发送和确认入库的异常边界，已送达但确认失败的记录不得进入可重发状态。

### P1：不合格草稿会阻塞同一期的后续重建

位置：[service.py](../plugins/news/service.py#L42)。草稿在最终复核和最少条数检查之前被保存。失败后再次生成同一期，只要存在 `payload` 就跳过编辑，一直复核同一份草稿。

复现：要求至少 2 条，有 2 条有效证据，第一次编辑仅返回 1 条。连续生成两次都报 `InsufficientEvidence`，编辑器只被调用 **1 次**，即使第二次编辑原本能够返回完整内容，也不会被调用。建议区分临时复核调用失败与草稿内容不合格，后者允许在有界尝试次数内重新编辑。

### P2：`/news retry` 会给原本没有投递记录的群首次发送

位置：[commands.py](../plugins/news/commands.py#L43)、[delivery.py](../plugins/news/delivery.py#L14)。`retry_failed` 只更新失败记录，但命令没有检查是否实际更新，随后 `deliver` 会创建全新目标记录并发送。

复现：对没有记录的合成群调用同一补发链路，实际发送 **1 次**。命令虽然限制为超级用户，但行为不符合“仅 failed 状态允许显式重试”的提示。建议重试只消费成功重置的已有目标，不创建新投递目标。

### P2：少量有效结果不会触发备用检索来源

位置：[sources.py](../plugins/news/sources.py#L131)。每个查询只要首选来源返回任意有效文章就立即返回，所有查询合并去重后数量不足时，也不会再尝试其他来源。

复现：首选来源在多个查询中均返回同一条有效文章，备用来源可返回足量证据；最终只有 **1 条**，备用来源调用数为 **0**。建议在聚合去重后按缺口进行有界补充检索。

另外，`max_generation_attempts` 和 `retention_days` 目前只有配置声明，没有对应的尝试次数控制和归档清理调用。渲染函数传入空日期／时间，图片页眉和页脚缺少期次时间。新闻发送全部失败时，handler 仍正常返回 `TaskRunResult`，Clockwork 因而会记录任务 `success`；只能从输出摘要的投递状态看出失败。

## Exa HTTP MCP

本次分别对公开端点及本机 Exa 配置执行真实 `list_tools()`，两次均成功返回：

```text
web_search_exa
web_fetch_exa
```

本机相关条目使用 `http`，地址为 `https://mcp.exa.ai/mcp`；对应当前适配器的 `StreamableHttpTransport`。只检查了 Exa 条目和工具发现，没有调用搜索工具，也没有将配置凭据写入输出。

这能确认检查时当前环境的握手和工具发现可用，不能证明此前的偶发失败已被修复。`utils/mcp.py` 和 `tools/mcp_client.py` 在新闻提交中没有修改；新闻模块改走 REST 也不会修复 Agent 的 MCP 加载。

仍存在明确缺口：[mcp_client.py](../tools/mcp_client.py#L129) 将失败服务转为空列表，然后永久缓存合并结果；[工具注册器](../tools/__init__.py#L134) 和 Agent 组件又各自缓存工具集合。首次发现时若 Exa 短暂不可用，进程内后续请求不会自动重新发现该服务。需要同时设计失败服务的退避重发现和工具集合／Agent 组件刷新，仅在底层增加重试入口还不够。

当前配置校验还不接受 `headers`，HTTP 适配器也不传递认证头。如果将来配置 Exa 请求头认证，应同步修改这两处。现有本机条目没有配置认证头，此点不是本次连接的故障原因。Exa 官方支持该端点和请求头认证：[官方仓库](https://github.com/exa-labs/exa-mcp-server)。

## 已修复：后台原样输出 `%s`

NoneBot 的 logger 使用 Loguru 的 `{}` 参数格式；标准库 `logging` 使用 `%s`。部分模块混用了两套写法，导致参数没有插入日志。格式约定见 [Loguru 文档](https://loguru.readthedocs.io/en/stable/api/logger.html)。

已修正 18 个文件中的 69 处 Loguru 调用，包括 Agent 消息、附件、提示词、ACP 和后台工具日志，保留浮点精度。标准库 logging 的 `%s` 调用继续使用原写法。新增真实错误日志断言，以及检查导入来源的格式回归检查，防止再次混用。

验证入口：`test/utils/logging_format_test.py`。原有新闻／MCP／Clockwork 定向测试 20 项通过；日志和消息投递定向回归 72 项通过。最终全量回归 **875 passed**，ruff、CI 指定的类型检查和 `git diff --check` 均通过。新闻异常场景通过独立合成数据探针复现，现有通过的测试不代表这些缺口已修复。真实 QQ 投递、付费搜索和付费模型生成未执行。
