# 消息身份与历史迁移退役

旧数据库已完成升级，当前版本移除了消息 ID 迁移、历史补列与关系回填、附件去重和媒体格式修补、裸 ID 会话目录搬迁，以及旧提醒任务导入代码。

## 当前数据库要求

- `Message.id` 是独立主键，`time` 仅表示毫秒时间；同一毫秒可以保存多条消息。
- 附件通过 `message_id`、转发节点通过 `parent_message_id` 关联消息；FTS 使用消息 ID。
- 平台事件去重键由机器人账号、群/私聊类型、会话 ID 和 Milky 消息序号组成。
- `MessageDatabase.insert()` 返回 `MessageInsertResult(message_id, time, inserted)`。更新消息、绑定附件和替换转发节点时使用消息 ID。
- 历史时间筛选保持不变，排序使用 `(time, id)`。仅传时间而不能唯一定位消息时抛出 `ValueError`。

启动会检查已有消息、附件和任务表的必要列与主键。结构不兼容时明确报错，不再自动改表或回填数据。新数据库仍会正常建表，并维护查询索引和 FTS。已存在的 `frontier_schema_version` 标记保持原样，不再读取或更新。

当前会话目录使用 `group-{id}` / `dm-{id}` 前缀。启动不再移动裸 ID 目录或修补历史附件；正常附件写入与过期清理继续运行。

## 恢复旧备份

需要恢复尚未升级的历史备份时，应先使用包含迁移工具的历史版本（例如提交 `c469c2f`）在备份副本上完成升级，核对消息、附件与搜索结果，再交给当前版本使用。不要直接用当前版本启动旧结构数据库。

## 验证

测试使用临时合成数据库，覆盖旧结构无修改拒绝、当前库重启保留数据和旧目录、并发平台去重，以及相同时间消息的媒体、FTS 和转发隔离。

```bash
uv run --locked pytest test/utils/message_identity_test.py test/utils/database_test.py test/utils/database_performance_test.py test/plugins/clockwork_test.py -q
```
