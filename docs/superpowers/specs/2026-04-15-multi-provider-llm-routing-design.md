# 多 Provider LLM 路由层设计文档

**日期：** 2026-04-15  
**状态：** 待实现

---

## 背景

当前代码在 `utils/agents.py` 和 `utils/subagents.py` 中硬编码使用 `ChatOpenAI`，通过 OpenRouter 作为代理接入 Google 等模型。目标是引入原生多 Provider 支持，使 Google Gemini、OpenAI GPT、Anthropic Claude 各走自己的原生 SDK，不依赖中转服务。

---

## 目标

- 根据模型名称前缀自动路由到对应 Provider
- 各 Provider 参数自动过滤（避免传入不支持的 kwargs 导致报错）
- 新增 Provider 只需注册一条记录，不改核心逻辑
- 向后兼容：调用方代码改动最小

---

## 受影响文件

| 文件 | 变更类型 | 说明 |
|---|---|---|
| `env.toml` | 修改 | 新增 `google_api_key`、`anthropic_api_key`；模型名改为原生格式 |
| `utils/configs.py` | 修改 | 新增 `GOOGLE_API_KEY`、`ANTHROPIC_API_KEY` 字段 |
| `utils/llm_factory.py` | **新建** | Provider 注册表 + `create_llm()` 工厂函数 |
| `utils/agents.py` | 修改 | 替换两处 `ChatOpenAI(...)` 为 `create_llm(...)` |
| `utils/subagents.py` | 修改 | 替换模块级 `model = ChatOpenAI(...)` 为 `create_llm(...)` |

---

## 核心设计：`utils/llm_factory.py`

### ProviderConfig 数据类

```python
@dataclass
class ProviderConfig:
    cls: type                    # LangChain LLM 类
    api_key_fn: Callable         # 从 EnvConfig 获取 API Key 的函数
    valid_kwargs: set[str]       # 该 Provider 支持的构造参数白名单
    needs_base_url: bool = False # 是否传入 OPENAI_BASE_URL
```

### Provider 注册表（PROVIDERS）

| 前缀 | Provider | LLM 类 | 特有 kwargs |
|---|---|---|---|
| `gemini-` | Google | `ChatGoogleGenerativeAI` | — |
| `gpt-` | OpenAI | `ChatOpenAI` | `use_responses_api`, `reasoning_effort`, `verbosity`, `base_url` |
| `o` | OpenAI (o 系列) | `ChatOpenAI` | 同上 |
| `claude-` | Anthropic | `ChatAnthropic` | — |

### 路由逻辑

```python
def create_llm(model: str, **kwargs) -> BaseChatModel:
    for prefix, config in PROVIDERS.items():
        if model.startswith(prefix):
            api_key = config.api_key_fn()
            filtered = {k: v for k, v in kwargs.items() if k in config.valid_kwargs}
            if config.needs_base_url:
                filtered["base_url"] = EnvConfig.OPENAI_BASE_URL
            return config.cls(model=model, api_key=api_key, **filtered)
    raise ValueError(f"未知模型前缀，无法路由: {model}")
```

**前缀匹配顺序：** `PROVIDERS` 为有序字典，较长/更具体的前缀（如 `gemini-`）必须排在较短前缀（如 `g`）之前，避免误匹配。当前注册表中各前缀互不重叠，无歧义。

**参数过滤行为：**
- `use_responses_api`、`reasoning_effort`、`verbosity` 仅在 OpenAI Provider 下生效
- 传入 Google/Anthropic 时自动忽略，不报错

---

## 配置变更

### `env.toml`

```toml
[endpoint]
openai_base_url = "https://api.openai.com/v1"
basic_model = "gemini-2.5-flash"    # 从 "google/gemini-2.5-flash" 改为原生格式
advan_model = "gpt-4o"              # 从 "openai/gpt-5-mini" 改为原生格式
paint_model = "gemini-3-pro"        # 同上

[key]
openai_api_key = "..."
google_api_key = ""      # 新增，填入 Google AI Studio API Key
anthropic_api_key = ""   # 新增，可选
```

### `utils/configs.py`

新增：
```python
GOOGLE_API_KEY: SecretStr = SecretStr(key.get("google_api_key", ""))
ANTHROPIC_API_KEY: SecretStr = SecretStr(key.get("anthropic_api_key", ""))
```

---

## 调用方变化

### `utils/agents.py`（`assistant_agent`）

```python
# 改前
model = ChatOpenAI(
    api_key=EnvConfig.OPENAI_API_KEY,
    base_url=EnvConfig.OPENAI_BASE_URL,
    model=use_model,
    streaming=False,
    max_retries=2,
    timeout=300,
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
)

# 改后
model = create_llm(
    model=use_model,
    streaming=False,
    max_retries=2,
    timeout=300,
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
)
```

### `utils/agents.py`（`chat_agent`）

`model_kwargs` 字典构建逻辑保持不变，最后调用 `create_llm(**model_kwargs)` 而非 `ChatOpenAI(**model_kwargs)`。同时从 `model_kwargs` 中移除 `api_key` 和 `base_url`（由工厂内部处理）。

### `utils/subagents.py`

模块级 `model = ChatOpenAI(...)` → `model = create_llm(model=BASIC_MODEL, max_retries=2, timeout=30)`

---

## 错误处理

- 若模型名前缀不在注册表中，`create_llm()` 抛出 `ValueError`，明确提示未知前缀
- 若对应 API Key 为空字符串，由 LangChain 各 Provider 在实际调用时抛出认证错误（不在工厂层提前校验，避免启动时阻断其他 Provider 的正常使用）

---

## 扩展新 Provider

后续如需增加 Mistral、Cohere 等，只需：
1. 在 `pyproject.toml` 添加 `langchain-mistralai` 等依赖
2. 在 `env.toml [key]` 添加对应 API Key
3. 在 `utils/configs.py` 添加 Key 字段
4. 在 `PROVIDERS` 字典添加一条记录

---

## 测试策略

- 单元测试 `create_llm()` 的前缀匹配逻辑（mock 各 LLM 类构造器）
- 验证 OpenAI 专有 kwargs 在 Google/Anthropic Provider 下被正确过滤
- 验证未知前缀时抛出 `ValueError`
