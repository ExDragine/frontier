# Frontier 轻量策略层 - 设计文档

> 状态: **待实施**
> 创建日期: 2026-06-03
> 参考: [Microsoft Agent Governance Toolkit - ACS Policy Engine](https://github.com/microsoft/agent-governance-toolkit/blob/main/policy-engine/README.md)

## 1. 概述

### 1.1 目标

在 Frontier 项目中构建一个纯 Python 的轻量策略层（Policy Layer），借鉴 Microsoft ACS Policy Engine 的设计模式，替代当前分散在多个模块中的治理逻辑，实现集中化、声明式、确定性的 agent 安全治理。

### 1.2 核心原则

| 原则 | 实现 |
|------|------|
| **无状态** | 策略引擎不保留可变状态，每次调用提供完整快照 |
| **确定性** | 同一 manifest、同一快照 → 同一判决 |
| **故障关闭 (Fail-Closed)** | safety 策略异常 → `deny`；normal 策略异常 → `warn` 降级 |
| **声明式配置** | 单一 `manifesto.yaml` 描述所有策略绑定 |

### 1.3 第一阶段范围

实现 `input` 和 `output` 两个介入点，替代以下现有代码：

| 介入点 | 替代的现有逻辑 | 源文件 |
|--------|---------------|--------|
| `input` | `message_gateway()` + `message_check()` | `utils/message.py`, `utils/context_check.py` |
| `output` | `sanitize_outgoing_text()` | `utils/message.py` |

`message_extract()`（纯数据解析）和 `reply_check()`（业务决策，非安全治理）保留在策略层之外。

### 1.4 关键决策记录

| 决策 | 结论 |
|------|------|
| 方案选择 | 方案 C：策略类 + YAML 绑定 |
| Manifesto 格式 | 单文件 `policy/manifesto.yaml` |
| 与现有代码的关系 | 替换模式 — 旧代码删除 |
| deny 行为 | 携带用户可见 message，由 LLM 发送拒绝提示 |
| images 加载 | Snapshot 中使用 `Callable[[], bytes]` 延迟加载 |
| safety 策略异常 | deny（严格故障关闭） |
| normal 策略异常 | warn（降级放行） |
| env.toml 治理字段 | 迁移后清理删除 |

---

## 2. 架构

### 2.1 目录结构

```
frontier/
  policy/                          # 新增：轻量策略层
    __init__.py                    # PolicyEngine 单例 + 便捷导入
    engine.py                      # 策略引擎核心（加载 manifesto、执行策略链）
    manifesto.py                   # YAML manifesto 解析与校验（Pydantic 模型）
    decisions.py                   # Decision 值对象
    snapshots.py                   # 快照数据类（InputSnapshot, OutputSnapshot）
    base.py                        # BasePolicy 抽象基类 + 接口
    errors.py                      # 策略异常类型
    policies/                      # 内置策略实现
      __init__.py
      access_control.py            # 访问控制策略
      content_safety.py            # 内容安全策略
    manifesto.yaml                 # 策略配置清单
```

### 2.2 数据流

```
QQ Message Event
    │
    ▼
message_extract()                      ← 保留，纯解析
    │
    ▼
PolicyEngine.intervene("input", snapshot)   ← 新入口
    │
    ├── 1. AccessControlPolicy.evaluate()
    │       ├── @mention / 名称前缀 → allow（快速放行）
    │       ├── 黑名单检查 → deny
    │       └── 白名单检查 → deny/allow
    │
    ├── 2. ContentSafetyPolicy.evaluate()
    │       ├── 文本安全检查 → deny/allow/warn
    │       └── 图片安全检查 → deny/allow/warn
    │
    ▼
[Agent 处理]                           ← 现有逻辑不变
    │
    ▼
PolicyEngine.intervene("output", snapshot)  ← 新入口
    │
    └── 3. ContentSafetyPolicy.evaluate()（output 方向）
            └── 输出文本安全过滤 → deny/allow
    │
    ▼
send_messages()                        ← 保留，纯发送
```

### 2.3 与现有代码的替换关系

```
之前（分散治理）                          之后（集中策略层）
─────────────────────────              ─────────────────────────
message.py                            policy/policies/access_control.py
  ├── message_extract()      保留        ├── AccessControlPolicy
  ├── message_gateway()     →删除→       └── (manifesto.yaml 配置)
  ├── reply_check()          保留
  ├── message_check()       →删除→    policy/policies/content_safety.py
  └── sanitize_outgoing_text() →删除→     └── ContentSafetyPolicy

context_check.py
  ├── Qwen3Guard 调用        →保留函数   (content_safety.py 通过 import 复用)
  └── NSFW detection          →保留函数
```

> **注意**: `context_check.py` 中的模型调用函数保留不动，`ContentSafetyPolicy` 通过 import 复用它们，仅改变调用路径。

---

## 3. 组件设计

### 3.1 Decision 值对象 (`policy/decisions.py`)

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"

@dataclass
class Decision:
    verdict: Verdict
    reason: str                              # 机器可读原因码
    message: Optional[str] = None            # 用户可见消息
    metadata: dict = field(default_factory=dict)

    @classmethod
    def allow(cls, reason: str = "ok") -> "Decision": ...
    @classmethod
    def deny(cls, reason: str, message: str) -> "Decision": ...
    @classmethod
    def warn(cls, reason: str, message: str) -> "Decision": ...
```

**契约**:
- `allow` 和 `warn`: 继续执行策略链中的下一条策略
- `deny`: 短路，立即返回，后续策略不执行
- `deny` **必须**携带 `message`（不允许静默拦截）
- `metadata` 用于携带 face-less 的附加数据，如 `{"reaction": 26}`

### 3.2 Snapshot 数据类 (`policy/snapshots.py`)

```python
from dataclasses import dataclass, field
from typing import Optional, Callable

@dataclass
class InputSnapshot:
    """input 介入点的完整快照"""
    user_id: str
    group_id: Optional[str]
    chat_type: str                           # "group" | "private"
    text: str
    images: list[Callable[[], bytes]] = field(default_factory=list)
    is_at_bot: bool = False
    is_bot_name_prefix: bool = False
    raw_message: dict = field(default_factory=dict)

@dataclass
class OutputSnapshot:
    """output 介入点的完整快照"""
    user_id: str
    group_id: Optional[str]
    text: str
    agent_response_raw: str = ""
```

**设计要点**:
- `images` 使用 `Callable[[], bytes]` 而非 `bytes` — 策略层只在真正检查时才触发下载
- `raw_message` 保留原始消息以备未来策略使用，初期不参与评估

### 3.3 BasePolicy 抽象基类 (`policy/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Any, Union

class BasePolicy(ABC):
    name: str = ""                           # 子类设置
    severity: str = "normal"                  # "safety" | "normal"
    config: dict[str, Any] = {}

    def configure(self, config: dict[str, Any]) -> None:
        """注入 manifesto 中的 config 节"""
        self.config = config
        self.severity = config.get("severity", self.severity)

    @abstractmethod
    async def evaluate(
        self, snapshot: Union[InputSnapshot, OutputSnapshot]
    ) -> Decision: ...
```

**子类契约**:
- 必须设置 `name`（对应 manifesto 中的 `policies.<name>`）
- `evaluate()` 必须是无状态、确定性的（给定相同输入，返回相同判决）
- `configure()` 在 `__init__` 之后、`evaluate()` 之前由引擎调用

### 3.4 Manifesto Schema (`policy/manifesto.py`)

```python
from pydantic import BaseModel
from typing import Any

class PolicyDefinition(BaseModel):
    type: str = "builtin"                   # "builtin" | "custom"
    class_path: str                          # 策略类完整路径
    description: str = ""

class PolicyBinding(BaseModel):
    policy: str                              # 策略名，引用 policies 节
    config: dict[str, Any] = {}              # 策略专用配置
    default_decision: str = "allow"          # 策略链耗尽时的默认判决

class ManifestoMetadata(BaseModel):
    name: str
    description: str = ""

class Manifesto(BaseModel):
    version: str
    metadata: ManifestoMetadata
    policies: dict[str, PolicyDefinition]
    intervention_points: dict[str, list[PolicyBinding]]

    @classmethod
    def from_yaml(cls, path: Path) -> "Manifesto": ...
```

**加载流程**:
```
import 时 → PolicyEngine.__init__()
              ├── 1. 读取 policy/manifesto.yaml
              ├── 2. Pydantic 校验结构（失败 → PolicyLoadError）
              ├── 3. 对每个 PolicyBinding 实例化对应策略类
              ├── 4. 调用 policy.configure(config) 注入配置
              └── 5. 赋值 policy.severity（覆盖默认值）
```

### 3.5 Manifesto YAML 配置 (`policy/manifesto.yaml`)

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
        whitelist_mode: true
        whitelist_persons: []
        whitelist_groups: []
        blacklist_persons: []
        blacklist_groups: []
        bot_name_prefixes:
          - "小李子"
          - "小栗子"
        test_group_id: null
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

### 3.6 PolicyEngine 核心 (`policy/engine.py`)

```python
from pathlib import Path
import importlib
import logging

logger = logging.getLogger(__name__)

class PolicyEngine:
    def __init__(self, manifesto_path: Path):
        self.manifesto = Manifesto.from_yaml(manifesto_path)
        self._policies: dict[str, list[tuple[PolicyBinding, BasePolicy]]] = {}
        self._load_policies()

    def _load_policies(self) -> None:
        """遍历 manifesto 的 intervention_points，实例化并配置策略"""
        for point_name, bindings in self.manifesto.intervention_points.items():
            chain = []
            for binding in bindings:
                policy_def = self.manifesto.policies[binding.policy]
                policy = self._instantiate_policy(policy_def.class_path)
                policy.configure(binding.config)
                chain.append((binding, policy))
            self._policies[point_name] = chain

    def _instantiate_policy(self, class_path: str) -> BasePolicy:
        """动态导入并实例化策略类"""
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls()

    async def intervene(
        self, intervention_point: str,
        snapshot: InputSnapshot | OutputSnapshot,
    ) -> Decision:
        """在指定介入点执行策略链，返回最终判决"""
        if intervention_point not in self._policies:
            logger.error(f"Unknown intervention point: {intervention_point}")
            return Decision.deny(
                "unknown_intervention_point",
                message="系统策略配置异常，暂时无法处理您的请求"
            )

        bindings = self._policies[intervention_point]
        if not bindings:
            return Decision.deny(
                "no_policy_bound",
                message="系统策略配置异常，暂时无法处理您的请求"
            )

        for binding, policy in bindings:
            try:
                decision = await policy.evaluate(snapshot)
            except Exception as e:
                logger.exception(f"Policy {policy.name} raised during evaluate")
                if policy.severity == "safety":
                    return Decision.deny(
                        "safety_policy_error",
                        message="内容安全检查暂时不可用，请求被拦截"
                    )
                else:
                    # normal 策略异常 → warn 降级放行
                    logger.warning(f"Policy {policy.name} degraded to warn")
                    continue

            if decision.verdict == Verdict.DENY:
                logger.info("policy_decision", extra={
                    "intervention_point": intervention_point,
                    "verdict": "deny",
                    "reason": decision.reason,
                    "policy": policy.name,
                })
                return decision

        # 策略链耗尽 → 使用最后一条绑定的 default_decision
        default = bindings[-1][0].default_decision
        if default == "deny":
            return Decision.deny("default_deny",
                message="请求被默认策略拦截")
        return Decision.allow(reason="chain_exhausted_default_allow")
```

### 3.7 模块入口 (`policy/__init__.py`)

```python
"""Frontier 轻量策略层

Usage:
    from policy import engine

    decision = await engine.intervene("input", snapshot)
"""

from pathlib import Path
from .engine import PolicyEngine

# 全局单例 — 进程启动时加载，fail-fast
_manifesto_path = Path(__file__).parent / "manifesto.yaml"
engine = PolicyEngine(_manifesto_path)
```

**设计要点**:
- 模块级单例 `engine`，各处 `from policy import engine` 使用同一实例
- Manifesto 加载在 import 时完成，YAML 语法错误直接导致 ImportError（fail-fast）
- `engine` 暴露为模块公共 API，其余类通过 `policy.decisions`、`policy.snapshots` 等子模块导入

### 3.8 策略实现

#### 3.8.1 AccessControlPolicy (`policy/policies/access_control.py`)

评估顺序:

1. **快速放行**: `is_at_bot` 或 `is_bot_name_prefix` → 直接 `allow`
2. **测试群组**: `group_id == test_group_id` → `deny`（不给未点名测试群回复）
3. **黑名单**: `user_id` 或 `group_id` 在黑名单 → `deny`
4. **白名单**: 白名单模式下，不在白名单 → `deny`
5. **默认**: `allow`

**severity**: `normal`（访问控制异常时降级放行，不影响服务可用性）

#### 3.8.2 ContentSafetyPolicy (`policy/policies/content_safety.py`)

通过 `config.direction` 区分行为:

| direction | 行为 | 来源 |
|-----------|------|------|
| `input` | 文本安全 + 图片安全检测 → `deny`/`allow`/`warn` | 替代 `message_check()` |
| `output` | 输出文本安全检测 → `deny`/`allow` | 替代 `sanitize_outgoing_text()` |

**依赖**: 复用 `utils/context_check.py` 中的模型调用函数（`check_text_safety()`, `check_image_safety()`）。

**severity**: `safety`（安全检查异常时严格 deny，不容忍静默放行）

### 3.9 调用方适配 (`plugins/agent/__init__.py`)

```python
from policy import engine
from policy.snapshots import InputSnapshot, OutputSnapshot
from policy.decisions import Verdict

# === 输入阶段 ===
snapshot = InputSnapshot(
    user_id=message_event.get_user_id(),
    group_id=message_event.group_id,
    chat_type="group" if message_event.is_group else "private",
    text=extracted_text,
    images=[lambda url=url: download_media(url) for url in pending_urls],
    is_at_bot=is_at,
    is_bot_name_prefix=has_prefix,
    raw_message=event.dict(),
)

decision = await engine.intervene("input", snapshot)

if decision.verdict == Verdict.DENY:
    # LLM 发送拒绝提示
    await send_message(decision.message)
    if decision.metadata.get("reaction"):
        await add_reaction(decision.metadata["reaction"])
    return

if decision.verdict == Verdict.WARN:
    if decision.metadata.get("reaction"):
        await add_reaction(decision.metadata["reaction"])
    # 继续处理，可选地将 warning 注入 agent context

# === Agent 处理 ===
response = await f_cognitive.chat_agent(...)

# === 输出阶段 ===
output_snapshot = OutputSnapshot(
    user_id=user_id,
    group_id=group_id,
    text=response_text,
    agent_response_raw=response_raw,
)

output_decision = await engine.intervene("output", output_snapshot)

if output_decision.verdict == Verdict.DENY:
    await send_message(output_decision.message)
    return

# 正常发送
await send_messages(response.messages)
```

### 3.10 错误处理与故障关闭

```
                    ┌─────────────────┐
                    │ policy.evaluate()│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ 抛出异常？       │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼                             ▼
         是                               否
              │                             │
    ┌─────────▼─────────┐         ┌────────▼────────┐
    │ severity=="safety"?│         │ 返回 Decision    │
    └─────────┬─────────┘         └─────────────────┘
              │
    ┌─────────┼─────────┐
    ▼                   ▼
  是                   否
    │                   │
┌───▼───┐         ┌────▼────┐
│ deny  │         │  warn   │
│ (拦截) │         │ (降级放行)│
└───────┘         └─────────┘
```

**三条铁律**:
1. 任何异常 → 必须显式处理（不允许静默吞异常）
2. 未知状态 → deny（未注册介入点、无策略绑定 → deny）
3. deny 必须携带 `message`（用户可见，不允许静默拦截）

---

## 4. env.toml 迁移映射

| env.toml 字段 | manifesto 路径 | 备注 |
|---------------|---------------|------|
| `AGENT_WHITELIST_MODE` | `intervention_points.input[0].config.whitelist_mode` | |
| `AGENT_WHITELIST_PERSON_LIST` | `intervention_points.input[0].config.whitelist_persons` | |
| `AGENT_WHITELIST_GROUP_LIST` | `intervention_points.input[0].config.whitelist_groups` | |
| `AGENT_BLACKLIST_PERSON_LIST` | `intervention_points.input[0].config.blacklist_persons` | |
| `AGENT_BLACKLIST_GROUP_LIST` | `intervention_points.input[0].config.blacklist_groups` | |
| `AGENT_REPLY_PREFIX` | `intervention_points.input[0].config.bot_name_prefixes` | |
| `AGENT_TEST_GROUP_ID` | `intervention_points.input[0].config.test_group_id` | |
| `CONTENT_CHECK_ENABLED` | 从 input 链中移除 `content_safety` 策略即禁用 | 不需要单独的开关字段 |

迁移完成后，从 `utils/configs.py` 和 `env.toml` 中删除以上字段。

---

## 5. 测试策略

### 5.1 单元测试 (`tests/policy/`)

```
tests/policy/
  test_decisions.py          # Decision 工厂方法
  test_manifesto.py          # YAML 加载、校验、字段缺失报错
  test_engine.py             # 策略链执行、短路、异常降级
  test_access_control.py     # 黑白名单、@mention 放行、边界条件
  test_content_safety.py     # Mock Qwen3Guard 返回值的各种场景
```

**核心契约测试** (`test_engine.py`):

| 测试用例 | 验证点 |
|---------|--------|
| `test_chain_short_circuit_on_deny` | 第一条策略 deny → 后续策略不执行 |
| `test_safety_policy_error_returns_deny` | safety 策略抛异常 → deny |
| `test_normal_policy_error_returns_warn` | normal 策略抛异常 → warn 降级 |
| `test_unknown_intervention_point_returns_deny` | 未注册介入点 → deny |
| `test_chain_exhausted_uses_default_decision` | 全部 allow → default_decision |
| `test_images_not_downloaded_when_denied_early` | 早期 deny 时延迟图片不会被下载 |

### 5.2 集成测试

复用现有 `nonebug` + `pytest` 框架:

| 测试用例 | 验证点 |
|---------|--------|
| `test_blacklisted_user_receives_deny_message` | 黑名单用户收到 DENY 提示 |
| `test_whitelist_group_passes_input_policy` | 白名单群组正常放行 |
| `test_unsafe_output_blocked_before_send` | Unsafe 输出被 output 策略拦截 |

---

## 6. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 替换 message_gateway 后行为不一致 | 使用特性开关 `POLICY_ENGINE_ENABLED`，先内测再全量切换 |
| Qwen3Guard 调用路径变化导致行为差异 | ContentSafetyPolicy 复用现有 `context_check.py` 函数，不改模型代码 |
| YAML 语法错误导致服务无法启动 | Pydantic 校验 + Fail-fast，启动阶段即暴露问题 |
| 清理 env.toml 时误删其他配置 | `git diff` 逐字段确认 |
| ContentSafetyPolicy 误杀率高 | 初期只在测试群启用，调优阈值后再全量 |

---

## 7. 未来扩展（第二阶段+）

完成第一阶段并验证架构后，可扩展到其余介入点：

| 介入点 | 潜在策略 | 优先级 |
|--------|---------|--------|
| `pre_tool_call` | 工具权限控制（按用户/群组限制敏感工具） | 高 |
| `post_tool_call` | 工具结果安全过滤 + IFC 标签传播 | 中 |
| `pre_model_call` | 系统提示词完整性校验 + Token 预算控制 | 中 |
| `post_model_call` | 结构化输出格式校验 + PII 泄露检测 | 中 |
| `agent_startup` | 启动依赖检查（MCP 连接、模型可用性） | 低 |
| `agent_shutdown` | 资源清理确认 + 会话存档完整性 | 低 |

---
