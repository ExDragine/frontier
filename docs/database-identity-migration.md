# 消息身份迁移

本次改动将消息的数据库身份与时间拆开。`Message.id` 是独立、自动增长的主键，`Message.time` 继续表示毫秒时间。同一毫秒的群聊、私聊和机器人回复可以同时保存。新媒体文件名包含数据库消息 ID，避免同一会话同一毫秒的图片覆盖。

## 兼容关系

- 原有消息迁移后 `id = 原 time`，原 `time`、正文、规范化内容、引用 JSON 及扩展字段原样保留。旧版转发节点的负时间也保留；新转发节点使用节点时间，缺失时使用父消息时间。
- 附件新增 `message_id`，转发节点新增 `parent_message_id`；迁移在原时间和会话范围相符时补齐关系。原附件路径不因身份迁移而改名。
- FTS 的 `content_rowid` 和触发器改用 `id`，并在同一事务内重建索引。旧版索引同步失败时整笔身份迁移回滚。
- `msg_id` 仍为 Milky 的消息序号。正常消息的去重键由机器人账号、群/私聊类型、会话 ID、消息序号组成。没有平台序号的消息不去重。
- 已有重复平台记录保留，仅最新一条占用去重键；重复事件返回该条记录的 ID 和原时间。缺失机器人账号的历史记录使用 `0` 命名空间，不能与已知账号记录可靠合并。

## 调用契约

`MessageDatabase.insert()` 返回 `MessageInsertResult(message_id, time, inserted)`。入口使用 `inserted` 判断是否为新事件；需要修改消息或绑定附件时传入 `message_id`。转发替换使用 `parent_message_id`。

历史筛选的 `before_time`、`start_time`、`end_time` 仍然是时间，排序以 `(time, id)` 处理同时间消息。只传时间的旧查询/更新接口在无法唯一确定正常消息时抛出 `ValueError`，避免误更新其他消息。尚未绑定消息的旧附件兼容按时间、发送者、会话和平台序号匹配；新增生产路径明确传消息 ID。

## 迁移与恢复

`utils/storage_migrations.py` 只接收调用方传入的 SQLAlchemy engine，不自行打开应用数据库。`MessageDatabase` 初始化时会在补齐历史可选列后运行身份迁移。

迁移使用 `BEGIN IMMEDIATE`，在同一 SQLite 事务内完成消息表重建、关系补齐、FTS 重建和 `frontier_schema_version` 的 `message_identity = 1` 标记。重复启动不会重复重建；版本高于当前代码时拒绝降级。新表保留旧扩展列、唯一约束、检查约束以及自定义索引和触发器；未知主键布局或自定义表外键引用消息表时会中止迁移，避免表重建触发级联删除。

部署前停止旧版本写入并通过 SQLite backup API 对数据库生成一致性备份，同时保存对应配置和附件目录。先对备份副本运行新版，核对消息/附件数量、引用关系、FTS 查询、`PRAGMA integrity_check`，再切换正式实例。迁移需要重建消息表和 FTS，耗时及临时磁盘需求取决于历史规模。

发生事务内错误时数据库身份变更自动回滚，可以修复原因后重试。迁移前补齐的历史可选列属于向后兼容增量，可能已经存在。身份迁移不搬动附件文件；原有 workspace 目录迁移依然是独立启动步骤。

成功迁移后的数据库不能直接交给旧代码：旧代码把 `time` 当主键。回退应停止新版、恢复迁移前备份并切回对应代码；迁移后新增的数据需另行导出再处理，没有自动降级脚本。

本次验证只使用临时合成数据库，覆盖旧库迁移、重复运行、事务失败恢复、未来版本拒绝、并发事件去重、时间冲突下的媒体/FTS/转发隔离。没有读取或修改真实 `frontier.db`、真实配置或用户附件。

验证命令：

```bash
uv run --locked pytest test/utils/database_test.py test/utils/database_performance_test.py test/utils/reply_context_test.py test/utils/storage_migrations_test.py -q
```
