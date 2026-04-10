# Content Check Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 默认禁用消息/图像内容检测模型，通过 `env.toml` 的 `[content_check] enabled` 显式启用，禁用时仍发送 🔮 表情回复。

**Architecture:** 新增 `CONTENT_CHECK_ENABLED` 配置项（默认 `false`），在 `utils/message.py` 模块级按此标志条件实例化模型，`message_check()` 开头加早期返回，`plugins/fireside/__init__.py` 中将 `risk_check` 赋值改为条件分支。

**Tech Stack:** Python, NoneBot2, tomllib, pytest-asyncio

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `env.toml` | 修改 | 新增 `[content_check]` 配置段 |
| `utils/configs.py` | 修改 | 读取新段，添加 `CONTENT_CHECK_ENABLED` |
| `utils/message.py` | 修改 | 条件实例化模型，`message_check()` 加早期返回 |
| `plugins/fireside/__init__.py` | 修改 | `risk_check` 改为条件分支 |
| `test/utils/message_test.py` | 修改 | 更新现有测试 + 新增禁用场景测试 |

---

### Task 1: 添加 `CONTENT_CHECK_ENABLED` 配置

**Files:**
- Modify: `env.toml`
- Modify: `utils/configs.py`

- [ ] **Step 1: 在 `env.toml` 末尾新增配置段**

  打开 `env.toml`，在文件末尾添加：

  ```toml
  [content_check]
  enabled = false
  ```

- [ ] **Step 2: 在 `utils/configs.py` 读取新段**

  在现有 `dashboard: dict = ...` 行之后、`class EnvConfig:` 之前，添加：

  ```python
  content_check: dict = config.get("content_check", {})
  ```

  在 `EnvConfig` 类末尾（`IMAGE_AUTO_CLEANUP` 之后）添加：

  ```python
  CONTENT_CHECK_ENABLED: bool = content_check.get("enabled", False)
  ```

- [ ] **Step 3: 验证配置可读取**

  ```bash
  cd /home/exdragine/frontier
  python -c "from utils.configs import EnvConfig; print(EnvConfig.CONTENT_CHECK_ENABLED)"
  ```

  Expected output:
  ```
  False
  ```

- [ ] **Step 4: 提交**

  ```bash
  git add env.toml utils/configs.py
  git commit -m "feat: add CONTENT_CHECK_ENABLED config (default false)"
  ```

---

### Task 2: 更新 `utils/message.py` — 条件实例化 + 早期返回

**Files:**
- Modify: `utils/message.py:23-24`（模块级实例化）
- Modify: `utils/message.py:248-258`（`message_check` 函数体）
- Modify: `test/utils/message_test.py`（更新现有测试 + 新增测试）

- [ ] **Step 1: 先写新增的测试**

  在 `test/utils/message_test.py` 末尾添加：

  ```python
  @pytest.mark.asyncio
  async def test_message_check_disabled_returns_safe(monkeypatch):
      """CONTENT_CHECK_ENABLED=False 时，message_check 直接返回 Safe，不调用检测器"""
      monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", False)
      result = await message_module.message_check("任意内容", None)
      assert result == "Safe"


  @pytest.mark.asyncio
  async def test_message_check_disabled_with_images_returns_safe(monkeypatch):
      """CONTENT_CHECK_ENABLED=False 时，即使有图片也直接返回 Safe"""
      monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", False)
      result = await message_module.message_check(None, [b"fake_image_bytes"])
      assert result == "Safe"
  ```

- [ ] **Step 2: 更新现有 `test_message_check_text` 以适配条件实例化**

  将 `test/utils/message_test.py` 中的 `test_message_check_text` 替换为：

  ```python
  @pytest.mark.asyncio
  async def test_message_check_text(monkeypatch):
      """CONTENT_CHECK_ENABLED=True 时，调用 text_det 进行检测"""
      import types

      monkeypatch.setattr(message_module.EnvConfig, "CONTENT_CHECK_ENABLED", True)

      fake_det = types.SimpleNamespace()

      async def fake_predict(text):
          return "Safe", []

      fake_det.predict = fake_predict
      monkeypatch.setattr(message_module, "text_det", fake_det)

      result = await message_module.message_check("hello", None)
      assert result == "Safe"
  ```

- [ ] **Step 3: 运行测试，确认新测试失败（TDD）**

  ```bash
  cd /home/exdragine/frontier
  python -m pytest test/utils/message_test.py::test_message_check_disabled_returns_safe \
      test/utils/message_test.py::test_message_check_disabled_with_images_returns_safe \
      test/utils/message_test.py::test_message_check_text -v
  ```

  Expected: 3 个测试均 FAIL（函数尚未添加早期返回）

- [ ] **Step 4: 修改 `utils/message.py` — 条件实例化**

  将第 23-24 行：

  ```python
  text_det = TextCheck()
  image_det = ImageCheck()
  ```

  替换为：

  ```python
  text_det = TextCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
  image_det = ImageCheck() if EnvConfig.CONTENT_CHECK_ENABLED else None
  ```

- [ ] **Step 5: 修改 `utils/message.py` — `message_check()` 加早期返回**

  将 `message_check` 函数（第 248 行起）改为：

  ```python
  async def message_check(text: str | None, images: list | None) -> Literal["Safe", "Controversial", "Unsafe"]:
      if not EnvConfig.CONTENT_CHECK_ENABLED:
          return "Safe"
      if text:
          safe_label, categories = await text_det.predict(text)
          return safe_label
      if images:
          for image in images:
              image = Image.open(BytesIO(image))
              det_result = await image_det.predict(image)
              if det_result == "nsfw":
                  return "Unsafe"
      return "Safe"
  ```

- [ ] **Step 6: 运行测试，确认全部通过**

  ```bash
  cd /home/exdragine/frontier
  python -m pytest test/utils/message_test.py -v
  ```

  Expected: 所有测试 PASS

- [ ] **Step 7: 提交**

  ```bash
  git add utils/message.py test/utils/message_test.py
  git commit -m "feat: conditionally instantiate content check models, skip when disabled"
  ```

---

### Task 3: 更新 `plugins/fireside/__init__.py` — 条件分支

**Files:**
- Modify: `plugins/fireside/__init__.py:208-247`

- [ ] **Step 1: 修改 `handle_common` 中的检测调用**

  将第 208-210 行：

  ```python
  if not await message_gateway(event, messages):
      await common.finish()
  risk_check = await message_check(text, images)
  ```

  替换为：

  ```python
  if not await message_gateway(event, messages):
      await common.finish()
  if EnvConfig.CONTENT_CHECK_ENABLED:
      risk_check = await message_check(text, images)
  else:
      risk_check = "Safe"
  ```

  注意：`EnvConfig` 已通过 `from utils.configs import EnvConfig` 在文件顶部导入，无需额外导入。

- [ ] **Step 2: 验证 `match risk_check` 块无需改动**

  检查第 211 行起的 `match risk_check:` 块保持原样——三个 case 分支 (`"Safe"`, `"Controversial"`, `"Unsafe"`) 不变。禁用时 `risk_check = "Safe"` 会触发 🔮 表情回复，行为符合设计。

- [ ] **Step 3: 运行现有 fireside 测试，确认无回归**

  ```bash
  cd /home/exdragine/frontier
  python -m pytest test/plugins/fireside_flow_test.py test/plugins/fireside_memory_commands_test.py -v
  ```

  Expected: 所有测试 PASS

- [ ] **Step 4: 提交**

  ```bash
  git add plugins/fireside/__init__.py
  git commit -m "feat: skip content check inference when disabled, default to Safe reaction"
  ```

---

### Task 4: 全量验证

- [ ] **Step 1: 运行完整测试套件**

  ```bash
  cd /home/exdragine/frontier
  python -m pytest test/ -v --ignore=test/integration
  ```

  Expected: 所有测试 PASS，无新增失败

- [ ] **Step 2: 验证禁用状态下模块可正常导入（不加载模型）**

  ```bash
  python -c "
  import time
  t = time.time()
  from utils.message import message_check, text_det, image_det
  print(f'导入耗时: {time.time()-t:.2f}s')
  print(f'text_det: {text_det}')
  print(f'image_det: {image_det}')
  "
  ```

  Expected（`enabled = false` 时）：
  ```
  导入耗时: <1s   # 不加载模型，应远快于之前
  text_det: None
  image_det: None
  ```
