# Wonderland 绘画模块独立配置设计

**日期：** 2026-04-23
**状态：** 已审批

## 背景

当前 `plugins/wonderland/__init__.py` 的绘画请求直接复用全局 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY`。这会把文本模型路由和绘画路由强耦合在一起：

- 文本模型可能走 OpenRouter 或其他 OpenAI 兼容网关
- 绘画模型可能走 OpenAI 官方 Images API
- 绘画模型也可能走 `vertex-ai` 风格的中转（如 ZenMux）

当两类流量需要不同的 URL 或 Key 时，单一全局配置会导致绘画调用打到错误的服务上。

## 目标

- 为绘画模块单独提供 URL 和 API Key 配置
- 在未填写绘画专用配置时，自动回退到现有全局 OpenAI 配置
- 不改动现有命令入口和绘画模型字段 `paint_model`
- 保持 dashboard 设置页可直接编辑新字段
- 热重载后立即生效，无需重启

## 不采用的方案

- 新增独立 `[paint]` 配置段
  优点是语义最完整，但会扩大改动面，现阶段不需要整体重构配置结构。

- 强制要求必须填写 `paint_base_url` 和 `paint_api_key`
  这会破坏当前已有配置，且对只使用单一 Provider 的用户没有价值。

## 采用方案

在现有 `[endpoint]` 和 `[key]` 中分别新增绘画专用字段：

```toml
[endpoint]
openai_base_url = ""
basic_model = ""
advan_model = ""
paint_model = ""
paint_base_url = ""

[key]
openai_api_key = ""
paint_api_key = ""
```

运行规则：

- `wonderland` 优先使用 `paint_base_url` / `paint_api_key`
- 当其中任一字段为空字符串或不存在时，回退到 `openai_base_url` / `openai_api_key`
- `vertex-ai` 网关检测基于“绘画实际使用的 URL”，不再基于全局 `OPENAI_BASE_URL`

## 受影响文件

| 文件 | 变更类型 | 说明 |
|---|---|---|
| `env.toml.example` | 修改 | 新增 `paint_base_url`、`paint_api_key` 示例字段 |
| `utils/configs.py` | 修改 | 新增 `PAINT_BASE_URL`、`PAINT_API_KEY`，并实现回退逻辑 |
| `plugins/wonderland/__init__.py` | 修改 | 绘画调用改为只读取绘画专用配置 |
| `plugins/dashboard/api/settings_routes.py` | 修改 | 热重载时同步更新绘画专用配置 |
| `test/utils/configs_test.py` | 修改 | 覆盖默认回退与显式覆盖行为 |
| `test/plugins/wonderland_test.py` | 修改 | 验证绘画优先使用专用 URL / Key |

`plugins/dashboard/web/pages/Settings.js` 无需改动。该页面按 section 中的字段动态渲染，新字段会自动显示。

## 配置设计

### `utils/configs.py`

新增两个运行时字段：

```python
PAINT_BASE_URL: str = endpoint.get("paint_base_url") or OPENAI_BASE_URL
PAINT_API_KEY: SecretStr = SecretStr(key.get("paint_api_key") or key["openai_api_key"])
```

这里明确将空字符串视为“未配置”，而不是有效值。原因是 dashboard 和手工编辑配置时，最常见的“使用默认值”表达方式就是留空。

### `plugins/dashboard/api/settings_routes.py`

热重载逻辑同步改为：

```python
EnvConfig.OPENAI_BASE_URL = ep.get("openai_base_url", EnvConfig.OPENAI_BASE_URL)
EnvConfig.PAINT_BASE_URL = ep.get("paint_base_url") or EnvConfig.OPENAI_BASE_URL

EnvConfig.OPENAI_API_KEY = SecretStr(key.get("openai_api_key", ""))
EnvConfig.PAINT_API_KEY = SecretStr(key.get("paint_api_key") or key.get("openai_api_key", ""))
```

要求：

- 即使只更新了全局 OpenAI 配置，也要重新计算绘画回退值
- 即使 `paint_base_url` / `paint_api_key` 在配置文件中存在但为空，也必须回退

## Wonderland 运行逻辑

### 配置读取

`plugins/wonderland/__init__.py` 中所有与网络路由相关的逻辑统一改为读取：

- `EnvConfig.PAINT_BASE_URL`
- `EnvConfig.PAINT_API_KEY`
- `EnvConfig.PAINT_MODEL`

文本模型相关配置仍继续读取全局 `OPENAI_BASE_URL` / `OPENAI_API_KEY`，不受影响。

### Provider 判定

当前实现中 `_use_vertex_image_gateway()` 基于 `EnvConfig.OPENAI_BASE_URL.lower()` 判断。改造后应改为：

```python
def _paint_base_url() -> str:
    return EnvConfig.PAINT_BASE_URL

def _use_vertex_image_gateway() -> bool:
    return "vertex-ai" in _paint_base_url().lower()
```

### OpenAI 原生路径

OpenAI Images API 客户端参数改为：

```python
AsyncClient(
    api_key=EnvConfig.PAINT_API_KEY.get_secret_value(),
    base_url=EnvConfig.PAINT_BASE_URL,
)
```

### Vertex 风格路径

`google.genai.Client(...)` 参数改为：

```python
genai.Client(
    api_key=EnvConfig.PAINT_API_KEY.get_secret_value(),
    vertexai=True,
    http_options=genai_types.HttpOptions(
        api_version="v1",
        base_url=EnvConfig.PAINT_BASE_URL,
    ),
)
```

## 错误处理

- 若绘画专用字段为空，则自动回退，不视为错误
- 若回退后的 URL 或 Key 仍为空，则由下游 SDK 在请求时抛出认证或连接错误
- `wonderland` 的用户侧行为保持不变：日志记录异常，聊天中返回“这里空空如也，什么都没有画出来。”

## 测试策略

### 配置测试

在 `test/utils/configs_test.py` 中新增断言：

- 未设置 `paint_base_url` / `paint_api_key` 时，`EnvConfig` 回退到全局配置
- 显式设置时，优先使用绘画专用配置

### Wonderland 测试

在 `test/plugins/wonderland_test.py` 中新增或调整断言：

- OpenAI Images 路径下，`AsyncClient` 使用绘画专用 URL / Key
- Vertex 风格路径下，`genai.Client` 使用绘画专用 URL / Key
- `vertex-ai` 判定基于绘画专用 URL，而不是全局 URL

## 范围边界

本次只处理绘画模块与配置系统的解耦，不包含：

- dashboard 总览页展示绘画专用 URL / Key
- 其他工具模块拆分专用 Provider 配置
- 将 `paint_model` 从 `[endpoint]` 迁移到新 section
