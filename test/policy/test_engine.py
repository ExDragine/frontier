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
