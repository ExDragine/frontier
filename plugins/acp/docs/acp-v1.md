# Frontier ACP v1 接入规范

对应 [ACP 官方 v1 规范](https://agentclientprotocol.com/protocol/v1/overview)，使用
`agent-client-protocol==1.0.0rc1` 的标准 `acp` API。SDK 版本与协议版本是两个概念；
升级 SDK 不会把旧配置切换为 v2。另见 [v2 接入规范](acp-v2.md)。

## QQ 客户端配置

在 `acp.json` 中为每个 Agent 选择协议版本。省略 `protocol_version` 等同于 `1`。

```json
{
  "default": "legacy",
  "agents": {
    "legacy": {
      "protocol_version": 1,
      "command": "/absolute/path/to/agent",
      "args": ["--stdio"],
      "permission_policy": "deny",
      "timeout_seconds": 600
    }
  }
}
```

使用 `/acp <任务>` 或 `/acp --agent legacy <任务>`；`--list` 查看 Agent，
`--cancel` 取消当前任务，`--reset` 关闭连接并重建会话。
现有 `env`、`inherit_env`、`auth_method`、`expose_as_subagent`、访问名单等配置继续有效。
配置文件只由管理员维护，聊天消息不能指定任意启动命令。

## 消息生命周期

1. 通过 stdio 建立 JSON-RPC 2.0 连接。
2. `initialize` 发送 `protocolVersion: 1`、`clientInfo`、`clientCapabilities`，核对返回版本。
3. 配置了 `auth_method` 时，核对 Agent 公布的 `authMethods[].id` 并调用 `authenticate`。
4. `session/new` 返回 `sessionId`。同一个 Agent、同一个群聊或私聊 scope 复用进程和会话。
5. `session/prompt` 在任务执行期间保持挂起；`session/update` 传递消息块与工具进度。
6. prompt 响应中的 `stopReason` 表示结束。`session/cancel` 是通知，取消后仍等待 prompt 结束。

客户端根据 `agentCapabilities.promptCapabilities` 判断图片和音频支持。文本是基线输入；
不支持的媒体附带省略说明。群聊只发送最终回复，私聊可发送脱敏后的进度；原始思考不外发。
权限默认拒绝；`allow_once`／`allow_always` 仅匹配对端提供的对应选项。
客户端不声明宿主文件系统或终端执行能力。超时或异常后关闭进程，下次请求新建连接。

## Frontier 作为 Agent

```bash
uv sync --locked
uv run --locked python -m plugins.acp --protocol-version 1
```

支持初始化、新建会话、列出会话、prompt、取消和关闭会话；图片与音频输入可用。
未实现的认证、加载、恢复、分叉、模式与配置变更方法不会被宣称为可用能力。
服务端 stdout 只用于协议，日志发往 stderr。

每个会话复用 Frontier 的受限运行时身份和 sandbox。`cwd` 只作为元数据；这是 Frontier
与通用编码 Agent 工作目录语义的差异，传入路径不授予宿主文件访问权。额外目录和客户端
MCP servers 会被拒绝。QQ 平台工具、QQ 聊天记忆与 ACP 子代理不会暴露给入站会话。

## 兼容与验证

旧 `acp.json` 和现有 `/acp` 命令保持兼容。SDK 1.0 移除了旧消息构造 helper，
Frontier 已改用官方 schema 类型，线上 JSON-RPC 字段仍按 v1 发送。
测试覆盖真实 stdio 的初始化、媒体输出、多轮会话复用与取消，以及 QQ 投递路径。
示例配置中的路径需要替换为实际 Agent 程序；测试不调用真实模型服务。
