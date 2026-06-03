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

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:  # noqa: ARG002
        return Decision.allow(reason="always")


class AlwaysDenyPolicy(BasePolicy):
    name = "always_deny"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:  # noqa: ARG002
        return Decision.deny(reason="blocked", message="访问被拒绝")


class ExplodingPolicy(BasePolicy):
    name = "exploding"

    async def evaluate(self, snapshot: InputSnapshot | OutputSnapshot) -> Decision:  # noqa: ARG002
        raise RuntimeError("boom")
