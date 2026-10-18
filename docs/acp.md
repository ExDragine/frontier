# ACP 接入

[Agent Client Protocol (ACP)](https://agentclientprotocol.com/) 是 Frontier 的内置能力，包含两个方向：

- **Frontier 作为客户端**：在 QQ 中通过 `/acp` 命令调用一个或多个外部本地 ACP Agent；也可把指定 Agent 注册为 Deep Agents 子代理。
- **Frontier 作为服务端**：通过 stdio 暴露 Frontier 内置 Deep Agent，供其他 ACP 客户端启动和驱动。

协议实现、配置示例和字段差异集中在本仓库的 [ACP 插件](../plugins/acp/README.md)；两版协议规范见 [ACP v1 接入规范](../plugins/acp/docs/acp-v1.md) 与 [ACP v2 Draft 接入规范](../plugins/acp/docs/acp-v2.md)。

## 作为客户端：快速开始

复制配置示例并在项目根目录填写：

```bash
cp plugins/acp/acp.json.example acp.json
```

`acp.json` 同时只能处于以下状态之一：不存在（ACP 不可用）、存在且校验通过。示例默认配置一个名为 `dsh` 的 Agent，指向 DeepSeek Harness 的 ACP 演示服务；使用前需要把示例中的绝对路径替换成本机 checkout。

启动后可在 QQ 中使用 `/acp <任务>`。`/acp` 仅超级用户可用，并且会再次经过 `[agent_policy]` 的访问名单校验：白名单模式开启时用户和群都必须在白名单中，个人或群黑名单始终优先。聊天消息不能指定任意启动命令，Agent 子进程只能来自管理员维护的 `acp.json`。

## `acp.json` 配置

根节点只接受 `default` 和 `agents`：

- `default`：未使用 `--agent` 时选择的 Agent 名称。
- `agents`：非空对象，键是 Agent 名称；名称只能包含字母、数字、点、下划线和连字符。`agents.<名称>` 拒绝未知字段。

单个 Agent 的字段：

| 字段 | 说明 |
| --- | --- |
| `command` | 必填，ACP Agent 的可执行文件 |
| `args` | 字符串数组，传给子进程的参数 |
| `env` | 额外环境变量对象，键和值都是字符串 |
| `inherit_env` | 显式继承的宿主环境变量名白名单；缺少任何一项都会拒绝启动，且不能与 `env` 重名 |
| `description` | 1–500 字符；`expose_as_subagent` 开启时作为子代理描述 |
| `expose_as_subagent` | 是否注册为 Deep Agents 子代理，默认 `false` |
| `auth_method` | 初始化阶段要求 Agent 公布的认证方式 ID；不匹配时明确报错 |
| `permission_policy` | `deny`、`allow_once` 或 `allow_always`，默认 `deny` |
| `timeout_seconds` | 单次任务超时，1–3600 秒，默认 600 |
| `protocol_version` | `1` 或 `2`，默认 `1` |

在 POSIX 系统上，如果 `acp.json` 允许 group 或 other 写入，启动时会打印权限警告。配置错误会在 `/acp` 命令中显示为“ACP 配置错误”，不会静默降级。

## `/acp` 命令

```text
/acp <任务>
/acp --agent <名称> <任务>
/acp --list
/acp --cancel [--agent <名称>]
/acp --reset [--agent <名称>]
```

- `/acp <任务>` 使用 `default` Agent，`--agent` 选择其他 Agent；也可以写成 `--agent=<名称>`。
- `--list` 列出已配置的 Agent 和默认项；`--cancel` 取消当前 turn；`--reset` 关闭连接并重建会话。
- 命令支持文本、图片和音频输入；视频输入会被省略并附加说明。
- 群聊和私聊各自一个 scope：群聊使用 `group:{group_id}`，私聊使用 `dm:{user_id}`，同一个 Agent 在同一 scope 内复用进程和会话。
- QQ 群聊和私聊只发送最终回复、媒体工件或必要的失败提示，不发送思考、工具调用或过程进度；原始思考不外发。最终文本和媒体会经过输出安全检查，投递失败时提示重试。

## 工作区、生命周期与缓存清理

- 外部 Agent 的进程工作目录是 `cache/acp/workspaces/<scope 哈希>`；每个 Agent + scope 组合拥有独立进程和会话。
- `acp.json` 在每个新连接前重新读取；命令、参数、环境变量、权限策略、协议版本等配置指纹变化时，下次调用会重建连接。
- 每日缓存维护会关闭闲置 ACP 进程并删除其 workspace；正在执行的 scope 不受影响。
- 超时或异常后关闭进程，下一次请求创建新连接。

## 子代理桥接

把某个 Agent 的 `expose_as_subagent` 设为 `true` 后，它会以 `acp-<名称>` 注册为 DeepAgents 子代理，主 Agent 可以按 `description` 将任务委托给它。子代理返回的媒体会保存到当前 Frontier workspace 的 `/acp-artifacts/`，不会把大段 base64 直接塞回模型上下文。该开关默认关闭，避免仅用于 `/acp` 的进程被模型意外调用。

## 协议版本

- 每个 Agent 的 `protocol_version` 可设为 `1` 或 `2`，省略时保持 v1；修改后下次调用自动重建连接。
- 可以同时配置两版 Agent，通过 `--agent` 选择。版本不匹配时明确报错，不自动降级，也不会把同一任务自动重发到另一版协议。
- SDK 锁定为 `agent-client-protocol==1.0.0rc1`：v1 使用标准 `acp` API，v2 使用官方 `acp.experimental.v2`（schema v2.0.0-alpha.3）。SDK 是预发布版，v2 是草案协议。

## 作为服务端：Frontier 内置 ACP server

```bash
uv run python -m plugins.acp
# v2 Draft
uv run python -m plugins.acp --protocol-version 2
```

`scripts/frontier_acp.py` 保留为兼容入口，转发到本插件的 CLI；普通 Python 导入不会注册 QQ 命令，NoneBot 加载 `plugins.acp` 时才注册命令和生命周期钩子。

服务端能力与边界：

- 复用同一个 `FrontierCognitive` 执行链，支持文本、图片和音频输入，并把已清洗的进度、工具状态、最终文本及内联媒体映射为 ACP 更新。
- v1 支持初始化、新建会话、列出会话、prompt、取消和关闭会话；v2 的 prompt 立即确认接收，完成与取消通过 `state_update` 表达，并支持进程内会话恢复和回放。单个 stdio 进程固定使用启动时选择的版本，需要同时提供两版时启动两个进程。
- 每个 ACP session 使用独立的内部身份、thread 和 sandbox workspace；客户端传入的 `cwd` 只作为协议元数据，不会成为文件访问授权。额外工作目录和客户端 MCP servers 会被拒绝。
- 为防止权限继承和 Agent 环路，ACP 入站会话不暴露 QQ 平台工具、聊天记忆和 ACP 子代理，只保留隔离 workspace、文档分析及模型原生能力。
- 服务端 stdout 只用于协议，日志发往 stderr；v2 的会话和回放数据仅保存在服务端进程内，跨重启恢复不在支持范围内。

## DeepSeek Harness (DSH) 接入

DeepSeek Harness 不再使用 Frontier 内置的 SDK/JSON-RPC 适配层，而是作为普通 ACP Agent 接入。官方仓库提供 `pnpm run demo:acp` 的 JSON-RPC stdio server；`plugins/acp/acp.json.example` 已包含对应配置。

使用步骤：

1. 克隆并构建 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)。
2. 把 `acp.json.example` 中 `args` 的绝对路径替换为本机 checkout。
3. 在 Frontier 进程环境中设置 `DEEPSEEK_API_KEY`（示例通过 `inherit_env` 显式继承）。
4. 使用 `/acp --agent dsh <任务>`。

DSH 仍处于 developer preview，建议将 checkout 固定到经过验证的 commit。DSH 当前的官方 ACP 自动化接口只发送已提交的 assistant 文本/图片，不公开推理、工具活动、计划等实时进度；因此 Frontier 能收到最终结果和权限请求，但不会复现原 `/dsh` 的专用进度事件。DSH 的模型、供应商、会话和工具配置均由 DSH 自己管理，不再读取 `env.toml` 的专用 `[dsh]` 段。

## 安全边界

- ACP Agent 是本地子进程，工作区不是操作系统 sandbox；它仍可能访问 Frontier 进程有权限读取的其他路径。不要把它当作不可信代码的隔离手段。
- `permission_policy` 默认为 `deny`，只有明确改为 `allow_once` 或 `allow_always` 时，Frontier 才会自动批准 Agent 的工具权限请求。
- `inherit_env` 是显式白名单，只会把列出的宿主变量传给对应子进程；缺少任何一项都会拒绝启动，避免无意泄露全部环境变量。
- 客户端不声明宿主文件系统或终端执行能力；未实现的认证、加载、恢复、分叉、模式与配置变更方法不会被宣称为可用能力。
- 服务端不要求认证，也不提供 HTTP／WebSocket 服务；面向远程或不可信客户端前需要额外的传输与鉴权层。
- SDK 与 v2 协议均为预发布状态，升级 SDK 不会自动把旧配置切换到 v2。

## 测试

```bash
uv run --locked pytest test/plugins/acp/ test/integration/acp_protocols_test.py test/integration/acp_imports_test.py -q
uv run --locked ty check plugins/acp scripts/frontier_acp.py
```

单元测试覆盖命令解析、配置校验、权限与取消；真实 stdio 契约测试连接两版测试服务端，使用确定性运行时，不发起模型 API 请求。

## 相关文档

- [ACP 插件目录说明](../plugins/acp/README.md)
- [ACP v1 接入规范](../plugins/acp/docs/acp-v1.md)
- [ACP v2 Draft 接入规范](../plugins/acp/docs/acp-v2.md)
- [ACP 配置示例](../plugins/acp/acp.json.example)
- [Agent 与平台解耦设计](agent-platform-separation.md)
