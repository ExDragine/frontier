# Multi-Provider LLM Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入 `utils/llm_factory.py` Provider 注册表，让模型名前缀自动路由到 Google、OpenAI、Anthropic 原生 SDK，替换现有硬编码的 `ChatOpenAI`。

**Architecture:** 新建 `utils/llm_factory.py`，包含 `ProviderConfig` 数据类和 `PROVIDERS` 列表（按前缀匹配）。`create_llm(model, **kwargs)` 在运行时查表、过滤 kwargs、实例化正确的 LLM 类。调用方(`agents.py`, `subagents.py`) 只需将 `ChatOpenAI(...)` 替换为 `create_llm(...)`。

**Tech Stack:** `langchain-openai`, `langchain-google-genai`, `langchain-anthropic`（均已安装），TOML 配置，pytest + monkeypatch 测试。

---

## File Map

| 文件 | 操作 | 说明 |
|---|---|---|
| `env.toml` | 修改 | 新增 `google_api_key`、`anthropic_api_key`；`basic_model`/`advan_model` 改为原生前缀格式 |
| `utils/configs.py` | 修改 | 新增 `GOOGLE_API_KEY`、`ANTHROPIC_API_KEY` |
| `test/conftest.py` | 修改 | 在 env.toml 模板里加入新 key 字段 |
| `test/utils/configs_test.py` | 修改 | 断言新 key 字段可读 |
| `utils/llm_factory.py` | **新建** | Provider 注册表 + `create_llm()` |
| `test/utils/llm_factory_test.py` | **新建** | 路由逻辑单元测试 |
| `utils/agents.py` | 修改 | 去掉 `ChatOpenAI` 导入，改用 `create_llm` |
| `test/utils/agents_test.py` | 修改 | patch `create_llm` 而非 `ChatOpenAI` |
| `utils/subagents.py` | 修改 | 去掉 `ChatOpenAI` 导入，改用 `create_llm` |

---

## Task 1: Config 层 — 新增 Google 和 Anthropic API Key 字段

**Files:**
- Modify: `utils/configs.py`
- Modify: `test/conftest.py`
- Modify: `test/utils/configs_test.py`
- Modify: `env.toml`

- [ ] **Step 1: 在 configs_test.py 补充断言（先写失败的测试）**

打开 `test/utils/configs_test.py`，在 `test_env_config_defaults` 的 assert 块末尾追加两行：

```python
    assert isinstance(configs.EnvConfig.GOOGLE_API_KEY, SecretStr)
    assert isinstance(configs.EnvConfig.ANTHROPIC_API_KEY, SecretStr)
```

测试中 env.toml 模板还没有 `google_api_key`，所以 `EnvConfig.GOOGLE_API_KEY` 会因 KeyError 而失败——这正是我们期望的。

- [ ] **Step 2: 确认测试失败**

```bash
cd /home/exdragine/frontier && python -m pytest test/utils/configs_test.py -v
```

预期：FAILED，错误信息类似 `KeyError: 'google_api_key'`

- [ ] **Step 3: 更新 `utils/configs.py`，增加两个字段**

在 `utils/configs.py` 第 38 行（`OPENAI_API_KEY` 所在的 `[key]` 区块）之后，添加：

```python
    GOOGLE_API_KEY: SecretStr = SecretStr(key.get("google_api_key", ""))
    ANTHROPIC_API_KEY: SecretStr = SecretStr(key.get("anthropic_api_key", ""))
```

使用 `key.get(...)` 默认空字符串，避免旧 env.toml 升级时报错。

- [ ] **Step 4: 更新 `test/conftest.py` env.toml 模板**

在 `_ensure_env_file` 函数的 `[key]` 区块（第 234-237 行附近），在 `github_pat = "ghp-test"` 后面加两行：

```toml
google_api_key = "ggl-test"
anthropic_api_key = "ant-test"
```

- [ ] **Step 5: 更新 `env.toml`（真实配置文件），新增两个 key 字段**

在 `env.toml` 的 `[key]` 区块（第 12-14 行），在 `github_pat = ""` 下方追加：

```toml
google_api_key = ""
anthropic_api_key = ""
```

在此处填入你的 Google AI Studio API Key（https://aistudio.google.com/apikey 获取）。

- [ ] **Step 6: 运行测试，确认通过**

```bash
python -m pytest test/utils/configs_test.py -v
```

预期：PASSED

- [ ] **Step 7: Commit**

```bash
git add utils/configs.py test/conftest.py test/utils/configs_test.py env.toml
git commit -m "feat: add GOOGLE_API_KEY and ANTHROPIC_API_KEY to config"
```

---

## Task 2: 新建 `utils/llm_factory.py`（TDD）

**Files:**
- Create: `utils/llm_factory.py`
- Create: `test/utils/llm_factory_test.py`

- [ ] **Step 1: 新建测试文件 `test/utils/llm_factory_test.py`**

```python
# ruff: noqa: S101

from unittest.mock import MagicMock

import pytest

import utils.llm_factory as factory


def test_gemini_routes_to_google(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(model="gemini-2.5-flash", max_retries=2, streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "gemini-2.5-flash"
    assert "google_api_key" in kw
    assert kw.get("max_retries") == 2
    assert kw.get("streaming") is False


def test_gpt_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="gpt-4o", timeout=300, streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "gpt-4o"
    assert "openai_api_key" in kw
    assert "openai_api_base" in kw
    assert kw.get("request_timeout") == 300   # timeout → request_timeout
    assert "timeout" not in kw                # raw "timeout" filtered out


def test_o3_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="o3", streaming=False)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "o3"
    assert "openai_api_key" in kw


def test_o4_mini_routes_to_openai(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="o4-mini")

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "o4-mini"
    assert "openai_api_key" in kw


def test_claude_routes_to_anthropic(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)

    factory.create_llm(model="claude-3-5-sonnet-20241022", timeout=60)

    mock_cls.assert_called_once()
    kw = mock_cls.call_args.kwargs
    assert kw["model"] == "claude-3-5-sonnet-20241022"
    assert "anthropic_api_key" in kw
    assert kw.get("default_request_timeout") == 60  # timeout → default_request_timeout
    assert "timeout" not in kw


def test_openai_kwargs_filtered_for_google(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(
        model="gemini-2.5-flash",
        use_responses_api=True,
        reasoning_effort="high",
        verbosity="low",
        max_retries=2,
    )

    kw = mock_cls.call_args.kwargs
    assert "use_responses_api" not in kw
    assert "reasoning_effort" not in kw
    assert "verbosity" not in kw
    assert kw.get("max_retries") == 2   # 通用参数正常传入


def test_openai_kwargs_filtered_for_anthropic(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatAnthropic", mock_cls)

    factory.create_llm(
        model="claude-3-5-haiku-20241022",
        use_responses_api=True,
        reasoning_effort="medium",
        max_retries=2,
    )

    kw = mock_cls.call_args.kwargs
    assert "use_responses_api" not in kw
    assert "reasoning_effort" not in kw
    assert kw.get("max_retries") == 2


def test_unknown_prefix_raises():
    with pytest.raises(ValueError, match="未知模型前缀"):
        factory.create_llm(model="mistral-7b-instruct")


def test_openai_base_url_included(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatOpenAI", mock_cls)

    factory.create_llm(model="gpt-4o")

    kw = mock_cls.call_args.kwargs
    assert "openai_api_base" in kw
    assert kw["openai_api_base"]  # 非空


def test_google_no_base_url_field(monkeypatch):
    mock_cls = MagicMock()
    monkeypatch.setattr(factory, "ChatGoogleGenerativeAI", mock_cls)

    factory.create_llm(model="gemini-2.0-flash")

    kw = mock_cls.call_args.kwargs
    assert "openai_api_base" not in kw
    assert "base_url" not in kw
```

- [ ] **Step 2: 确认测试失败（llm_factory.py 还不存在）**

```bash
python -m pytest test/utils/llm_factory_test.py -v
```

预期：ERROR — `ModuleNotFoundError: No module named 'utils.llm_factory'`

- [ ] **Step 3: 新建 `utils/llm_factory.py`**

```python
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from utils.configs import EnvConfig


@dataclass
class ProviderConfig:
    cls_fn: Callable[[], type[BaseChatModel]]  # 延迟求值，支持测试时替换
    api_key_fn: Callable[[], SecretStr]
    api_key_field: str
    valid_kwargs: set[str]
    kwarg_map: dict[str, str] = field(default_factory=dict)
    base_url_fn: Callable[[], str] | None = None
    base_url_field: str | None = None


_OPENAI_VALID = {
    "streaming", "max_retries", "timeout",
    "use_responses_api", "reasoning_effort", "verbosity", "temperature",
}
_GOOGLE_VALID = {"streaming", "max_retries", "timeout", "temperature"}
_ANTHROPIC_VALID = {"streaming", "max_retries", "timeout", "temperature"}

_openai_config = ProviderConfig(
    cls_fn=lambda: ChatOpenAI,
    api_key_fn=lambda: EnvConfig.OPENAI_API_KEY,
    api_key_field="openai_api_key",
    valid_kwargs=_OPENAI_VALID,
    kwarg_map={"timeout": "request_timeout"},
    base_url_fn=lambda: EnvConfig.OPENAI_BASE_URL,
    base_url_field="openai_api_base",
)

PROVIDERS: list[tuple[str, ProviderConfig]] = [
    (
        "gemini-",
        ProviderConfig(
            cls_fn=lambda: ChatGoogleGenerativeAI,
            api_key_fn=lambda: EnvConfig.GOOGLE_API_KEY,
            api_key_field="google_api_key",
            valid_kwargs=_GOOGLE_VALID,
        ),
    ),
    ("gpt-", _openai_config),
    ("o1", _openai_config),
    ("o3", _openai_config),
    ("o4", _openai_config),
    (
        "claude-",
        ProviderConfig(
            cls_fn=lambda: ChatAnthropic,
            api_key_fn=lambda: EnvConfig.ANTHROPIC_API_KEY,
            api_key_field="anthropic_api_key",
            valid_kwargs=_ANTHROPIC_VALID,
            kwarg_map={"timeout": "default_request_timeout"},
        ),
    ),
]


def create_llm(model: str, **kwargs) -> BaseChatModel:
    """根据模型名称前缀路由到对应 Provider，自动过滤不支持的 kwargs。"""
    for prefix, config in PROVIDERS:
        if model.startswith(prefix):
            cls = config.cls_fn()
            api_key = config.api_key_fn()
            filtered: dict = {}
            for k, v in kwargs.items():
                if k in config.valid_kwargs:
                    actual_key = config.kwarg_map.get(k, k)
                    filtered[actual_key] = v
            if config.base_url_fn and config.base_url_field:
                filtered[config.base_url_field] = config.base_url_fn()
            return cls(**{config.api_key_field: api_key, "model": model, **filtered})
    raise ValueError(
        f"未知模型前缀，无法路由: {model!r}。"
        f"支持的前缀: {[p for p, _ in PROVIDERS]}"
    )
```

- [ ] **Step 4: 运行测试，确认全部通过**

```bash
python -m pytest test/utils/llm_factory_test.py -v
```

预期：所有 10 个测试 PASSED

- [ ] **Step 5: Commit**

```bash
git add utils/llm_factory.py test/utils/llm_factory_test.py
git commit -m "feat: add llm_factory with multi-provider routing"
```

---

## Task 3: 更新 `utils/agents.py` 及其测试

**Files:**
- Modify: `utils/agents.py:1-16`（imports）、`utils/agents.py:50-58`、`utils/agents.py:175-187`
- Modify: `test/utils/agents_test.py:34`

- [ ] **Step 1: 更新 `test/utils/agents_test.py`，patch `create_llm` 而非 `ChatOpenAI`**

将第 31-35 行：

```python
    class DummyModel:
        def __init__(self, **_kwargs):
            pass

    monkeypatch.setattr(agents, "ChatOpenAI", DummyModel)
```

替换为：

```python
    class DummyModel:
        pass

    monkeypatch.setattr(agents, "create_llm", lambda model, **_kw: DummyModel())
```

- [ ] **Step 2: 运行测试，确认失败（agents.py 还没改）**

```bash
python -m pytest test/utils/agents_test.py -v
```

预期：FAILED — `AttributeError: module 'utils.agents' has no attribute 'create_llm'`

- [ ] **Step 3: 更新 `utils/agents.py` 的 imports**

将第 15 行：
```python
from langchain_openai import ChatOpenAI
```
替换为：
```python
from utils.llm_factory import create_llm
```

- [ ] **Step 4: 更新 `utils/agents.py` 的 `assistant_agent` 函数（第 50-58 行）**

将：
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

替换为：
```python
    model = create_llm(
        model=use_model,
        streaming=False,
        max_retries=2,
        timeout=300,
        use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
    )
```

- [ ] **Step 5: 更新 `utils/agents.py` 的 `chat_agent` 函数（第 175-187 行）**

将：
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

替换为：
```python
        model_kwargs: dict = {
            "model": EnvConfig.ADVAN_MODEL,
            "streaming": False,
            "max_retries": 2,
            "timeout": 300,
            "use_responses_api": EnvConfig.ADVAN_MODEL_USE_RESPONSES_API,
        }
        if EnvConfig.ADVAN_MODEL_USE_RESPONSES_API:
            model_kwargs["reasoning_effort"] = capability
            model_kwargs["verbosity"] = "low"
        model = create_llm(**model_kwargs)
```

- [ ] **Step 6: 运行 agents 测试**

```bash
python -m pytest test/utils/agents_test.py -v
```

预期：PASSED

- [ ] **Step 7: Commit**

```bash
git add utils/agents.py test/utils/agents_test.py
git commit -m "feat: replace ChatOpenAI with create_llm in agents.py"
```

---

## Task 4: 更新 `utils/subagents.py`

**Files:**
- Modify: `utils/subagents.py:1-22`

- [ ] **Step 1: 更新 `utils/subagents.py` 的 imports**

将第 4 行：
```python
from langchain_openai import ChatOpenAI
```
替换为：
```python
from utils.llm_factory import create_llm
```

同时删除第 10-12 行（现在 llm_factory 内部已处理这些值，不需要模块级变量）：
```python
OPENAI_BASE_URL = EnvConfig.OPENAI_BASE_URL
OPENAI_API_KEY = EnvConfig.OPENAI_API_KEY
```

- [ ] **Step 2: 替换模块级 `model` 初始化（第 15-22 行）**

将：
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

替换为：
```python
model = create_llm(
    model=BASIC_MODEL,
    max_retries=2,
    timeout=30,
    use_responses_api=EnvConfig.BASIC_MODEL_USE_RESPONSES_API,
)
```

- [ ] **Step 3: 运行全部测试，确认无回归**

```bash
python -m pytest test/ -v --tb=short
```

预期：全部 PASSED，无新增失败

- [ ] **Step 4: Commit**

```bash
git add utils/subagents.py
git commit -m "feat: replace ChatOpenAI with create_llm in subagents.py"
```

---

## Task 5: 更新 `env.toml` 模型名称为原生格式

**Files:**
- Modify: `env.toml`

> **注意：** `paint_model` 通过 `wonderland/__init__.py` 的原始 OpenAI AsyncClient 调用，走 OpenRouter，格式保持不变。只需改 `basic_model` 和 `advan_model`。

- [ ] **Step 1: 更新 `env.toml` 的模型名称**

将 `[endpoint]` 区块中：
```toml
openai_base_url = "https://openrouter.ai/api/v1"
basic_model = "google/gemini-2.5-flash"
advan_model = "openai/gpt-5-mini"
```

改为：
```toml
openai_base_url = "https://api.openai.com/v1"
basic_model = "gemini-2.5-flash"
advan_model = "gpt-4o-mini"
```

**关于 `openai_base_url`：**
- 如果你的 `advan_model` 仍然想走 OpenRouter（继续使用 OpenRouter key 访问 GPT），保留 `https://openrouter.ai/api/v1`
- 如果改为原生 OpenAI 直连，改为 `https://api.openai.com/v1` 并在 `openai_api_key` 填写官方 key
- Google 和 Anthropic 模型始终走原生 SDK，不使用 `openai_base_url`

- [ ] **Step 2: 运行全部测试，确认无回归**

```bash
python -m pytest test/ -v --tb=short
```

预期：全部 PASSED

- [ ] **Step 3: Commit**

```bash
git add env.toml
git commit -m "config: update model names to native provider format"
```

---

## 验证完成

- [ ] `python -m pytest test/ -v` 全部通过
- [ ] `utils/agents.py` 中无 `ChatOpenAI` 引用
- [ ] `utils/subagents.py` 中无 `ChatOpenAI` 引用
- [ ] `utils/llm_factory.py` 存在且包含 `PROVIDERS` 和 `create_llm`
- [ ] `env.toml` 中 `google_api_key` 字段存在（可为空）
