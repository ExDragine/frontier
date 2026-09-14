# Frontier ACP v2 Draft 接入规范

对应 [官方 v2 迁移规范](https://agentclientprotocol.com/protocol/v2/migration)，基于
Python SDK `1.0.0rc1` 的 `acp.experimental.v2` 与 `schema-v2.0.0-alpha.3`。
v2 仍处于 Draft，需显式启用；[v1](acp-v1.md) 保持默认。参考
[官方 Python SDK](https://github.com/agentclientprotocol/python-sdk)。

## 启用两版 Agent

`acp.json` 可以同时配置 v1、v2；名称区分不同进程配置，群聊和私聊各自隔离。

```json
{
  "default": "legacy",
  "agents": {
    "legacy": {
      "protocol_version": 1,
      "command": "/absolute/path/to/v1-agent",
      "permission_policy": "deny"
    },
    "next": {
      "protocol_version": 2,
      "command": "/absolute/path/to/v2-agent",
      "permission_policy": "deny",
      "timeout_seconds": 600
    }
  }
}
```

用 `/acp --agent next <任务>` 选择 v2；控制命令与 v1 相同。
`protocol_version` 只接受整数 `1` 或 `2`。修改版本会在下次请求重建连接；不匹配时拒绝
执行，不把同一任务自动重发到另一版协议。

Frontier 服务端使用独立的 v2 入口选择：

```bash
uv sync --locked
uv run --locked python -m plugins.acp --protocol-version 2
```

单个 stdio 进程固定使用启动时选择的版本；需要同时提供两版时启动两个进程。

## 与 v1 的差异

| 项目 | v1 | v2 Draft |
| --- | --- | --- |
| 初始化 | `clientInfo`／`agentInfo`、各自的 capabilities 字段 | 双方均使用 `info`、`capabilities` |
| 图片／音频能力 | `promptCapabilities.image: true` | `capabilities.session.prompt.image: {}`，按是否存在判断 |
| prompt 返回 | 完成时返回 `stopReason` | 接收后立即返回 `{}` |
| 任务结束 | prompt 响应 | `state_update` 的 `idle + stopReason` |
| 消息身份 | chunk 的 `messageId` 可选 | 消息更新及 chunk 都带 Agent 生成的 `messageId` |
| 整条消息 | 流式 chunk | `agent_message` 覆盖同 ID 内容，chunk 追加 |
| 工具事件 | `tool_call` + `tool_call_update` | 统一为 `tool_call_update` |
| 权限 | 请求中的 `toolCall` | `title` 和 `subject` 分离，策略仍使用 options |
| 登录 | `authenticate`、认证描述的 `id` | `auth/login`、`methodId` |

## v2 生命周期

Frontier 服务端先验证会话和输入，再确认 prompt，后台依次发送：

```json
{"sessionUpdate":"user_message","messageId":"user-opaque-id","content":[{"type":"text","text":"任务"}]}
{"sessionUpdate":"state_update","state":"running"}
{"sessionUpdate":"agent_message","messageId":"agent-opaque-id","content":[{"type":"text","text":"结果"}]}
{"sessionUpdate":"state_update","state":"idle","stopReason":"end_turn"}
```

以上是 `session/update` 的 `params.update` 示例，每次通知另带 `params.sessionId`。
实际 ID 由服务端生成。同一会话繁忙时拒绝新的 prompt，不隐式排队；不同会话独立执行。
取消会等运行时退出后发送 `idle/cancelled`。已确认接收后的执行异常发送通用失败消息和
`idle/refusal`；不通过协议返回异常堆栈或密钥。进程退出时取消未结束任务。

客户端等待结束状态而不是 ACK，超时覆盖整个任务。结束状态不能来自其他会话；没有
`stopReason` 的 idle 不作为本轮完成依据。支持 `requires_action` 等中间状态，收到取消后
拒绝尚未完成的权限请求。端点进程在结束状态前退出会报错并丢弃连接。

消息覆盖遵循三态规则：省略 `content` 保留旧内容；`null`／`[]` 清空；数组替换全部内容。
同 ID 后续 chunk 追加，交错 ID 仍各自归并。思考仅转为通用进度提示；工具内容和终端数据
不会被当作最终 assistant 回复或在宿主执行。

## 会话及支持范围

Frontier 声明 `capabilities.session`，实现新建、列出、恢复、关闭、prompt、取消和更新。
`session/resume` 要求匹配原会话 cwd。省略 `replayFrom` 时不回放；传
`{"type":"start"}` 会在返回前按顺序回放已记录的通知，保留消息 ID。
关闭会话取消任务并禁止直接 prompt；恢复后可继续，历史对话会进入运行时上下文。
会话和回放数据仅存于服务端进程内，跨重启恢复不在支持范围内。

文本、资源链接、图片和音频支持与 v1 一致。资源链接只作引用，视频、嵌入资源、外部 MCP、
额外工作目录、会话分叉／删除／配置选项等不声明支持。服务端不要求认证；客户端仅支持
对端声明的 `type: agent` 登录流程，终端交互登录不支持。客户端 elicitation 返回 decline。

沿用 [v1 的 sandbox 边界](acp-v1.md)：客户端 cwd 不转为宿主目录访问权限。当前交付是
stdio 会话与媒体能力，未实现 HTTP／WebSocket 服务。

## 验证

```bash
uv run --locked pytest test/plugins/acp/ test/integration/acp_protocols_test.py -q
```

单元测试核对覆盖更新、取消、回放、权限与参数边界；真实 stdio 测试连接两版 Frontier
测试服务端，核对序列化、媒体、ACK 与完成的区别、协议切换、错误版本以及超时清理。
测试服务端使用确定性运行时，不发起模型 API 请求。
