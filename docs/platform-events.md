# Milky 申请事件处理

`plugins.events` 自动监听好友申请、用户入群申请、成员邀请他人入群申请、邀请机器人入群四类事件。
普通消息仍走 `plugins.agent`；戳一戳、群解散和其他通知保留原有处理器。第一版不让模型扫描所有通知，
也不提供拥有主聊天工具全集的多步 Event Agent。

默认 `[events].enabled = true`，未配置的请求类型使用 `record`：只记录，不调用模型、不操作平台、不发聊天消息。
没有读取或修改部署环境真实配置的要求；按下面示例在自己的配置中选择启用范围。

## 配置

```toml
[events]
enabled = true
workers = 2
timeout_seconds = 30
ttl_seconds = 3600
max_pending = 1000
retention_days = 30

# 先只评估，查看 /events 后再改为 decision。
[events.rules.friend_request]
mode = "shadow"
actions = ["accept", "defer"]
initiator_ids = [123456789] # 可选授权范围；空列表表示不限制发起者
instructions = "只有申请附言明确说明已约定的测试用途时同意，否则保留待处理。"
allow_filtered = false

# 群级规则完整替换该类型的全局规则，不进行字段合并。
[events.groups."987654321".group_join_request]
mode = "decision"
actions = ["accept", "reject", "defer"]
instructions = "按本群实际入群标准填写；信息不足时 defer。"

# 仅处理指定邀请者邀请机器人加入这个群的请求。
[events.groups."987654321".group_invitation]
mode = "rule"
initiator_ids = [123456789]
actions = ["accept", "defer"]
action = "accept"
```

模式：`ignore` 不落库；`record` 只记录；`rule` 执行配置的固定 action；`shadow` 只记录模型建议；
`decision` 判断后执行。`defer` 始终可选；发起者不在允许范围或过滤请求未获授权时只能 defer。
修改规则通过现有 `EnvConfig.reload()` 生效，执行前再次核对配置；workers 数量在重启时调整。
配置改动不会自动重放已记录、已评估或待人工处理的事件。

## 管理

只有 NoneBot `SUPERUSERS` 超级用户可在 QQ 私聊使用：

- `/events`：显示最近 20 条记录的完整事件 key、机器人、状态、建议和结果摘要，不回显申请附言。
- `/events retry <完整事件 key>`：让未过期且从未尝试写操作的 recorded/deferred/shadow 事件，按当前策略重新排队。
- `/events reconcile`：只读核实最近记录中的 unknown 结果；绝不重新发送平台操作。

好友同意、拒绝、删除和机器人入群邀请的聊天工具也限制为超级用户；群入群审批工具保留原有目标群管理员校验。
工具优先使用冻结的运行时身份，申请附言、显示名或工具参数不能代替调用者身份。

## 执行和恢复

独立的 `platform_event_inbox` 与 `platform_event_actions` 表保存在项目数据库中，不进入聊天历史或会话 checkpoint。
原始申请正文上限 4000 字符；后台日志只记录错误类型，管理员命令不暴露正文。

- 去重 key 包含 Bot 身份。群请求使用通知/邀请序号；好友请求用 UID、事件时间、附言和来源指纹区分重新申请。
- SQLite 条件领取、有限 worker 和每 Bot/群（好友则每 UID）的锁限制并发；超出待处理容量的事件记录为 deferred。
- 模型只返回给定动作，不持有任何工具。拒答、无效结构、超时、权限不足和状态不明都保留待处理。
- 执行器绑定事件 Bot，读取真实申请状态，检查过滤标记；群审批还实时查询机器人管理员权限。
- 好友列表每个过滤分区最多读取 100 项，群通知最多各读 3 页。未找到目标时不推断为可处理。
- 写操作前持久化唯一动作记录。成功以平台返回为准；异常、取消或重启中断写操作记为 unknown。
- 过期评估租约可以重新领取；过期执行租约只能只读核实。远端状态已确定时标为 resolved，并记录是否与建议一致，
  不声称一定是本程序完成了该操作。后台每分钟尝试核实最多 20 条 unknown。
- 终结记录过期且超过 retention_days 后清理；unknown 保留供人工核实。清理后重投旧事件仍受发生时间 TTL 限制。
- 不自动通知群聊或申请人，不展示思考、进度，也不调用回复转图链路。操作结果通过日志状态和管理员命令查看。

Milky 当前没有“邀请机器人入群”的状态查询接口。这类自动操作只接受发生后 60 秒内的新鲜事件；
旧邀请转为待处理，执行结果不确定时必须人工核实，不自动重试。

第一版受限决策入口是 `utils/agents/event_agent.py`，复用配置中的 Decision 模型；没有新模型、MCP 或 OpenAI Decisions API 依赖。
生产建议一个 Frontier 进程拥有同一 Bot 与数据库；跨进程数据库领取有条件保护，但不会协调聊天工具中的人工操作。
