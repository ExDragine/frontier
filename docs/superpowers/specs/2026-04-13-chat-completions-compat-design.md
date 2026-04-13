# chat.completions 兼容性配置开关设计

**日期：** 2026-04-13
**状态：** 已审批

## 背景

项目于 2026-03-18（commit `3a4897f`）迁移至 OpenAI Responses API（`use_responses_api=True`），统一使用 `ChatOpenAI`，移除了对 Gemini / Claude / chat.completions 的分路逻辑。

部分后端提供商（如自托管端点、OpenRouter 部分模型）不支持 Responses API（`/v1/responses`），需要退回到标准 chat.completions 端点（`/v1/chat/completions`）。

## 目标

在不破坏现有行为的前提下，通过配置开关让 `BASIC_MODEL` 和 `ADVAN_MODEL` 各自独立选择使用 Responses API 或 chat.completions API。

## 设计决策

### 不采用的方案

- **方案 C（运行时动态传参）**：调用方不需要这种灵活性，会增加接口复杂度。
- **自动按模型名判断**：模型名与 API 能力无固定映射关系，维护成本高。

### 采用方案：分模型配置开关

## 配置

### `env.toml.example` — `[endpoint]` 块新增

```toml
basic_model_use_responses_api = true
advan_model_use_responses_api = true
```

默认均为 `true`，不修改配置的用户行为不变。

### `utils/configs.py` — `EnvConfig` 新增

```python
BASIC_MODEL_USE_RESPONSES_API: bool = endpoint.get("basic_model_use_responses_api", True)
ADVAN_MODEL_USE_RESPONSES_API: bool = endpoint.get("advan_model_use_responses_api", True)
```

## 代码变更

### `utils/agents.py`

**`assistant_agent()`**：将硬编码的 `use_responses_api=True` 改为读取配置：

```python
model = ChatOpenAI(
    ...
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
)
```

**`FrontierCognitive.chat_agent()`**：`reasoning_effort` / `verbosity` 为 Responses API 专属参数，切换为 chat.completions 时自动剔除：

```python
model_kwargs = {
    "api_key": EnvConfig.OPENAI_API_KEY,
    "base_url": EnvConfig.OPENAI_BASE_URL,
    "model": EnvConfig.ADVAN_MODEL,
    "streaming": False,
    "max_retries": 2,
    "timeout": 300,
    "use_responses_api": EnvConfig.ADVAN_MODEL_USE_RESPONSES_API,
}
if EnvConfig.ADVAN_MODEL_USE_RESPONSES_API:
    model_kwargs["reasoning_effort"] = capability
    model_kwargs["verbosity"] = "low"
model = ChatOpenAI(**model_kwargs)
```

### `utils/subagents.py`

子代理使用 `BASIC_MODEL`，同步读取 `BASIC_MODEL_USE_RESPONSES_API`：

```python
model = ChatOpenAI(
    ...
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
)
```

## 响应格式兼容性

`AIMessage.text` 属性对两种 API 的返回格式均可正确提取文本：

- chat.completions：`content = "hello"` → `.text = "hello"`
- Responses API：`content = [{"type": "text", "text": "hello"}]` → `.text = "hello"`

**响应解析代码无需修改。**

## 影响范围

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `env.toml.example` | 新增 | 2 行配置字段 |
| `utils/configs.py` | 新增 | 2 个 EnvConfig 字段 |
| `utils/agents.py` | 修改 | `assistant_agent` 1 行；`chat_agent` 改为 kwargs 展开（~6 行） |
| `utils/subagents.py` | 修改 | 1 行 |
| 测试文件 | 无需修改 | `DummyModel` 忽略所有 kwargs |
