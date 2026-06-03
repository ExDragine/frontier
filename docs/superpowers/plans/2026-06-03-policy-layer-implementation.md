# Frontier 轻量策略层 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建纯 Python 轻量策略层，用 manifesto 驱动的策略引擎替代 `message_gateway()`、`message_check()`、`sanitize_outgoing_text()`。

**Architecture:** `policy/` 模块提供 `PolicyEngine` 单例，加载 `manifesto.yaml` 并执行策略链。调用方(`plugins/agent/__init__.py`)在 `input` 和 `output` 两个介入点传入快照，获得 `Decision` 判决。拒绝时发送 LLM 生成的提示消息。

**Tech Stack:** Python 3.14+, Pydantic（manifesto 校验）, PyYAML（YAML 解析）, pytest + pytest-asyncio（测试）。

---

## File Map

| 操作 | 路径 | 职责 |
|------|------|------|
| **Create** | `policy/__init__.py` | 全局单例 `engine` |
| **Create** | `policy/decisions.py` | `Verdict` 枚举 + `Decision` 值对象 |
| **Create** | `policy/snapshots.py` | `InputSnapshot`, `OutputSnapshot` 数据类 |
| **Create** | `policy/base.py` | `BasePolicy` 抽象基类 |
| **Create** | `policy/errors.py` | `PolicyLoadError` 异常 |
| **Create** | `policy/manifesto.py` | Pydantic 模型 + YAML 加载 |
| **Create** | `policy/manifesto.yaml` | 策略配置清单 |
| **Create** | `policy/engine.py` | `PolicyEngine` 核心 |
| **Create** | `policy/policies/__init__.py` | 策略包入口 |
| **Create** | `policy/policies/access_control.py` | `AccessControlPolicy` |
| **Create** | `policy/policies/content_safety.py` | `ContentSafetyPolicy` |
| **Modify** | `plugins/agent/__init__.py` | 接入策略引擎，替换 gateway+check+sanitize |
| **Modify** | `utils/message.py` | 删除 `message_gateway()`、`message_check()`、`sanitize_outgoing_text()`、`sanitize_outgoing_message()`，保留其余函数 |
| **Modify** | `utils/configs.py` | 删除已迁移的 agent 访问控制字段和 CONTENT_CHECK_ENABLED |
| **Modify** | `env.toml` | 删除 `agent_whitelist_*`、`agent_blacklist_*` 和 `[content_check]` 节 |
| **Create** | `test/policy/__init__.py` | 测试包 |
| **Create** | `test/policy/conftest.py` | 策略层测试 fixtures |
| **Create** | `test/policy/test_decisions.py` | Decision 单元测试 |
| **Create** | `test/policy/test_manifesto.py` | Manifesto 加载/校验测试 |
| **Create** | `test/policy/test_engine.py` | 引擎核心契约测试 |
| **Create** | `test/policy/test_access_control.py` | 访问控制策略测试 |
| **Create** | `test/policy/test_content_safety.py` | 内容安全策略测试 |

---

### Task 1: 创建目录结构和数据层

**Files:**
- Create: `policy/decisions.py`
- Create: `policy/snapshots.py`
- Create: `policy/errors.py`
- Create: `policy/base.py`
- Create: `test/policy/__init__.py`
- Create: `test/policy/conftest.py`

- [ ] **Step 1: 创建 policy/ 目录结构**

```bash
mkdir -p policy/policies test/policy
touch policy/__init__.py policy/policies/__init__.py test/policy/__init__.py
```

- [ ] **Step 2: 创建 `policy/decisions.py`**

```python
"""策略判决值对象。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


@dataclass
class Decision:
    """策略链执行的判决结果。

    - allow: 继续执行下一条策略
    - deny:  短路，立即返回，不再执行后续策略。必须携带 message。
    - warn:  继续执行后续策略，可携带 message 和 metadata。
    """

    verdict: Verdict
    reason: str
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls, reason: str = "ok") -> "Decision":
        return cls(verdict=Verdict.ALLOW, reason=reason)

    @classmethod
    def deny(cls, reason: str, *, message: str) -> "Decision":
        if not message:
            raise ValueError("deny decision must carry a non-empty message")
        return cls(verdict=Verdict.DENY, reason=reason, message=message)

    @classmethod
    def warn(cls, reason: str, *, message: str = "") -> "Decision":
        return cls(verdict=Verdict.WARN, reason=reason, message=message)
```

- [ ] **Step 3: 创建 `policy/snapshots.py`**

```python
"""介入点快照数据类。"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class InputSnapshot:
    """input 介入点的完整快照。"""

    user_id: str
    group_id: int | None
    chat_type: str  # "group" | "private"
    text: str
    images: list[Callable[[], bytes | None]] = field(default_factory=list)
    is_at_bot: bool = False
    is_bot_name_prefix: bool = False
    raw_message: dict = field(default_factory=dict)


@dataclass
class OutputSnapshot:
    """output 介入点的完整快照。"""

    user_id: str
    group_id: int | None
    text: str
    agent_response_raw: str = ""
```

- [ ] **Step 4: 创建 `policy/errors.py`**

```python
"""策略层异常类型。"""


class PolicyLoadError(RuntimeError):
    """manifesto 加载/校验失败时抛出，阻止进程启动。"""
```

- [ ] **Step 5: 创建 `policy/base.py`**

```python
"""策略抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any

from .decisions import Decision
from .snapshots import InputSnapshot, OutputSnapshot


class BasePolicy(ABC):
    """所有策略的抽象基类。

    子类契约:
    - 必须设置 name 类属性（对应 manifesto 中的 policies.<name>）。
    - evaluate() 必须是无状态、确定性的。
    - configure() 在 __init__ 之后、evaluate() 之前由引擎调用。
    """

    name: str = ""
    severity: str = "normal"  # "safety" | "normal"
    config: dict[str, Any] = {}

    def configure(self, config: dict[str, Any]) -> None:
        self.config = config
        self.severity = config.get("severity", self.severity)

    @abstractmethod
    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        ...
```

- [ ] **Step 6: 创建 `test/policy/conftest.py`**

```python
# ruff: noqa: S101

from pathlib import Path

import pytest


@pytest.fixture
def sample_manifesto_yaml() -> str:
    return """
version: "1.0"
metadata:
  name: test-policy
  description: Test policy manifest

policies:
  always_allow:
    type: builtin
    class_path: test.policy.conftest.AlwaysAllowPolicy
    description: Always returns allow

  always_deny:
    type: builtin
    class_path: test.policy.conftest.AlwaysDenyPolicy
    description: Always returns deny

  exploding:
    type: builtin
    class_path: test.policy.conftest.ExplodingPolicy
    description: Always raises

intervention_points:
  input:
    - policy: always_deny
      config: {}
      default_decision: deny
    - policy: always_allow
      config: {}
      default_decision: allow
  output:
    - policy: always_allow
      config: {}
      default_decision: allow
  single_chain:
    - policy: always_allow
      config: {}
      default_decision: allow
"""


@pytest.fixture
def manifesto_file(tmp_path: Path, sample_manifesto_yaml: str) -> Path:
    path = tmp_path / "manifesto.yaml"
    path.write_text(sample_manifesto_yaml, encoding="utf-8")
    return path


# ── 测试桩策略 ──

from policy.base import BasePolicy
from policy.decisions import Decision
from policy.snapshots import InputSnapshot, OutputSnapshot


class AlwaysAllowPolicy(BasePolicy):
    name = "always_allow"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        return Decision.allow(reason="always")


class AlwaysDenyPolicy(BasePolicy):
    name = "always_deny"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        return Decision.deny(reason="blocked", message="访问被拒绝")


class ExplodingPolicy(BasePolicy):
    name = "exploding"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        raise RuntimeError("boom")
```

- [ ] **Step 7: 运行测试确认基础设施可用**

```bash
python -c "from policy.decisions import Decision, Verdict; d = Decision.deny('test', message='no'); assert d.message == 'no'; print('OK')"
```

Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git add policy/ test/policy/
git commit -m "feat(policy): scaffold data tier — Decision, Snapshot, BasePolicy, errors"
```

---

### Task 2: Manifesto 系统

**Files:**
- Create: `policy/manifesto.py`
- Create: `policy/manifesto.yaml`
- Create: `test/policy/test_manifesto.py`

- [ ] **Step 1: 创建 `policy/manifesto.py`**

```python
"""YAML manifesto 解析与校验。"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from .errors import PolicyLoadError


class PolicyDefinition(BaseModel):
    type: str = "builtin"
    class_path: str
    description: str = ""


class PolicyBinding(BaseModel):
    policy: str
    config: dict[str, Any] = {}
    default_decision: str = "allow"


class ManifestoMetadata(BaseModel):
    name: str
    description: str = ""


class Manifesto(BaseModel):
    version: str
    metadata: ManifestoMetadata
    policies: dict[str, PolicyDefinition]
    intervention_points: dict[str, list[PolicyBinding]]

    @classmethod
    def from_yaml(cls, path: Path) -> "Manifesto":
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PolicyLoadError(f"Invalid YAML in manifesto {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise PolicyLoadError(f"Manifesto {path} must be a YAML mapping, got {type(raw).__name__}")
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:
            raise PolicyLoadError(f"Invalid manifesto schema in {path}:\n{exc}") from exc
```

- [ ] **Step 2: 创建 `policy/manifesto.yaml`**

```yaml
version: "1.0"
metadata:
  name: frontier-policy
  description: Frontier QQ bot security and governance policies

policies:
  access_control:
    type: builtin
    class_path: policy.policies.access_control.AccessControlPolicy
    description: 用户和群组的黑白名单访问控制

  content_safety:
    type: builtin
    class_path: policy.policies.content_safety.ContentSafetyPolicy
    description: 文本和图片的内容安全检测

intervention_points:
  input:
    - policy: access_control
      config:
        whitelist_mode: false
        whitelist_persons: []
        whitelist_groups: []
        blacklist_persons: [2085003190]
        blacklist_groups: []
        bot_name_prefixes:
          - "小李子"
          - "小栗子"
        test_group_ids: []
      default_decision: deny

    - policy: content_safety
      config:
        direction: input
        severity: safety
        text_model: Qwen3Guard-Gen-0.6B
        image_model: Falconsai/nsfw_image_detection
        unsafe_reaction: 26
        controversial_reaction: 212
        safe_reaction: 32
      default_decision: allow

  output:
    - policy: content_safety
      config:
        direction: output
        severity: safety
        text_model: Qwen3Guard-Gen-0.6B
        block_message: "⚠️ 内容被安全策略拦截"
      default_decision: allow
```

- [ ] **Step 3: 创建 `test/policy/test_manifesto.py`**

```python
# ruff: noqa: S101

from pathlib import Path

import pytest

from policy.errors import PolicyLoadError
from policy.manifesto import Manifesto


class TestManifestoLoad:
    def test_load_valid_manifesto(self, manifesto_file: Path):
        manifesto = Manifesto.from_yaml(manifesto_file)
        assert manifesto.version == "1.0"
        assert manifesto.metadata.name == "test-policy"
        assert "input" in manifesto.intervention_points
        assert len(manifesto.intervention_points["input"]) == 2

    def test_load_missing_file_raises(self, tmp_path: Path):
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            Manifesto.from_yaml(missing)

    def test_load_invalid_yaml_raises_policy_load_error(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(": : : :", encoding="utf-8")
        with pytest.raises(PolicyLoadError, match="Invalid YAML"):
            Manifesto.from_yaml(bad)

    def test_load_non_mapping_raises_policy_load_error(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("- just a list", encoding="utf-8")
        with pytest.raises(PolicyLoadError, match="must be a YAML mapping"):
            Manifesto.from_yaml(bad)

    def test_load_missing_required_fields_raises(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text('version: "1.0"\n', encoding="utf-8")
        with pytest.raises(PolicyLoadError, match="Invalid manifesto schema"):
            Manifesto.from_yaml(bad)
```

- [ ] **Step 4: 运行测试验证失败（Pydantic 没有 metadata/policies 会报错）**

```bash
python -m pytest test/policy/test_manifesto.py -v
```

Expected: `test_load_missing_required_fields_raises` PASS, others pass.

- [ ] **Step 5: 验证生产 manifesto 可加载**

```bash
python -c "from policy.manifesto import Manifesto; from pathlib import Path; m = Manifesto.from_yaml(Path('policy/manifesto.yaml')); print(m.version)"
```

Expected: `1.0`

- [ ] **Step 6: Commit**

```bash
git add policy/manifesto.py policy/manifesto.yaml test/policy/test_manifesto.py
git commit -m "feat(policy): add manifesto schema with Pydantic validation"
```

---

### Task 3: 策略引擎核心

**Files:**
- Create: `policy/engine.py`
- Create: `test/policy/test_engine.py`

- [ ] **Step 1: 创建 `policy/engine.py`**

```python
"""策略引擎核心 — 加载 manifesto、执行策略链。"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from .base import BasePolicy
from .decisions import Decision, Verdict
from .manifesto import Manifesto, PolicyBinding
from .snapshots import InputSnapshot, OutputSnapshot

logger = logging.getLogger(__name__)


class PolicyEngine:
    def __init__(self, manifesto_path: Path) -> None:
        self.manifesto = Manifesto.from_yaml(manifesto_path)
        self._policies: dict[str, list[tuple[PolicyBinding, BasePolicy]]] = {}
        self._load_policies()

    def _load_policies(self) -> None:
        for point_name, bindings in self.manifesto.intervention_points.items():
            chain: list[tuple[PolicyBinding, BasePolicy]] = []
            for binding in bindings:
                policy_def = self.manifesto.policies[binding.policy]
                policy = self._instantiate_policy(policy_def.class_path)
                policy.configure(binding.config)
                chain.append((binding, policy))
            self._policies[point_name] = chain

    @staticmethod
    def _instantiate_policy(class_path: str) -> BasePolicy:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls()

    async def intervene(
        self,
        intervention_point: str,
        snapshot: InputSnapshot | OutputSnapshot,
    ) -> Decision:
        if intervention_point not in self._policies:
            logger.error("Unknown intervention point: %s", intervention_point)
            return Decision.deny(
                "unknown_intervention_point",
                message="系统策略配置异常，暂时无法处理您的请求",
            )

        bindings = self._policies[intervention_point]
        if not bindings:
            return Decision.deny(
                "no_policy_bound",
                message="系统策略配置异常，暂时无法处理您的请求",
            )

        for binding, policy in bindings:
            try:
                decision = await policy.evaluate(snapshot)
            except Exception:
                logger.exception("Policy %s raised during evaluate", policy.name)
                if policy.severity == "safety":
                    return Decision.deny(
                        "safety_policy_error",
                        message="内容安全检查暂时不可用，请求被拦截",
                    )
                # normal 策略异常 → warn 降级继续
                logger.warning("Policy %s degraded to warn", policy.name)
                continue

            if decision.verdict == Verdict.DENY:
                logger.info(
                    "policy_decision deny reason=%s policy=%s point=%s",
                    decision.reason,
                    policy.name,
                    intervention_point,
                )
                return decision

        default = bindings[-1][0].default_decision
        if default == "deny":
            return Decision.deny("default_deny", message="请求被默认策略拦截")
        return Decision.allow("chain_exhausted_default_allow")
```

- [ ] **Step 2: 创建 `test/policy/test_engine.py`**

```python
# ruff: noqa: S101

from pathlib import Path

import pytest

from policy.decisions import Verdict
from policy.engine import PolicyEngine
from policy.snapshots import InputSnapshot


def _snapshot(**kwargs) -> InputSnapshot:
    defaults = dict(user_id="u1", group_id=None, chat_type="group", text="hello")
    defaults.update(kwargs)
    return InputSnapshot(**defaults)


class TestPolicyEngineChain:
    @pytest.mark.asyncio
    async def test_chain_short_circuit_on_deny(self, manifesto_file: Path):
        """第一条策略 deny → 引擎立即返回 deny，后续不执行。"""
        engine = PolicyEngine(manifesto_file)
        decision = await engine.intervene("input", _snapshot())
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "blocked"

    @pytest.mark.asyncio
    async def test_chain_exhausted_default_allow(self, manifesto_file: Path):
        """全部 allow → 使用最后一条绑定的 default_decision。"""
        engine = PolicyEngine(manifesto_file)
        # single_chain 只有 always_allow，default_decision=allow
        decision = await engine.intervene("single_chain", _snapshot())
        assert decision.verdict == Verdict.ALLOW

    @pytest.mark.asyncio
    async def test_default_deny_kicks_in(self, tmp_path: Path):
        """default_decision=deny 时，策略链耗尽后返回 deny。"""
        yaml = """
version: "1.0"
metadata: {name: test, description: ""}
policies:
  a:
    type: builtin
    class_path: test.policy.conftest.AlwaysAllowPolicy
    description: ""
intervention_points:
  input:
    - policy: a
      config: {}
      default_decision: deny
"""
        path = tmp_path / "m.yaml"
        path.write_text(yaml, encoding="utf-8")
        engine = PolicyEngine(path)
        decision = await engine.intervene("input", _snapshot())
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "default_deny"


class TestPolicyEngineErrors:
    @pytest.mark.asyncio
    async def test_unknown_intervention_point_returns_deny(self, manifesto_file: Path):
        engine = PolicyEngine(manifesto_file)
        decision = await engine.intervene("nonexistent", _snapshot())
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "unknown_intervention_point"

    @pytest.mark.asyncio
    async def test_safety_policy_error_returns_deny(self, tmp_path: Path):
        yaml = """
version: "1.0"
metadata: {name: test, description: ""}
policies:
  boom:
    type: builtin
    class_path: test.policy.conftest.ExplodingPolicy
    description: ""
intervention_points:
  input:
    - policy: boom
      config: {severity: safety}
      default_decision: allow
"""
        path = tmp_path / "m.yaml"
        path.write_text(yaml, encoding="utf-8")
        engine = PolicyEngine(path)
        decision = await engine.intervene("input", _snapshot())
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "safety_policy_error"

    @pytest.mark.asyncio
    async def test_normal_policy_error_degrades_to_warn(self, tmp_path: Path):
        """normal 策略异常 → 降级继续，最终走 default_decision。"""
        yaml = """
version: "1.0"
metadata: {name: test, description: ""}
policies:
  boom:
    type: builtin
    class_path: test.policy.conftest.ExplodingPolicy
    description: ""
  ok:
    type: builtin
    class_path: test.policy.conftest.AlwaysAllowPolicy
    description: ""
intervention_points:
  input:
    - policy: boom
      config: {}
      default_decision: allow
    - policy: ok
      config: {}
      default_decision: allow
"""
        path = tmp_path / "m.yaml"
        path.write_text(yaml, encoding="utf-8")
        engine = PolicyEngine(path)
        decision = await engine.intervene("input", _snapshot())
        assert decision.verdict == Verdict.ALLOW
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest test/policy/test_engine.py -v
```

Expected: 全部 PASS (5 tests)

- [ ] **Step 4: Commit**

```bash
git add policy/engine.py test/policy/test_engine.py
git commit -m "feat(policy): add PolicyEngine core with chain execution and fail-closed"
```

---

### Task 4: 策略层入口 + 集成

**Files:**
- Create: `policy/__init__.py`
- Create: `policy/policies/__init__.py`

- [ ] **Step 1: 创建 `policy/__init__.py`**

```python
"""Frontier 轻量策略层。

Usage:
    from policy import engine

    decision = await engine.intervene("input", snapshot)
"""

from pathlib import Path

from .engine import PolicyEngine

_manifesto_path = Path(__file__).parent / "manifesto.yaml"
engine = PolicyEngine(_manifesto_path)
```

- [ ] **Step 2: 创建 `policy/policies/__init__.py`**

```python
"""内置策略实现。"""
```

- [ ] **Step 3: 验证单例加载**

```bash
python -c "from policy import engine; print(type(engine).__name__, engine.manifesto.version)"
```

Expected: `PolicyEngine 1.0`（可能在此时报 PolicyLoadError 如果 PolicyEngine 的 Manifesto.from_yaml 依赖 Pydantic… 实际上应该成功，因为我们还没有定义策略类，但 loading 阶段只做 manifesto 解析，不做策略类实例化… 等等，_load_policies 会实例化策略类，但策略类（AccessControlPolicy, ContentSafetyPolicy）还不存在，这会导致 ImportError！）

**在设计上这是预期行为**：`_load_policies()` 失败 → 进程无法启动（fail-fast）。先确认这能通过，因为后面 task 会创建这些策略类。我们先验证 Manifesto 本身能加载：

```bash
python -c "from policy.manifesto import Manifesto; from pathlib import Path; m = Manifesto.from_yaml(Path('policy/manifesto.yaml')); print('Manifesto OK', m.version)"
```

Expected: `Manifesto OK 1.0`

- [ ] **Step 4: Commit**

```bash
git add policy/__init__.py policy/policies/__init__.py
git commit -m "feat(policy): add module entrypoint with engine singleton"
```

---

### Task 5: AccessControlPolicy（替代 message_gateway）

**Files:**
- Create: `policy/policies/access_control.py`
- Create: `test/policy/test_access_control.py`

- [ ] **Step 1: 创建 `policy/policies/access_control.py`**

```python
"""访问控制策略 — 替代 utils.message.message_gateway()。"""

from policy.base import BasePolicy
from policy.decisions import Decision
from policy.snapshots import InputSnapshot, OutputSnapshot


class AccessControlPolicy(BasePolicy):
    name = "access_control"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        if not isinstance(snapshot, InputSnapshot):
            return Decision.allow(reason="not_applicable")

        # 第 1 层：快速放行 — @mention 或 bot 名称前缀
        if snapshot.is_at_bot or snapshot.is_bot_name_prefix:
            return Decision.allow(reason="direct_mention")

        user_id = snapshot.user_id
        group_id = snapshot.group_id
        numeric_user_id = _to_int(user_id)

        # 第 2 层：测试群组 — 不让未点名的群回复
        test_group_ids = self.config.get("test_group_ids", [])
        if group_id is not None and group_id in test_group_ids:
            return Decision.deny("test_group_no_reply", message="现在不太方便回复呢~")

        # 第 3 层：黑名单拦截
        if numeric_user_id in self.config.get("blacklist_persons", []):
            return Decision.deny("user_blacklisted", message="你已被限制使用")
        if group_id is not None and group_id in self.config.get("blacklist_groups", []):
            return Decision.deny("group_blacklisted", message="该群已被限制使用")

        # 第 4 层：白名单校验
        if self.config.get("whitelist_mode"):
            whitelist_persons = self.config.get("whitelist_persons", [])
            whitelist_groups = self.config.get("whitelist_groups", [])
            person_ok = numeric_user_id in whitelist_persons
            group_ok = group_id is not None and group_id in whitelist_groups
            # 私聊（group_id=None）只要通过用户白名单即可
            if group_id is None and not person_ok:
                return Decision.deny("not_whitelisted", message="你暂未开放此功能")
            if group_id is not None and not (person_ok or group_ok):
                return Decision.deny("not_whitelisted", message="该群暂未开放此功能")

        return Decision.allow(reason="passed_access_control")


def _to_int(value: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return hash(value) & 0x7FFFFFFF
```

- [ ] **Step 2: 创建 `test/policy/test_access_control.py`**

```python
# ruff: noqa: S101

import pytest

from policy.policies.access_control import AccessControlPolicy
from policy.decisions import Verdict
from policy.snapshots import InputSnapshot


def _snap(**overrides) -> InputSnapshot:
    defaults = dict(
        user_id="12345",
        group_id=1,
        chat_type="group",
        text="hello",
        is_at_bot=False,
        is_bot_name_prefix=False,
    )
    defaults.update(overrides)
    return InputSnapshot(**defaults)


@pytest.mark.asyncio
async def test_at_bot_is_allowed():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(is_at_bot=True)
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_bot_name_prefix_is_allowed():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(is_bot_name_prefix=True)
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_blacklist_denies():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [12345], "blacklist_groups": [], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "user_blacklisted"


@pytest.mark.asyncio
async def test_blacklist_group_denies():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [1], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "group_blacklisted"


@pytest.mark.asyncio
async def test_whitelist_mode_denies_unknown():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [99999], "whitelist_groups": [99999], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "not_whitelisted"


@pytest.mark.asyncio
async def test_whitelist_mode_allows_known_user():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [12345], "whitelist_groups": [], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_dm_allowed_when_person_whitelisted():
    """私聊时 group_id=None，只要用户在个人白名单中即可放行。"""
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [12345], "whitelist_groups": [99999], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(group_id=None, chat_type="private")
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_dm_denied_when_person_not_whitelisted():
    """私聊时 group_id=None，用户不在个人白名单中应拒绝。"""
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": True, "whitelist_persons": [99999], "whitelist_groups": [], "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = _snap(group_id=None, chat_type="private")
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.DENY


@pytest.mark.asyncio
async def test_test_group_denies():
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": [1]})
    decision = await policy.evaluate(_snap())
    assert decision.verdict == Verdict.DENY
    assert decision.reason == "test_group_no_reply"


@pytest.mark.asyncio
async def test_output_snapshot_skips():
    """非 InputSnapshot 时直接放行。"""
    from policy.snapshots import OutputSnapshot
    policy = AccessControlPolicy()
    policy.configure({"whitelist_mode": False, "blacklist_persons": [], "blacklist_groups": [], "test_group_ids": []})
    snap = OutputSnapshot(user_id="u1", group_id=None, text="response")
    decision = await policy.evaluate(snap)
    assert decision.verdict == Verdict.ALLOW
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest test/policy/test_access_control.py -v
```

Expected: 全部 PASS (9 tests)

- [ ] **Step 4: Commit**

```bash
git add policy/policies/access_control.py test/policy/test_access_control.py
git commit -m "feat(policy): add AccessControlPolicy replacing message_gateway"
```

---

### Task 6: ContentSafetyPolicy（替代 message_check + sanitize_outgoing_text）

**Files:**
- Create: `policy/policies/content_safety.py`
- Create: `test/policy/test_content_safety.py`

- [ ] **Step 1: 创建 `policy/policies/content_safety.py`**

```python
"""内容安全策略 — 替代 utils.message.message_check() 和 sanitize_outgoing_text()。"""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO
from typing import Callable

from PIL import Image

from policy.base import BasePolicy
from policy.decisions import Decision, Verdict
from policy.snapshots import InputSnapshot, OutputSnapshot

logger = logging.getLogger(__name__)

# 延迟导入避免启动时加载模型
_text_detector = None
_image_detector = None
_import_lock = asyncio.Lock()


async def _ensure_text_detector(model_name: str):
    global _text_detector
    if _text_detector is not None:
        return _text_detector
    from utils.context_check import TextCheck

    _text_detector = TextCheck(model_name=model_name)
    return _text_detector


async def _ensure_image_detector(model_name: str):
    global _image_detector
    if _image_detector is not None:
        return _image_detector
    from utils.context_check import ImageCheck

    _image_detector = ImageCheck()
    return _image_detector


class ContentSafetyPolicy(BasePolicy):
    name = "content_safety"

    def configure(self, config: dict) -> None:
        super().configure(config)
        direction = config.get("direction", "input")
        if direction == "input":
            self._handler = self._evaluate_input
        else:
            self._handler = self._evaluate_output

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:
        return await self._handler(snapshot)

    async def _evaluate_input(self, snapshot: InputSnapshot) -> Decision:
        text_model = self.config.get("text_model", "Qwen3Guard-Gen-0.6B")
        image_model = self.config.get("image_model", "Falconsai/nsfw_image_detection")

        # 文本安全检查
        if snapshot.text:
            try:
                det = await _ensure_text_detector(text_model)
                safe_label, _categories = await det.predict(snapshot.text)
            except Exception:
                logger.exception("ContentSafetyPolicy text check failed")
                # safety severity → 由引擎处理为 deny
                raise

            if safe_label == "Unsafe":
                return Decision.deny(
                    "unsafe_text_input",
                    message="检测到不安全内容，已拦截",
                    metadata={"reaction": self.config.get("unsafe_reaction", 26)},
                )
            if safe_label == "Controversial":
                return Decision.warn(
                    "controversial_text_input",
                    message="检测到争议内容",
                    metadata={"reaction": self.config.get("controversial_reaction", 212)},
                )

        # 图片安全检查（延迟加载）
        if snapshot.images:
            try:
                det = await _ensure_image_detector(image_model)
            except Exception:
                logger.exception("ContentSafetyPolicy image model init failed")
                raise

            for image_loader in snapshot.images:
                image_bytes = image_loader()
                if image_bytes is None:
                    continue
                try:
                    img = Image.open(BytesIO(image_bytes))
                    result = await det.predict(img)
                except Exception:
                    logger.exception("ContentSafetyPolicy image check failed")
                    raise
                if result == "nsfw":
                    return Decision.deny(
                        "unsafe_image_input",
                        message="检测到不安全图片，已拦截",
                        metadata={"reaction": self.config.get("unsafe_reaction", 26)},
                    )

        return Decision.allow("input_safe",
            metadata={"reaction": self.config.get("safe_reaction", 32)})

    async def _evaluate_output(self, snapshot: OutputSnapshot) -> Decision:
        if not snapshot.text:
            return Decision.allow("empty_output")

        text_model = self.config.get("text_model", "Qwen3Guard-Gen-0.6B")
        try:
            det = await _ensure_text_detector(text_model)
            safe_label, _categories = await det.predict(snapshot.text)
        except Exception:
            logger.exception("ContentSafetyPolicy output check failed")
            raise

        if safe_label == "Unsafe":
            return Decision.deny(
                "unsafe_text_output",
                message=self.config.get("block_message", "⚠️ 内容被安全策略拦截"),
            )
        return Decision.allow("output_safe")
```

- [ ] **Step 2: 创建 `test/policy/test_content_safety.py`**

```python
# ruff: noqa: S101

from unittest.mock import AsyncMock, patch

import pytest

from policy.decisions import Verdict
from policy.policies.content_safety import ContentSafetyPolicy
from policy.snapshots import InputSnapshot, OutputSnapshot


def _input_snap(**overrides) -> InputSnapshot:
    defaults = dict(user_id="u1", group_id=1, chat_type="group", text="hi")
    defaults.update(overrides)
    return InputSnapshot(**defaults)


def _output_snap(text: str) -> OutputSnapshot:
    return OutputSnapshot(user_id="u1", group_id=1, text=text)


class FakeTextDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, text: str):
        return "Safe", []


class FakeUnsafeDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, text: str):
        return "Unsafe", ["Violent"]


class FakeControversialDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, text: str):
        return "Controversial", ["Politically Sensitive Topics"]


class FakeImageDetector:
    def __init__(self):
        pass

    async def predict(self, img):
        return "normal"


class FakeNsfwImageDetector:
    def __init__(self):
        pass

    async def predict(self, img):
        return "nsfw"


@pytest.fixture(autouse=True)
def reset_module_detectors():
    import policy.policies.content_safety as cs

    cs._text_detector = None
    cs._image_detector = None
    yield
    cs._text_detector = None
    cs._image_detector = None


@pytest.mark.asyncio
async def test_input_safe_text_passes():
    with patch("policy.policies.content_safety.TextCheck", FakeTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "text_model": "dummy"})
        decision = await policy.evaluate(_input_snap(text="hello"))
        assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_input_unsafe_text_denies():
    with patch("policy.policies.content_safety.TextCheck", FakeUnsafeDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "text_model": "dummy"})
        decision = await policy.evaluate(_input_snap(text="bad stuff"))
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "unsafe_text_input"
        assert decision.metadata["reaction"] == 26


@pytest.mark.asyncio
async def test_input_controversial_text_warns():
    with patch("policy.policies.content_safety.TextCheck", FakeControversialDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input"})
        decision = await policy.evaluate(_input_snap(text="controversial"))
        assert decision.verdict == Verdict.WARN
        assert decision.metadata["reaction"] == 212


@pytest.mark.asyncio
async def test_input_nsfw_image_denies():
    with (
        patch("policy.policies.content_safety.TextCheck", FakeTextDetector),
        patch("policy.policies.content_safety.ImageCheck", FakeNsfwImageDetector),
    ):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input"})
        decision = await policy.evaluate(_input_snap(text="", images=[lambda: b"fake_image"]))
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "unsafe_image_input"


@pytest.mark.asyncio
async def test_input_safe_image_passes():
    with (
        patch("policy.policies.content_safety.TextCheck", FakeTextDetector),
        patch("policy.policies.content_safety.ImageCheck", FakeImageDetector),
    ):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input"})
        decision = await policy.evaluate(_input_snap(text="", images=[lambda: b"ok_image"]))
        assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_output_unsafe_text_denies():
    with patch("policy.policies.content_safety.TextCheck", FakeUnsafeDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "output", "block_message": "blocked!"})
        decision = await policy.evaluate(_output_snap("dangerous"))
        assert decision.verdict == Verdict.DENY
        assert decision.message == "blocked!"


@pytest.mark.asyncio
async def test_output_safe_text_passes():
    with patch("policy.policies.content_safety.TextCheck", FakeTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "output"})
        decision = await policy.evaluate(_output_snap("innocent"))
        assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_output_empty_text_passes():
    policy = ContentSafetyPolicy()
    policy.configure({"direction": "output"})
    decision = await policy.evaluate(_output_snap(""))
    assert decision.verdict == Verdict.ALLOW
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest test/policy/test_content_safety.py -v
```

Expected: 全部 PASS (8 tests)

- [ ] **Step 4: 验证策略层单例现在可以正常加载**

```bash
python -c "from policy import engine; print('Engine loaded OK, points:', list(engine._policies.keys()))"
```

Expected: `Engine loaded OK, points: ['input', 'output']`

- [ ] **Step 5: Commit**

```bash
git add policy/policies/content_safety.py test/policy/test_content_safety.py
git commit -m "feat(policy): add ContentSafetyPolicy replacing message_check and sanitize_outgoing_text"
```

---

### Task 7: 调用方适配 — 在 `plugins/agent/__init__.py` 中接入策略引擎

**Files:**
- Modify: `plugins/agent/__init__.py`

- [ ] **Step 1: 在 `plugins/agent/__init__.py` 中替换 input 阶段逻辑**

找到文件中的 Phase 1-4 段（约第 195-320 行），删去旧的 gateway + check 逻辑，替换为策略引擎调用。

在文件头部 import 区域添加：
```python
from policy import engine as policy_engine
from policy.decisions import Verdict
from policy.snapshots import InputSnapshot, OutputSnapshot
```

**修改 `handle_common` 函数**：在 `message_extract` 之后，`message_gateway` 之前的位置，插入策略引擎的 input 拦截。

具体改动：阅读 `plugins/agent/__init__.py`，将第 212-279 行（从 `text, image_downloaders, ...` 到 `match risk_check:` 结束）替换为以下逻辑：

```python
    # ── Phase 1: 快速提取文本（不下载媒体）──
    text, image_downloaders, audio_downloaders, video_downloaders = await message_extract(event.data.segments)

    quoted_images: list[bytes] = []
    if reply_seq := reply_seq_from_segments(event.data.segments):
        quote_text, quoted_images = await build_reply_context(bot, event, reply_seq, group_id, messages_db)
        if quote_text:
            text += quote_text
    if video_downloaders:
        text = f"{text}\n{' '.join('[视频]' for _ in video_downloaders)}".strip()
    if not text and not event.is_tome():
        await common.finish()

    msg_time = int(time.time() * 1000)

    # ── Phase 2: 存储消息文本 ──
    await messages_db.insert(
        time=msg_time, msg_id=event_id, user_id=int(user_id), group_id=group_id,
        user_name=user_name,
        role="user" if user_id != str(event.self_id) else "assistant",
        content=text,
    )

    messages = await messages_db.prepare_message(
        int(user_id), group_id, query_numbers=EnvConfig.QUERY_MESSAGE_NUMBERS, before_time=msg_time,
    )

    # ── Phase 3: 策略引擎 — input 介入点 ──
    bot_name_prefixes = next(
        (b.config.get("bot_name_prefixes", [])
         for point_name, chain in policy_engine._policies.items()
         if point_name == "input"
         for binding, _policy in chain
         if binding.policy == "access_control"),
        [EnvConfig.BOT_NAME],
    )

    input_snapshot = InputSnapshot(
        user_id=user_id,
        group_id=group_id,
        chat_type="group" if group_id else "private",
        text=text,
        images=[],  # 延迟下载在策略通过后由 download_media 处理
        is_at_bot=event.is_tome(),
        is_bot_name_prefix=any(text.strip().startswith(p) for p in bot_name_prefixes),
        raw_message=event.dict() if hasattr(event, "dict") else {},
    )

    input_decision = await policy_engine.intervene("input", input_snapshot)

    if input_decision.verdict == Verdict.DENY:
        if input_decision.metadata.get("reaction") and group_id:
            await bot.send_group_message_reaction(
                group_id=group_id, message_seq=event_id,
                reaction=str(input_decision.metadata["reaction"]), is_add=True,
            )
        await common.finish(input_decision.message)

    # ── Phase 4: 网关通过后下载媒体 + 内容安全判定 ──
    images, _audio, videos = await download_media(image_downloaders, audio_downloaders, video_downloaders)

    if images and EnvConfig.IMAGE_ENABLED:
        try:
            await messages_db.insert_images(msg_time=msg_time, user_id=int(user_id), group_id=group_id, images=images)
        except Exception as e:
            logger.warning("⚠️ 图片保存失败（不影响主流程）: %s", e)

    # 附带图片的二次安全检查（延迟加载 image loaders）
    delayed_loaders = [lambda b=img: b for img in images]
    if delayed_loaders:
        image_safety = await policy_engine.intervene("input", InputSnapshot(
            user_id=user_id, group_id=group_id, chat_type="group" if group_id else "private",
            text="", images=delayed_loaders,
        ))
        if image_safety.verdict == Verdict.DENY:
            if image_safety.metadata.get("reaction") and group_id:
                await bot.send_group_message_reaction(
                    group_id=group_id, message_seq=event_id,
                    reaction=str(image_safety.metadata["reaction"]), is_add=True,
                )
            await common.finish(image_safety.message)

    # warn verdict 的处理：添加 reaction
    if input_decision.verdict == Verdict.WARN and input_decision.metadata.get("reaction"):
        if group_id:
            await bot.send_group_message_reaction(
                group_id=group_id, message_seq=event_id,
                reaction=str(input_decision.metadata["reaction"]), is_add=True,
            )
```

然后删除 `_process_agent_request` 函数中第 152-154 行的 `sanitize_outgoing_text` 调用，替换为策略引擎的 output 介入点。找到：

```python
        response_content = outgoing_message_content(response["messages"][-1])
        sanitized_response = await sanitize_outgoing_text(response_content)
        if sanitized_response != response_content:
            response["messages"][-1] = SimpleNamespace(text=sanitized_response)
```

替换为：

```python
        response_content = outgoing_message_content(response["messages"][-1])
        output_snapshot = OutputSnapshot(
            user_id=context.user_id,
            group_id=context.group_id,
            text=response_content,
            agent_response_raw=str(getattr(response["messages"][-1], "text", "") or ""),
        )
        output_decision = await policy_engine.intervene("output", output_snapshot)
        if output_decision.verdict == Verdict.DENY:
            response["messages"][-1] = SimpleNamespace(text=output_decision.message)
```

同时从文件顶部的 import 中移除不再使用的 `message_gateway`、`message_check`、`sanitize_outgoing_text`：

```python
# 修改前
from utils.message import (
    download_media,
    message_check,
    message_extract,
    message_gateway,
    outgoing_message_content,
    sanitize_outgoing_text,
    send_artifacts,
    send_messages,
)

# 修改后
from utils.message import (
    download_media,
    message_extract,
    outgoing_message_content,
    send_artifacts,
    send_messages,
)
```

- [ ] **Step 2: 运行现有测试确认未破坏**

```bash
python -m pytest test/utils/agents_test.py -x -q
```

Expected: 通过的测试应该仍然通过（agents_test 可能依赖 message 模块的其他函数，确认不涉及被删除的函数）。

- [ ] **Step 3: Commit**

```bash
git add plugins/agent/__init__.py
git commit -m "refactor(agent): integrate policy engine for input and output checkpoints"
```

---

### Task 8: 清理旧代码

**Files:**
- Modify: `utils/message.py`
- Modify: `utils/configs.py`
- Modify: `env.toml`

- [ ] **Step 1: 从 `utils/message.py` 删除被替换的函数**

删除以下函数及其辅助函数/常量：
- `_message_gateway_user_id()` (第 208-213 行)
- `_message_gateway_blocked_by_access_policy()` (第 216-223 行)
- `message_gateway()` (第 558-570 行)
- `message_check()` (第 573-588 行)
- `sanitize_outgoing_text()` (第 473-484 行)
- `sanitize_outgoing_message()` (第 487-492 行)

以及 head 区的 `text_det` 和 `image_det` 模块级懒加载变量（第 26-27 行），和 `OUTPUT_RISK_BLOCKED_MESSAGE` (第 28 行) — 但需要确认它们没有被其他地方引用。

同时删除不再需要的 import：
- `from utils.configs import EnvConfig` → 保留 (其他地方仍用)
- `from utils.context_check import ImageCheck, TextCheck` → 删除 (仅被 content_safety policy 使用)

**关键：在删除前先用 `git grep` 确认这些函数/变量的引用范围。**

```bash
git grep "message_gateway" --name-only
git grep "message_check" --name-only
git grep "sanitize_outgoing_text\|sanitize_outgoing_message" --name-only
```

Expected: 只有 `utils/message.py` 和 `plugins/agent/__init__.py`（已适配）引用。

执行删除后，`utils/message.py` 保留的函数：
- `extract_message_text()` 及其辅助函数
- `download_media()` / `_resolve_media_item()`
- `message_extract()`
- `send_artifacts()`
- `outgoing_message_content()`
- `send_messages()` 及其辅助函数
- `_reply_check_*` 辅助函数（reply_check 保留）

- [ ] **Step 2: 从 `utils/configs.py` 删除已迁移的字段**

删除以下字段定义（第 90-94 行）：
```python
AGENT_WHITELIST_MODE: bool = function_list["agent_whitelist_mode"]
AGENT_WHITELIST_PERSON_LIST: list = function_list["agent_whitelist_person_list"]
AGENT_WHITELIST_GROUP_LIST: list = function_list["agent_whitelist_group_list"]
AGENT_BLACKLIST_PERSON_LIST: list = function_list["agent_blacklist_person_list"]
AGENT_BLACKLIST_GROUP_LIST: list = function_list["agent_blacklist_group_list"]
```

删除 `CONTENT_CHECK_ENABLED` (第 173 行)。

保留 `paint_*` 字段（paint 模块独立治理，暂不迁移）。

在 `reload()` 方法中删除对应的热重载逻辑（第 249-262 行的 agent access control 部分）。

- [ ] **Step 3: 从 `env.toml` 删除已迁移的字段**

从 `[function]` 节中删除：
```toml
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = [2085003190]
agent_blacklist_group_list = []
```

删除整个 `[content_check]` 节：
```toml
[content_check]
enabled = false
```

- [ ] **Step 4: 同步更新 `test/conftest.py`**

`test/conftest.py` 中的 `_ensure_env_file()` 函数构造了一个内嵌的测试 env.toml。删除其中已迁移的字段（第 88-92 行的 agent 白/黑名单，以及如果存在 content_check 节）。

- [ ] **Step 5: 更新测试文件**

运行 `test/utils/message_test.py` 中涉及 `message_gateway` 和 `message_check` 的测试。这些测试现在会失败（函数已删除）。删除以下测试函数：
- `test_message_gateway_blacklist`
- `test_message_gateway_whitelist_numeric_id`
- `test_message_gateway_whitelist_dm_allowed`
- `test_message_gateway_test_group_reply_check_does_not_mutate_messages`
- `test_message_gateway_test_group_reply_check_strips_image_data`
- `test_message_gateway_test_group_skips_casual_messages`
- `test_message_gateway_test_group_reply_check_has_group_cooldown`
- `test_message_gateway_test_group_active_group_requires_strong_signal`
- `test_message_gateway_test_group_uses_database_assistant_reply_cooldown`
- `test_message_check_text`
- `test_message_check_disabled_returns_safe`
- `test_message_check_disabled_with_images_returns_safe`
- `test_sanitize_outgoing_text_blocks_unsafe_output`
- `test_sanitize_outgoing_text_allows_controversial_output`

同时删除 `DummyTestGroupEvent` 类（第 41-55 行）和 `DummyReplyCheckFalse`、`DummyReplyCheckTrue`、`DummyReplyCheckDb` 类（第 58-77 行），以及 `patch_reply_check_prompt()` 函数（第 80-100 行）和 `clear_reply_check_state` fixture（第 103-107 行）— 这些都是 message_gateway 测试的辅助。

- [ ] **Step 6: 运行全部新老测试**

```bash
python -m pytest test/ -x -q --ignore=test/utils/database_performance_test.py
```

Expected: 全部通过（排除 database_performance_test，因为它有已知的缓慢问题）。

- [ ] **Step 7: Commit**

```bash
git add utils/message.py utils/configs.py env.toml test/conftest.py test/utils/message_test.py
git commit -m "refactor: remove legacy gateway/check/sanitize replaced by policy engine"
```

---

### Task 9: 全面测试 + 最终验证

**Files:**
- Run: 全量测试套件
- Run: 策略层自治导入验证

- [ ] **Step 1: 运行策略层测试**

```bash
python -m pytest test/policy/ -v
```

Expected: 全部 PASS (~25 tests: 4 manifesto + 5 engine + 9 access_control + 8 content_safety)

- [ ] **Step 2: 运行 message 模块剩余测试**

```bash
python -m pytest test/utils/message_test.py -v
```

Expected: 全部 PASS (留存的测试：message_extract, send_messages, markdown rendering, extractors)

- [ ] **Step 3: 运行 agent 相关测试**

```bash
python -m pytest test/utils/agents_test.py -v -x
```

Expected: 全部 PASS

- [ ] **Step 4: 验证模块导入**

```bash
python -c "
from policy import engine
from policy.decisions import Decision, Verdict
from policy.snapshots import InputSnapshot, OutputSnapshot
d = Decision.deny('test', message='blocked')
assert d.verdict == Verdict.DENY
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 5: Commit（如有残留修改）**

```bash
git status
git add -A
git diff --cached --stat
git commit -m "test(policy): verify full test suite passes with policy integration"
```

---

### 回滚方案

如生产发现问题，恢复旧代码：

1. `git revert` 最后 4 个 commit（Task 5-8）
2. 回退 `plugins/agent/__init__.py` 到旧逻辑
3. 恢复 `utils/message.py` 中删除的函数
4. 恢复 `env.toml` 和 `utils/configs.py` 中的字段

回滚后策略层文件保留（`policy/` 目录），不加载即不影响运行。
