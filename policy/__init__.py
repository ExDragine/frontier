"""Frontier 轻量策略层。

Usage:
    from policy import engine

    decision = await engine.intervene("input", snapshot)
"""

from pathlib import Path

from .engine import PolicyEngine

_manifesto_path = Path(__file__).parent / "manifesto.yaml"
engine = PolicyEngine(_manifesto_path)
