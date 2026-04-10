# Content Check Toggle — Design Spec

**Date:** 2026-04-10  
**Status:** Approved

## 背景

`utils/message.py` 在模块导入时无条件实例化两个大模型：

- `TextCheck` → `Qwen3Guard-Gen-0.6B`（文本安全分类）
- `ImageCheck` → `Falconsai/nsfw_image_detection`（NSFW 图像检测）

这导致即使功能未使用，模型也会在启动时占用内存并延长启动时间。`plugins/fireside/__init__.py` 的 `handle_common` 在每条消息中都无条件调用 `message_check()`。

## 目标

- 默认禁用内容检测，不加载模型
- 通过 `env.toml` 的 `[content_check]` 段显式启用
- 禁用时仍发送默认表情回复（🔮）以确认 bot 状态
- 风格与现有 `MEMORY_ENABLED`、`IMAGE_ENABLED` 配置项保持一致

## 变更范围

### 1. `env.toml`

新增配置段（默认禁用）：

```toml
[content_check]
enabled = false
```

### 2. `utils/configs.py`

新增顶层字典读取和 `EnvConfig` 字段：

```python
content_check: dict = config.get("content_check", {})

class EnvConfig:
    # ...
    CONTENT_CHECK_ENABLED: bool = content_check.get("enabled", False)
```

### 3. `utils/message.py`

将模块级无条件实例化改为条件实例化：

```python
text_det = TextCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
image_det = ImageCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
```

在 `message_check()` 函数开头添加早期返回：

```python
async def message_check(...):
    if not EnvConfig.CONTENT_CHECK_ENABLED:
        return "Safe"
    # 原有逻辑不变
```

### 4. `plugins/fireside/__init__.py`

在 `handle_common` 中，将无条件调用改为按开关赋值，表情回复逻辑不变：

```python
# 之前
risk_check = await message_check(text, images)

# 之后
if EnvConfig.CONTENT_CHECK_ENABLED:
    risk_check = await message_check(text, images)
else:
    risk_check = "Safe"  # 禁用时默认安全，仍触发 🔮 表情回复

match risk_check:
    case "Safe": ...      # 发送 🔮（原有逻辑不变）
    case "Controversial": ...
    case "Unsafe": ...
```

## 行为对比

| 场景 | 启用前（当前） | 禁用（新默认） | 启用（显式配置） |
|------|--------------|--------------|----------------|
| 启动时模型加载 | 是 | 否 | 是 |
| 每条消息推理 | 是 | 否 | 是 |
| 表情回复 | 按检测结果 | 固定 🔮 | 按检测结果 |
| 内存占用 | 高 | 低 | 高 |

## 不变更的内容

- `IMAGE_ENABLED` 及其控制的绘画模块逻辑
- 表情回复的 match-case 结构
- `message_check()` 检测逻辑本身
