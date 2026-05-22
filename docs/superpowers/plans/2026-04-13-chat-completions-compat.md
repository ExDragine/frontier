# chat.completions 兼容性配置开关 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `BASIC_MODEL` 和 `ADVAN_MODEL` 各自增加独立的 `use_responses_api` 配置开关，使系统可在 Responses API 和 chat.completions API 之间按模型切换。

**Architecture:** 在 `env.toml` 中新增两个布尔字段，通过 `EnvConfig` 读取后注入到 `ChatOpenAI` 实例化参数中。`ADVAN_MODEL` 专属的 `reasoning_effort`/`verbosity` 参数在 `use_responses_api=False` 时自动剔除，不影响响应解析逻辑（`msg.text` 对两种 API 均有效）。

**Tech Stack:** Python, `langchain_openai.ChatOpenAI`, TOML 配置（`tomllib`）, `pydantic.SecretStr`, pytest

---

## 文件变更一览

| 文件 | 操作 | 说明 |
|---|---|---|
| `env.toml.example` | 修改 | `[endpoint]` 新增 2 个字段 |
| `utils/configs.py` | 修改 | `EnvConfig` 新增 2 个字段 |
| `utils/agents.py` | 修改 | `assistant_agent` 和 `chat_agent` 读取新配置 |
| `utils/subagents.py` | 修改 | 模块级 `ChatOpenAI` 读取新配置 |
| `test/utils/agents_test.py` | 修改 | 新增覆盖两种 API 模式的测试 |

---

### Task 1: 配置层 — `env.toml.example` + `EnvConfig`

**Files:**
- Modify: `env.toml.example`
- Modify: `utils/configs.py`
- Test: `test/utils/agents_test.py`

- [ ] **Step 1: 写失败测试 — EnvConfig 新字段存在且默认为 True**

在 `test/utils/agents_test.py` 文件末尾追加：

```python
def test_env_config_responses_api_defaults():
    from utils.configs import EnvConfig
    assert EnvConfig.BASIC_MODEL_USE_RESPONSES_API is True
    assert EnvConfig.ADVAN_MODEL_USE_RESPONSES_API is True
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_env_config_responses_api_defaults -v
```

预期输出：`FAILED` — `AttributeError: type object 'EnvConfig' has no attribute 'BASIC_MODEL_USE_RESPONSES_API'`

- [ ] **Step 3: 修改 `utils/configs.py`，新增两个字段**

在 `EnvConfig` 类中，紧接 `PAINT_MODEL` 行之后添加：

```python
    BASIC_MODEL_USE_RESPONSES_API: bool = endpoint.get("basic_model_use_responses_api", True)
    ADVAN_MODEL_USE_RESPONSES_API: bool = endpoint.get("advan_model_use_responses_api", True)
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_env_config_responses_api_defaults -v
```

预期输出：`PASSED`

- [ ] **Step 5: 修改 `env.toml.example`，在 `[endpoint]` 块中新增两行**

在 `paint_model = ""` 行下方加入：

```toml
basic_model_use_responses_api = true
advan_model_use_responses_api = true
```

- [ ] **Step 6: Commit**

```bash
cd /home/exdragine/frontier && git add utils/configs.py env.toml.example test/utils/agents_test.py
git commit -m "feat: add per-model use_responses_api config fields"
```

---

### Task 2: `utils/subagents.py` — 子代理模型读取新配置

**Files:**
- Modify: `utils/subagents.py`
- Test: `test/utils/agents_test.py`

- [ ] **Step 1: 写失败测试 — subagents 模块的 model 携带正确的 use_responses_api**

在 `test/utils/agents_test.py` 末尾追加：

```python
def test_subagents_model_respects_config(monkeypatch):
    import importlib
    import utils.subagents as subagents_module
    from utils.configs import EnvConfig

    created_kwargs = {}

    class CapturingModel:
        def __init__(self, **kwargs):
            created_kwargs.update(kwargs)

    monkeypatch.setattr(subagents_module, "ChatOpenAI", CapturingModel)
    monkeypatch.setattr(EnvConfig, "BASIC_MODEL_USE_RESPONSES_API", False)

    importlib.reload(subagents_module)

    assert created_kwargs.get("use_responses_api") is False
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_subagents_model_respects_config -v
```

预期输出：`FAILED` — `AssertionError: assert True is False`（当前硬编码为 `True`）

- [ ] **Step 3: 修改 `utils/subagents.py`，将模块级 `ChatOpenAI` 的 `use_responses_api` 改为读取配置**

将现有：

```python
model = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    model=BASIC_MODEL,
    max_retries=2,
    timeout=30,
    use_responses_api=True,
)
```

改为：

```python
model = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    model=BASIC_MODEL,
    max_retries=2,
    timeout=30,
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
)
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_subagents_model_respects_config -v
```

预期输出：`PASSED`

- [ ] **Step 5: Commit**

```bash
cd /home/exdragine/frontier && git add utils/subagents.py test/utils/agents_test.py
git commit -m "feat: subagents model reads BASIC_MODEL_USE_RESPONSES_API from config"
```

---

### Task 3: `utils/agents.py` — `assistant_agent` 读取新配置

**Files:**
- Modify: `utils/agents.py`
- Test: `test/utils/agents_test.py`

- [ ] **Step 1: 写失败测试 — assistant_agent 在 use_responses_api=False 时传入 False**

在 `test/utils/agents_test.py` 末尾追加：

```python
@pytest.mark.asyncio
async def test_assistant_agent_uses_basic_model_config(monkeypatch):
    import builtins
    import types
    from utils import agents
    from utils.configs import EnvConfig

    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("system_prompt.md"):
            raise FileNotFoundError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    class DummyAgent:
        async def ainvoke(self, payload):
            return {"messages": [types.SimpleNamespace(type="ai", content="ok", text="ok")]}

    def fake_create_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_agent", fake_create_agent)

    captured = {}

    class CapturingModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(agents, "ChatOpenAI", CapturingModel)
    monkeypatch.setattr(EnvConfig, "BASIC_MODEL_USE_RESPONSES_API", False)

    await agents.assistant_agent(user_prompt="hello")

    assert captured.get("use_responses_api") is False
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_assistant_agent_uses_basic_model_config -v
```

预期输出：`FAILED` — `AssertionError: assert True is False`

- [ ] **Step 3: 修改 `utils/agents.py` — `assistant_agent` 中将 `use_responses_api=True` 替换为配置读取**

将 `assistant_agent` 内的 `ChatOpenAI(...)` 调用：

```python
    model = ChatOpenAI(
        api_key=EnvConfig.OPENAI_API_KEY,
        base_url=EnvConfig.OPENAI_BASE_URL,
        model=use_model,
        streaming=False,
        max_retries=2,
        timeout=300,
        use_responses_api=True,
    )
```

改为：

```python
    model = ChatOpenAI(
        api_key=EnvConfig.OPENAI_API_KEY,
        base_url=EnvConfig.OPENAI_BASE_URL,
        model=use_model,
        streaming=False,
        max_retries=2,
        timeout=300,
        use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
    )
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_assistant_agent_uses_basic_model_config -v
```

预期输出：`PASSED`

- [ ] **Step 5: Commit**

```bash
cd /home/exdragine/frontier && git add utils/agents.py test/utils/agents_test.py
git commit -m "feat: assistant_agent reads BASIC_MODEL_USE_RESPONSES_API from config"
```

---

### Task 4: `utils/agents.py` — `chat_agent` 读取新配置并剔除不兼容参数

**Files:**
- Modify: `utils/agents.py`
- Test: `test/utils/agents_test.py`

- [ ] **Step 1: 写失败测试 — chat_agent 在 use_responses_api=False 时不传 reasoning_effort/verbosity**

在 `test/utils/agents_test.py` 末尾追加：

```python
@pytest.mark.asyncio
async def test_chat_agent_drops_reasoning_params_when_chat_completions(monkeypatch):
    import types
    import uuid
    from utils import agents
    from utils.configs import EnvConfig

    class DummyAgent:
        async def ainvoke(self, payload, config=None):
            return {
                "messages": [
                    types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)
                ]
            }

    def fake_create_deep_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)

    captured = {}

    class CapturingModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(agents, "ChatOpenAI", CapturingModel)
    monkeypatch.setattr(EnvConfig, "ADVAN_MODEL_USE_RESPONSES_API", False)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.subagents = []
    frontier.checkpoint = None
    frontier.backend = None
    frontier.memory = None

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
    )

    assert captured.get("use_responses_api") is False
    assert "reasoning_effort" not in captured
    assert "verbosity" not in captured


@pytest.mark.asyncio
async def test_chat_agent_includes_reasoning_params_when_responses_api(monkeypatch):
    import types
    from utils import agents
    from utils.configs import EnvConfig

    class DummyAgent:
        async def ainvoke(self, payload, config=None):
            return {
                "messages": [
                    types.SimpleNamespace(type="ai", content="ok", text="ok", artifact=None)
                ]
            }

    def fake_create_deep_agent(**_kwargs):
        return DummyAgent()

    monkeypatch.setattr(agents, "create_deep_agent", fake_create_deep_agent)

    captured = {}

    class CapturingModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(agents, "ChatOpenAI", CapturingModel)
    monkeypatch.setattr(EnvConfig, "ADVAN_MODEL_USE_RESPONSES_API", True)

    frontier = agents.FrontierCognitive.__new__(agents.FrontierCognitive)
    frontier.tools = []
    frontier.subagents = []
    frontier.checkpoint = None
    frontier.backend = None
    frontier.memory = None

    await frontier.chat_agent(
        messages=[{"role": "user", "content": "hi"}],
        user_id="u1",
        user_name="test",
        capability="medium",
    )

    assert captured.get("use_responses_api") is True
    assert captured.get("reasoning_effort") == "medium"
    assert captured.get("verbosity") == "low"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_chat_agent_drops_reasoning_params_when_chat_completions test/utils/agents_test.py::test_chat_agent_includes_reasoning_params_when_responses_api -v
```

预期输出：两个测试均 `FAILED`

- [ ] **Step 3: 修改 `utils/agents.py` — `chat_agent` 中改为 kwargs 展开**

将 `chat_agent` 内现有的 `ChatOpenAI(...)` 调用块：

```python
        model = ChatOpenAI(
            api_key=EnvConfig.OPENAI_API_KEY,
            base_url=EnvConfig.OPENAI_BASE_URL,
            model=EnvConfig.ADVAN_MODEL,
            streaming=False,
            reasoning_effort=capability,
            verbosity="low",
            max_retries=2,
            timeout=300,
            use_responses_api=True,
        )
```

替换为：

```python
        model_kwargs: dict = {
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

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/utils/agents_test.py::test_chat_agent_drops_reasoning_params_when_chat_completions test/utils/agents_test.py::test_chat_agent_includes_reasoning_params_when_responses_api -v
```

预期输出：两个测试均 `PASSED`

- [ ] **Step 5: Commit**

```bash
cd /home/exdragine/frontier && git add utils/agents.py test/utils/agents_test.py
git commit -m "feat: chat_agent reads ADVAN_MODEL_USE_RESPONSES_API, drops reasoning params when disabled"
```

---

### Task 5: 全量回归

**Files:**
- Test: `test/utils/agents_test.py`（及全套）

- [ ] **Step 1: 运行全部测试套件**

```bash
cd /home/exdragine/frontier && .venv/bin/pytest test/ -v
```

预期输出：所有原有测试 + 本次新增测试全部 `PASSED`，无 `ERROR`

- [ ] **Step 2: 若有失败，根据错误信息修复后重跑，直到全绿**

- [ ] **Step 3: Commit（如有修复）**

```bash
cd /home/exdragine/frontier && git add -p
git commit -m "fix: address regression from chat completions compat changes"
```
