# Frontier 运行与维护边界

## 请求生命周期

QQ、用户定时任务和内置 Agent 的 ACP 服务使用
`FrontierAgentRuntime.run(AgentRuntimeRequest)`。ACP `prompt()` 是这一入口的协议转换层。
`FrontierCognitive.chat_agent()` 保留为兼容入口，执行同样的生命周期管理。

1. 入口构造请求、可信用户/群身份及投递目标。
2. `utils/agents/chat_context.py` 分配当前消息、引用和历史的媒体预算。
3. `utils/agents/execution.py` 从构建模型开始管理整轮执行，应用总超时和 workspace 锁。
4. `cognitive.py` 组合模型、工具、middleware 和 subagent，消费进度流并提取结果。
5. 入口使用 `utils/delivery.py` 的投递结果决定是否记录已发送回复。

同一个群共享工作区，因此不同成员的内置 Agent 执行也共享 `workspace:` 锁。
QQ 入口另有 `delivery:` 队列保证生成、发送和落库顺序；锁顺序只能是 delivery → workspace。
不同群和不同私聊可以并发。锁条目在最后一个使用者退出后释放，避免长期增长。

## 结果和错误

`AgentResult` 保留兼容的 `response`、`uni_messages`、`should_reply` 和 `total_time` 字段，
包含 `status`、`run_id`、`usage`，失败时附加 `error` / `error_code`。调用预算、统计范围与工具异常规则见 [Agent 执行控制](agent-execution-controls.md)。

- `success`：生成完成；是否送达另由投递结果确定。
- `silent`：主动选择不回复。
- `failed`：初始化、调用或输出整理失败。
- `timeout`：模型调用超时或超过整轮时间预算。
- 外部取消传播 `CancelledError`，不转换成成功回复；任务执行器记录 `cancelled`。

每轮 UUID 同时进入日志和模型运行 metadata。用户只收到分类后的提示，供应商原始异常留在日志。
重试限于模型调用和显式只读工具；不能重跑整个 Agent 图，避免重复平台写操作。
主模型 SDK 重试关闭，由 ModelRetryMiddleware 统一控制，防止叠加重试。
失败后的进度通知最多再等待 1 秒；外部取消直接传播，不等待进度发送。

`agent_job_timeout_seconds` 约束整轮内置 Agent。用户自动任务执行器还覆盖结果投递阶段。
它不改变内置商人轮询等有独立时段规则的长期任务。

## 初始化和配置

导入 MCP 加载模块不会读取 mcp.json 或连接服务器。首轮在当前事件循环内异步发现工具，
各服务独立超时；单服务故障不使全部工具失效。同步加载入口仅供尚未启动事件循环的兼容调用者。

FrontierCognitive 构造函数不再构建模型或子代理。首次执行才初始化；EnvConfig 成功 reload 后
递增 REVISION，使下次执行重建依赖模型配置的组件。
异步捕获意图判断和工具发现发生在建图之前；此后模型、能力筛选和 middleware
在同一事件循环中连续构建，避免 Dashboard 重载将一张图拼成两个配置版本。
已构建的模型不会在运行中替换；工具在后续调用时读取的配置可以更新。
现存 EnvConfig import 读取行为保留为旧模块的兼容桥；新组件应从运行入口初始化资源，
不可添加模块级网络访问或客户端连接。

## 持久化

QQ 可选会话缓存由进程级 `SessionManager` 和 `BoundedMemorySaver` 管理，默认关闭。身份为机器人＋群／私聊＋代次；图每轮重新构建，saver 跨轮复用，权限和动态工具每轮重新绑定。`TurnLease` 通过运行请求传入并保留到投递结算。TTL、轮数、会话数和序列化容量共同限制存储；历史 token 预算单独由 middleware 控制。过期／轮换后下一次从原历史边界重建，不恢复旧任务。配置、指标、媒体与失败规则见 [QQ 会话缓存](agent-sessions.md)。

v3 图流在退出时显式 abort；QuickJS 使用请求级生命周期适配，取消／失败时仍通过公开 after_agent hook 清理解释器资源。活动会话的 checkpoint 必须等执行结束后才能删除。

消息身份、时间和平台去重键是不同概念。查询可以按时间排序，但附件、转发关联和 FTS
必须使用独立消息 ID，不能再把毫秒时间戳当作唯一标识。
历史迁移已退役；当前结构要求与旧备份恢复说明见 [数据库说明](database-identity-migration.md)。启动只检查已有表结构、初始化新表并维护索引/FTS。

## 验证与依赖

提交前执行：

```bash
uv sync --locked --group dev
uv run --locked ruff check .
uv run --locked pytest test/ -q
```

CI 还对运行边界执行 ty 检查。真实依赖契约测试使用独立 Python 进程，覆盖真实
LangChain / Deep Agents 工具调用与 MCP stdio，避免全局替身掩盖升级兼容性问题。
一般单元测试在应用边界注入替身，动态导入和 monkeypatch 必须在测试结束后恢复。

依赖升级单独提交 pyproject.toml / uv.lock，并运行同一套契约测试；不要把自动升级放进机器人重启循环。
旧 API 在调用者完成迁移、测试覆盖真实行为后再删除，不能只为了缩短文件而移除兼容代码。
