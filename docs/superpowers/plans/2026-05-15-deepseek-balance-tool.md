# DeepSeek Balance Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a LangChain tool that queries the configured DeepSeek API account balance.

**Architecture:** Implement a focused `tools/deepseek_balance.py` module with URL normalization, response formatting, async HTTP querying, and one `@tool` function. Register the module in the explicit tool-group map so it appears in the main agent tools. Cover behavior with existing pytest-style tool tests.

**Tech Stack:** Python 3.14, LangChain `@tool`, httpx async client, Pydantic `SecretStr`, pytest, pytest-asyncio.

---

## File Structure

- Create `tools/deepseek_balance.py`: DeepSeek balance URL building, API request, response formatting, tool function, and `aclose_http_client()`.
- Modify `tools/__init__.py`: add `deepseek_balance` to `_TOOL_MODULE_GROUPS` as `main`.
- Modify `test/tools/basic_info_tools_test.py`: add behavior tests for the new tool.
- Modify `test/tools/http_client_lifecycle_test.py`: add new module to HTTP client close contract.

### Task 1: Add DeepSeek Balance Behavior Tests

**Files:**
- Modify: `test/tools/basic_info_tools_test.py`

- [ ] **Step 1: Write failing tests**

Add these imports near the existing imports if they are not present:

```python
import httpx
from pydantic import SecretStr
```

Append these tests to `test/tools/basic_info_tools_test.py`:

```python
@pytest.mark.asyncio
async def test_deepseek_balance_tool_formats_balance(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr("sk-test"), raising=False)
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_BASE", "", raising=False)

    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "is_available": True,
                "balance_infos": [
                    {
                        "currency": "CNY",
                        "total_balance": "110.00",
                        "granted_balance": "10.00",
                        "topped_up_balance": "100.00",
                    }
                ],
            }

    class DummyClient:
        async def get(self, url, headers):
            captured["url"] = url
            captured["headers"] = headers
            return DummyResponse()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert captured["url"] == "https://api.deepseek.com/user/balance"
    assert captured["headers"] == {"Authorization": "Bearer sk-test"}
    assert "DeepSeek API 余额：可用" in result
    assert "- CNY 总余额 110.00，赠金 10.00，充值 100.00" in result
```

```python
@pytest.mark.asyncio
async def test_deepseek_balance_tool_reports_missing_key(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr(""), raising=False)

    result = await mod.get_deepseek_api_balance()

    assert result == "未配置 DeepSeek API Key：请在 env.toml 的 [key].deepseek_api_key 中填写。"
```

```python
@pytest.mark.asyncio
async def test_deepseek_balance_tool_normalizes_configured_base_url(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr("sk-test"), raising=False)
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1", raising=False)

    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"is_available": False, "balance_infos": []}

    class DummyClient:
        async def get(self, url, headers):
            captured["url"] = url
            return DummyResponse()

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert captured["url"] == "https://api.deepseek.com/user/balance"
    assert result == "DeepSeek API 余额：不可用\n余额明细：无"
```

```python
@pytest.mark.asyncio
async def test_deepseek_balance_tool_reports_http_error(load_tool_module, monkeypatch):
    mod = load_tool_module("deepseek_balance")
    monkeypatch.setattr(mod.EnvConfig, "DEEPSEEK_API_KEY", SecretStr("sk-test"), raising=False)

    class DummyClient:
        async def get(self, url, headers):
            raise httpx.ConnectError("network down")

    monkeypatch.setattr(mod, "httpx_client", DummyClient())

    result = await mod.get_deepseek_api_balance()

    assert result == "获取 DeepSeek API 余额失败: network down"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest test/tools/basic_info_tools_test.py -k deepseek_balance -q
```

Expected: FAIL because `tools/deepseek_balance.py` does not exist.

### Task 2: Implement DeepSeek Balance Tool

**Files:**
- Create: `tools/deepseek_balance.py`
- Modify: `test/tools/basic_info_tools_test.py`

- [ ] **Step 1: Write minimal implementation**

Create `tools/deepseek_balance.py` with:

```python
from urllib.parse import urlparse, urlunparse

import httpx
from langchain.tools import tool
from nonebot import logger

from utils.configs import EnvConfig

DEFAULT_BALANCE_URL = "https://api.deepseek.com/user/balance"

transport = httpx.AsyncHTTPTransport(http2=True, retries=3)
httpx_client = httpx.AsyncClient(transport=transport, timeout=30)


async def aclose_http_client() -> None:
    await httpx_client.aclose()


def _api_key_value() -> str:
    return EnvConfig.DEEPSEEK_API_KEY.get_secret_value().strip()


def _balance_url() -> str:
    raw_base = (EnvConfig.DEEPSEEK_API_BASE or "").strip()
    if not raw_base:
        return DEFAULT_BALANCE_URL

    parsed = urlparse(raw_base)
    if not parsed.scheme or not parsed.netloc:
        return DEFAULT_BALANCE_URL
    return urlunparse((parsed.scheme, parsed.netloc, "/user/balance", "", "", ""))


def _format_balance(data: dict) -> str:
    if not isinstance(data, dict):
        raise ValueError("响应不是 JSON 对象")

    available = "可用" if data.get("is_available") else "不可用"
    balance_infos = data.get("balance_infos")
    if not isinstance(balance_infos, list):
        raise ValueError("响应缺少 balance_infos 数组")
    if not balance_infos:
        return f"DeepSeek API 余额：{available}\n余额明细：无"

    lines = [f"DeepSeek API 余额：{available}"]
    for item in balance_infos:
        if not isinstance(item, dict):
            raise ValueError("balance_infos 包含非对象条目")
        currency = item.get("currency", "UNKNOWN")
        total = item.get("total_balance", "0")
        granted = item.get("granted_balance", "0")
        topped_up = item.get("topped_up_balance", "0")
        lines.append(f"- {currency} 总余额 {total}，赠金 {granted}，充值 {topped_up}")
    return "\n".join(lines)


@tool(response_format="content")
async def get_deepseek_api_balance() -> str:
    """查询 DeepSeek API 账户余额。"""
    api_key = _api_key_value()
    if not api_key:
        return "未配置 DeepSeek API Key：请在 env.toml 的 [key].deepseek_api_key 中填写。"

    try:
        response = await httpx_client.get(_balance_url(), headers={"Authorization": f"Bearer {api_key}"})
        response.raise_for_status()
        return _format_balance(response.json())
    except Exception as e:
        logger.error("DeepSeek balance query error", exc_info=e)
        return f"获取 DeepSeek API 余额失败: {e}"
```

- [ ] **Step 2: Run the focused tests**

Run:

```bash
pytest test/tools/basic_info_tools_test.py -k deepseek_balance -q
```

Expected: PASS.

### Task 3: Register Tool Group and Lifecycle Test

**Files:**
- Modify: `tools/__init__.py`
- Modify: `test/tools/basic_info_tools_test.py`
- Modify: `test/tools/http_client_lifecycle_test.py`

- [ ] **Step 1: Add lifecycle test parameter**

In `test/tools/http_client_lifecycle_test.py`, add this tuple to the parametrized list:

```python
("deepseek_balance", "httpx_client"),
```

- [ ] **Step 2: Update tool grouping test**

In `test/tools/basic_info_tools_test.py`, add this fake module entry:

```python
"deepseek_balance": types.SimpleNamespace(get_deepseek_api_balance=FakeBaseTool("get_deepseek_api_balance")),
```

Add `"get_deepseek_api_balance"` to the expected `module.agent_tools.main_tools` set.

- [ ] **Step 3: Register module group**

In `tools/__init__.py`, add this mapping inside `_TOOL_MODULE_GROUPS`:

```python
"deepseek_balance": "main",
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest test/tools/basic_info_tools_test.py test/tools/http_client_lifecycle_test.py -q
```

Expected: PASS.

### Task 4: Final Verification

**Files:**
- Verify all modified files

- [ ] **Step 1: Run linter on changed Python files**

Run:

```bash
ruff check tools/deepseek_balance.py tools/__init__.py test/tools/basic_info_tools_test.py test/tools/http_client_lifecycle_test.py
```

Expected: PASS with no lint errors.

- [ ] **Step 2: Run the relevant test suite**

Run:

```bash
pytest test/tools/basic_info_tools_test.py test/tools/http_client_lifecycle_test.py -q
```

Expected: PASS.

- [ ] **Step 3: Review git diff**

Run:

```bash
git diff -- tools/deepseek_balance.py tools/__init__.py test/tools/basic_info_tools_test.py test/tools/http_client_lifecycle_test.py docs/superpowers/specs/2026-05-15-deepseek-balance-tool-design.md docs/superpowers/plans/2026-05-15-deepseek-balance-tool.md
```

Expected: diff only contains the DeepSeek balance tool, tests, spec, and plan.

## Plan Self-Review

Spec coverage: the plan covers the new tool module, URL normalization, missing key handling, failure handling, tool group exposure, lifecycle closure, and verification.

Placeholder scan: no placeholder text remains.

Type consistency: test and implementation names match: `get_deepseek_api_balance`, `EnvConfig.DEEPSEEK_API_KEY`, `EnvConfig.DEEPSEEK_API_BASE`, and `httpx_client`.
