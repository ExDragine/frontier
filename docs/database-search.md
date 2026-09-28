# SQLite 消息搜索维护

Frontier 的聊天原文以 `message` 为唯一事实来源，`message_fts` 使用 SQLite FTS5
external-content 模式建立全文索引。FTS 表不重复保存正文，增删改由三个触发器同步。

## 搜索接口

- `MessageDatabase.search_messages()` 保持兼容，返回 `Message` 列表。
- `MessageDatabase.search_message_details()` 返回消息、BM25 分数和 `snippet()` 摘要，
  适合 Dashboard 或记忆检索层展示相关度。
- `MessageDatabase.select_message_timeline()` 以命中消息为锚点，按同一群聊或私聊范围
  读取时间窗口内的上下文。

FTS5 不可用、查询过短或索引查询失败时，会降级到带作用域过滤的 LIKE 查询。

## 一致性与维护

启动时会检查 FTS 表结构并记录 `frontier_fts_metadata` 中的 schema 版本。检测到结构
变化时会在事务内重建索引。运行时可以通过维护脚本检查或修复索引：

```bash
uv run python scripts/database_maintenance.py diagnose
uv run python scripts/database_maintenance.py maintain --checkpoint
```

`diagnose` 会报告 FTS 表是否存在、schema 版本、完整性检查结果和数据库大小。
`maintain` 执行 `PRAGMA optimize`、FTS5 `optimize`，发现不一致时自动重建，最后可选执行
被动 WAL checkpoint。

`PRAGMA optimize` 和 FTS5 合并操作应批量、定期执行，不要放到每条消息写入路径中。
