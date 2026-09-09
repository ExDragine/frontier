# Milky 1.3 适配

依据 [Milky v1.3.0 发布说明](https://github.com/SaltifyDev/milky/releases/tag/v1.3.0)，
项目声明 `nonebot-adapter-milky>=1.3.0`，锁文件当前使用 1.3.0。

| 协议变更 | Frontier 行为 |
| --- | --- |
| 接收 `markdown.content` | 正文进入消息提取、回复网关、上下文、引用/转发归一化及历史查询摘要。Markdown 中的图片链接保留为文本，不在门控前下载。 |
| 私聊文件 `is_self_send` | 文件下载工具显式提供该参数；引用文件恢复按真实发送者判断方向，`user_id` 仍是私聊对端。普通收到的文件默认 false。 |
| `persist_group_file` | 新增同名 Agent 工具，把现有群临时文件转存为永久；复用目标群管理员/群主检查，保留为直接写操作工具。 |
| 转发节点可选 `time` | `send_forwarded_message` 支持向群或好友发送文本合并转发，节点包含发送者、正文和可选 Unix 秒时间戳。未知时间省略，保留适配器默认行为。 |
| `group_disband` | 独立通知监听器记录群号和操作人；戳一戳监听器仅匹配戳一戳事件，让其他通知正常分发。既有历史、workspace 和任务设置保留，由管理员维护。 |

本次协议只新增了接收 Markdown。回复仍使用现有文本/渲染图片投递链路。
`face.is_large` 的版本标注补全不改变消息结构，现有超级表情识别继续适用。
消息归一化版本递增为 3，使引用中的旧原始消息可以按新规则重新归一化。

测试覆盖真实 Milky 事件解析、LangChain 工具 schema 与实际转发结构序列化，
以及 Markdown 门控、文件引用恢复和跨群权限拒绝；网络发送使用替身，正式 Milky 服务需支持对应 API。
