# Wonderland Paint Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decouple `plugins/wonderland` from the global OpenAI URL and key by adding paint-specific configuration with fallback behavior.

**Architecture:** Extend the existing `[endpoint]` and `[key]` sections with `paint_base_url` and `paint_api_key`, compute derived fallback values in `EnvConfig`, and recompute the same derived values during dashboard hot reload. Route all provider detection and client construction inside `plugins/wonderland` through `PAINT_BASE_URL` / `PAINT_API_KEY`, while leaving the rest of the application on the existing global OpenAI settings.

**Tech Stack:** Python 3.12+, NoneBot2, Pydantic `SecretStr`, `openai`, `google-genai`, pytest, Ruff, dashboard vanilla JS

---

## File Map

- `env.toml.example`
  Adds `paint_base_url` and `paint_api_key` to the sample config so users can discover the new fields.

- `utils/configs.py`
  Defines `EnvConfig.PAINT_BASE_URL` and `EnvConfig.PAINT_API_KEY` with empty-string fallback to the global OpenAI settings.

- `plugins/dashboard/api/settings_routes.py`
  Recomputes paint-specific fallback values on hot reload and masks `paint_api_key` in API responses.

- `plugins/dashboard/web/pages/Settings.js`
  Treats `paint_api_key` as a sensitive field so the settings UI renders it like the existing secret inputs.

- `plugins/wonderland/__init__.py`
  Uses only the derived paint config for OpenAI client construction, Vertex gateway detection, and `google.genai` client setup.

- `test/utils/configs_test.py`
  Verifies default fallback and explicit override behavior for the new config fields.

- `test/plugins/dashboard_routes_test.py`
  Verifies backend masking and `_reload_env_config()` fallback recomputation.

- `test/plugins/wonderland_test.py`
  Verifies paint-specific URL/key precedence for both OpenAI Images and Vertex-style gateways.

### Task 1: Add Paint-Specific Config Fields With Fallback

**Files:**
- Modify: `env.toml.example`
- Modify: `utils/configs.py`
- Modify: `test/utils/configs_test.py`

- [ ] **Step 1: Write the failing config tests**

Add these tests to `test/utils/configs_test.py` below the existing `test_env_config_defaults` test.

```python
def test_env_config_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
paint_base_url = ""

[key]
openai_api_key = "sk"
paint_api_key = ""
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[memory]
enabled = true

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.PAINT_BASE_URL == "https://example.com"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk"
```

```python
def test_env_config_paint_specific_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
paint_base_url = "https://paint.example.com"

[key]
openai_api_key = "sk-openai"
paint_api_key = "sk-paint"
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[memory]
enabled = true

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    configs = importlib.import_module("utils.configs")
    importlib.reload(configs)

    assert configs.EnvConfig.PAINT_BASE_URL == "https://paint.example.com"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk-paint"
```

- [ ] **Step 2: Run the config tests to verify they fail**

Run: `uv run pytest test/utils/configs_test.py -v`

Expected: FAIL with an `AttributeError` or assertion failure because `EnvConfig` does not yet expose `PAINT_BASE_URL` / `PAINT_API_KEY`.

- [ ] **Step 3: Implement the new config fields and sample config entries**

Update `env.toml.example` so the `[endpoint]` and `[key]` sections look like this:

```toml
[endpoint]
openai_base_url = ""
basic_model = ""
advan_model = ""
paint_model = ""
paint_base_url = ""
basic_model_use_responses_api = true
advan_model_use_responses_api = true

[key]
openai_api_key = ""
paint_api_key = ""
google_api_key = ""
anthropic_api_key = ""
nasa_api_key = "DEMO_KEY"
github_pat = ""
```

Update `utils/configs.py` in `EnvConfig` by inserting these lines immediately after `PAINT_MODEL` and `OPENAI_API_KEY`:

```python
    PAINT_BASE_URL: str = endpoint.get("paint_base_url") or OPENAI_BASE_URL
```

```python
    PAINT_API_KEY: SecretStr = SecretStr(key.get("paint_api_key") or key["openai_api_key"])
```

- [ ] **Step 4: Run the config tests to verify they pass**

Run: `uv run pytest test/utils/configs_test.py -v`

Expected: PASS for both config tests, including fallback and explicit override behavior.

- [ ] **Step 5: Commit the config field changes**

```bash
git add env.toml.example utils/configs.py test/utils/configs_test.py
git commit -m "feat: add paint-specific config fields"
```

### Task 2: Recompute Paint Config On Hot Reload And Mask It In Dashboard

**Files:**
- Modify: `plugins/dashboard/api/settings_routes.py`
- Modify: `plugins/dashboard/web/pages/Settings.js`
- Modify: `test/plugins/dashboard_routes_test.py`

- [ ] **Step 1: Write the failing dashboard tests**

Add these tests to `test/plugins/dashboard_routes_test.py` after `test_settings_mask_value`.

```python
def test_settings_sanitize_masks_paint_api_key():
    result = settings_routes._sanitize_config(
        {
            "key": {
                "openai_api_key": "sk-openai",
                "paint_api_key": "sk-paint-secret",
            }
        }
    )

    assert result["key"]["paint_api_key"] == "****cret"
```

```python
def test_reload_env_config_recomputes_paint_specific_values(tmp_path, monkeypatch):
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "Bot"

[endpoint]
openai_base_url = "https://global.example.com/v1"
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"
paint_base_url = ""

[key]
openai_api_key = "sk-global"
paint_api_key = ""
nasa_api_key = "nasa"
github_pat = "gh"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 3

[debug]
agent_debug_mode = false

[memory]
enabled = true

[dashboard]
password = "admin"
jwt_secret = "secret"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(settings_routes, "TOML_PATH", env_path)

    import utils.configs as configs

    configs.EnvConfig.OPENAI_BASE_URL = "https://old.example.com/v1"
    configs.EnvConfig.PAINT_BASE_URL = "https://old-paint.example.com/v1"
    configs.EnvConfig.OPENAI_API_KEY = SecretStr("sk-old-global")
    configs.EnvConfig.PAINT_API_KEY = SecretStr("sk-old-paint")

    settings_routes._reload_env_config()

    assert configs.EnvConfig.OPENAI_BASE_URL == "https://global.example.com/v1"
    assert configs.EnvConfig.PAINT_BASE_URL == "https://global.example.com/v1"
    assert configs.EnvConfig.OPENAI_API_KEY.get_secret_value() == "sk-global"
    assert configs.EnvConfig.PAINT_API_KEY.get_secret_value() == "sk-global"
```

Add the import needed for the second test at the top of the file:

```python
from pydantic import SecretStr
```

- [ ] **Step 2: Run the dashboard tests to verify they fail**

Run: `uv run pytest test/plugins/dashboard_routes_test.py -v`

Expected: FAIL because `paint_api_key` is not masked and `_reload_env_config()` does not yet recompute `PAINT_BASE_URL` / `PAINT_API_KEY`.

- [ ] **Step 3: Implement backend masking, hot reload, and settings UI secrecy**

In `plugins/dashboard/api/settings_routes.py`, update `SENSITIVE_FIELDS` to include `paint_api_key`:

```python
SENSITIVE_FIELDS = {
    "key": {"openai_api_key", "paint_api_key", "nasa_api_key", "github_pat"},
    "dashboard": {"jwt_secret", "password"},
}
```

In the `_reload_env_config()` function, add the paint-specific fallback assignments immediately after the existing OpenAI assignments:

```python
    EnvConfig.OPENAI_BASE_URL = ep.get("openai_base_url", EnvConfig.OPENAI_BASE_URL)
    EnvConfig.BASIC_MODEL = ep.get("basic_model", EnvConfig.BASIC_MODEL)
    EnvConfig.ADVAN_MODEL = ep.get("advan_model", EnvConfig.ADVAN_MODEL)
    EnvConfig.PAINT_MODEL = ep.get("paint_model", EnvConfig.PAINT_MODEL)
    EnvConfig.PAINT_BASE_URL = ep.get("paint_base_url") or EnvConfig.OPENAI_BASE_URL
```

```python
    EnvConfig.OPENAI_API_KEY = SecretStr(key.get("openai_api_key", ""))
    EnvConfig.PAINT_API_KEY = SecretStr(key.get("paint_api_key") or key.get("openai_api_key", ""))
    EnvConfig.NASA_API_KEY = SecretStr(key.get("nasa_api_key", ""))
    EnvConfig.GITHUB_PAT = SecretStr(key.get("github_pat", ""))
```

In `plugins/dashboard/web/pages/Settings.js`, update the `key` sensitive field set:

```javascript
const sensitiveFields = {
    key: new Set(['openai_api_key', 'paint_api_key', 'nasa_api_key', 'github_pat']),
    dashboard: new Set(['jwt_secret', 'password']),
};
```

- [ ] **Step 4: Run the dashboard tests to verify they pass**

Run: `uv run pytest test/plugins/dashboard_routes_test.py -v`

Expected: PASS for the new masking and hot-reload tests, along with the pre-existing dashboard route tests.

- [ ] **Step 5: Manually verify the settings UI and commit**

Start the app if it is not already running, open the dashboard settings page, switch to the `key` tab, and confirm `paint_api_key` is rendered as a password-style input with a show/hide toggle rather than a plain text field.

Then commit:

```bash
git add plugins/dashboard/api/settings_routes.py plugins/dashboard/web/pages/Settings.js test/plugins/dashboard_routes_test.py
git commit -m "feat: reload and mask paint-specific settings"
```

### Task 3: Route Wonderland Through Paint-Specific URL And Key

**Files:**
- Modify: `plugins/wonderland/__init__.py`
- Modify: `test/plugins/wonderland_test.py`

- [ ] **Step 1: Write the failing wonderland tests**

Update `test_paint_uses_images_generate_without_reference_images` so it explicitly differentiates the global config from the paint-specific config:

```python
    monkeypatch.setattr(wonderland.EnvConfig, "OPENAI_BASE_URL", "https://global.example.com/v1")
    monkeypatch.setattr(wonderland.EnvConfig, "PAINT_BASE_URL", "https://paint.example.com/v1")
    monkeypatch.setattr(wonderland.EnvConfig, "OPENAI_API_KEY", SecretStr("sk-global"))
    monkeypatch.setattr(wonderland.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint"))
```

Change the assertions at the bottom of that test to:

```python
    assert calls["client"]["base_url"] == "https://paint.example.com/v1"
    assert calls["client"]["api_key"] == "sk-paint"
```

Update the Vertex gateway tests so only the paint-specific URL contains `vertex-ai`:

```python
    monkeypatch.setattr(wonderland.EnvConfig, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setattr(wonderland.EnvConfig, "PAINT_BASE_URL", "https://zenmux.ai/api/vertex-ai")
    monkeypatch.setattr(wonderland.EnvConfig, "OPENAI_API_KEY", SecretStr("sk-global"))
    monkeypatch.setattr(wonderland.EnvConfig, "PAINT_API_KEY", SecretStr("sk-paint"))
```

Add these assertions to both Vertex tests:

```python
    assert calls["client"]["api_key"] == "sk-paint"
    assert calls["client"]["http_options"].kwargs["base_url"] == "https://zenmux.ai/api/vertex-ai"
```

Add the import needed for the `SecretStr` monkeypatches at the top of the file:

```python
from pydantic import SecretStr
```

- [ ] **Step 2: Run the wonderland tests to verify they fail**

Run: `uv run pytest test/plugins/wonderland_test.py -v`

Expected: FAIL because `plugins/wonderland/__init__.py` still reads `OPENAI_BASE_URL` / `OPENAI_API_KEY` for provider detection and client construction.

- [ ] **Step 3: Implement paint-specific client routing**

In `plugins/wonderland/__init__.py`, add these helpers near `_normalize_reference_image()`:

```python
def _paint_base_url() -> str:
    return EnvConfig.PAINT_BASE_URL


def _paint_api_key() -> str:
    return EnvConfig.PAINT_API_KEY.get_secret_value()
```

Update `_use_vertex_image_gateway()` and `_openai_client_kwargs()` to use those helpers:

```python
def _use_vertex_image_gateway() -> bool:
    return "vertex-ai" in _paint_base_url().lower()


def _openai_client_kwargs() -> dict[str, str]:
    kwargs = {"api_key": _paint_api_key()}
    if _paint_base_url():
        kwargs["base_url"] = _paint_base_url()
    return kwargs
```

Update `_paint_with_vertex_gateway()` to use the paint-specific config instead of the global OpenAI config:

```python
    client = genai.Client(
        api_key=_paint_api_key(),
        vertexai=True,
        http_options=genai_types.HttpOptions(api_version="v1", base_url=_paint_base_url()),
    )
```

Add the missing `SecretStr` import to the top of the file only if you need it for new helper tests; otherwise keep the production file imports unchanged.

- [ ] **Step 4: Run the wonderland tests to verify they pass**

Run: `uv run pytest test/plugins/wonderland_test.py -v`

Expected: PASS for OpenAI Images, Vertex-style generation, Vertex-style edits, prompt stripping, and error handling.

- [ ] **Step 5: Commit the wonderland routing changes**

```bash
git add plugins/wonderland/__init__.py test/plugins/wonderland_test.py
git commit -m "feat: use paint-specific wonderland credentials"
```

### Task 4: Run Final Verification For The Paint Config Slice

**Files:**
- Modify: none
- Test: `test/utils/configs_test.py`
- Test: `test/plugins/dashboard_routes_test.py`
- Test: `test/plugins/wonderland_test.py`

- [ ] **Step 1: Run the full targeted pytest slice**

Run:

```bash
uv run pytest test/utils/configs_test.py test/plugins/dashboard_routes_test.py test/plugins/wonderland_test.py -v
```

Expected: PASS for all targeted config, dashboard, and wonderland tests.

- [ ] **Step 2: Run Ruff on every touched file**

Run:

```bash
uv run ruff check utils/configs.py plugins/dashboard/api/settings_routes.py plugins/wonderland/__init__.py test/utils/configs_test.py test/plugins/dashboard_routes_test.py test/plugins/wonderland_test.py
node --check plugins/dashboard/web/pages/Settings.js
```

Expected: Ruff passes for all Python files, and `node --check` exits successfully for the dashboard settings page.

- [ ] **Step 3: Review the final diff**

Run:

```bash
git log --oneline -n 4
git diff -- env.toml.example utils/configs.py plugins/dashboard/api/settings_routes.py plugins/dashboard/web/pages/Settings.js plugins/wonderland/__init__.py test/utils/configs_test.py test/plugins/dashboard_routes_test.py test/plugins/wonderland_test.py
```

Expected: The recent commit log includes the three task commits, and the file diff shows only paint-specific config additions, dashboard secrecy/hot-reload updates, and wonderland routing changes.

- [ ] **Step 4: Create the final integration commit if Task 4 required follow-up edits**

If Task 4 surfaced any last-minute fixups, commit them with:

```bash
git add env.toml.example utils/configs.py plugins/dashboard/api/settings_routes.py plugins/dashboard/web/pages/Settings.js plugins/wonderland/__init__.py test/utils/configs_test.py test/plugins/dashboard_routes_test.py test/plugins/wonderland_test.py
git commit -m "test: verify paint config integration"
```

If Tasks 1-3 already left the branch clean, skip this commit.
