"""策略引擎核心 — 加载 manifesto、执行策略链。"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

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
