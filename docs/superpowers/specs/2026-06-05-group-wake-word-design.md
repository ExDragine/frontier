# 群组多唤醒词 — 设计文档

## 概述

允许每个群聊自定义多个唤醒词，群管理员通过 `/set wake` 命令管理。数据库中有自定义唤醒词时优先使用，否则 fallback 到 `env.toml` 中的 `BOT_NAME`。

## 命令接口

| 命令 | 权限 | 效果 |
|------|------|------|
| `/set wake add <词>` | 群主/管理员 | 添加一个唤醒词 |
| `/set wake remove <词>` | 群主/管理员 | 移除一个唤醒词 |
| `/set wake` | 所有人 | 查看当前唤醒词列表 |
| `/set wake clear` | 群主/管理员 | 清空所有自定义唤醒词 |

### 参数解析

`/set` 是主命令，子命令路由：`wake` → handler，再根据 `add/remove/clear` 动作分发。

### 响应示例

```
/set wake add 小天
→ ✅ 唤醒词 "小天" 已添加。当前唤醒词：小天

/set wake add 小助手
→ ✅ 唤醒词 "小助手" 已添加。当前唤醒词：小天, 小助手

/set wake
→ 当前群唤醒词：小天, 小助手

/set wake remove 小天
→ ✅ 唤醒词 "小天" 已移除。当前唤醒词：小助手

/set wake clear
→ ✅ 已清空所有唤醒词。将使用默认唤醒词 "小李子"。

/set wake add 小天
（已被占用，去重）
→ ⚠️ 唤醒词 "小天" 已存在。当前唤醒词：小天
```

### 边界处理

- 空白唤醒词拒绝
- 同群重复唤醒词静默跳过（不报错，返回已有列表）
- 移除不存在的唤醒词：提示不存在
- 清空时无数据：静默返回
- 非群聊场景（私聊）：提示"此命令仅支持群聊"

## 数据库

### 表结构

```sql
CREATE TABLE group_settings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id    INTEGER NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    updated_at  INTEGER NOT NULL
);

CREATE INDEX ix_group_settings_group_key ON group_settings (group_id, key);
```

- `(group_id, key)` 复合索引，查唤醒词时扫一条 key 即可
- key-value 行式存储，便于后续扩展 `/set model`、`/set cooldown` 等其他群设置
- 同 key 允许多行，天然支持多唤醒词

### Python Model

```python
class GroupSettings(SQLModel, table=True):
    __tablename__ = "group_settings"
    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    key: str = Field(index=True)
    value: str
    updated_at: int
```

### Manager 方法

- `get(group_id, key) -> list[str]` — 获取某 key 的所有 values
- `set(group_id, key, value) -> None` — 插入一行
- `remove(group_id, key, value) -> bool` — 删除一行，返回是否删到
- `clear(group_id, key) -> int` — 删除某 key 下所有行，返回删除数

## 触发链路

### `_get_wake_words(group_id) -> list[str]`

```python
def _get_wake_words(group_id: int) -> list[str]:
    words = group_settings_db.get(group_id, "wake_word")
    return words if words else [EnvConfig.BOT_NAME]
```

### `message_gateway()` 改动

```python
# 原来 (utils/message.py:701)
if plaintext.startswith(EnvConfig.BOT_NAME):
    return True

# 改为
wake_words = _get_wake_words(group_id)
if any(plaintext.startswith(w) for w in wake_words):
    return True
```

### 触发语义

- 纯前缀匹配：`plaintext.startswith(wake_word)`
- 支持连写：`"小天今天天气怎么样"` → ✅ 触发
- 管理员要注意避免过短的唤醒词（如单字），靠自觉

## 改动文件

| 文件 | 改动 |
|------|------|
| `utils/database.py` | 新增 `GroupSettings` model + `GroupSettingsManager` 类 |
| `plugins/toolbox/__init__.py` | 新增 `/set` 命令 + `handle_set` handler，解析 `wake add/remove/clear` |
| `utils/message.py` | `message_gateway()` 调用 `_get_wake_words()` 替代 `EnvConfig.BOT_NAME` |

## 测试要点

- 添加/移除/查看/清空唤醒词
- 空库 fallback 到 `BOT_NAME`
- 同群重复添加去重
- 移除不存在的唤醒词
- 非管理员被拒绝
- 私聊场景被拒绝
- `message_gateway` 中多唤醒词前缀匹配
- 清空后恢复 fallback 行为

## 后续扩展

此设计预留了 key-value 模式，后续可以复用同一张表扩展：
- `/set model <name>` — 群级别模型选择
- `/set cooldown <seconds>` — 群级别冷却时间
- `/set auto_reply on/off` — 群级别智能回复开关
