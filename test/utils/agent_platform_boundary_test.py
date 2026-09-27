# ruff: noqa: S101
"""Guard the boundary between the Agent Core and platform integrations.

The existing ``utils.agents`` package is still being migrated.  Its legacy
modules currently import a few NoneBot/Alconna objects, so that check remains a
non-strict ``xfail`` during the migration.  The new ``utils.agent_protocol``
package is the first clean boundary and is checked strictly as soon as it is
present.

Once the adapters have moved out of ``utils.agents``, remove the legacy
``xfail`` and make that check strict as well.  Keeping the scan in AST space
also catches imports hidden behind ``TYPE_CHECKING`` or function bodies before
those modules are imported by a test.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_FORBIDDEN_MODULE_ROOTS = (
    "nonebot",
    "utils.alconna",
)
_FORBIDDEN_SYMBOLS = frozenset({"UniMessage", "get_bot", "MessageDatabase"})


def _is_forbidden_module(module: str) -> bool:
    """Return whether an imported module belongs to a platform-only package."""

    return any(module == root or module.startswith(f"{root}.") for root in _FORBIDDEN_MODULE_ROOTS)


def _scan_imports(path: Path, *, root: Path) -> list[str]:
    """Return stable, human-readable violations found in one Python file."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative_path = path.relative_to(root)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_name = alias.name
                imported_symbol = alias.asname or imported_name.rsplit(".", maxsplit=1)[-1]
                if _is_forbidden_module(imported_name):
                    violations.append(f"{relative_path}:{node.lineno}: import {imported_name}")
                elif imported_symbol in _FORBIDDEN_SYMBOLS:
                    violations.append(f"{relative_path}:{node.lineno}: import symbol {imported_symbol}")
            continue

        if not isinstance(node, ast.ImportFrom):
            continue

        module = ("." * node.level) + (node.module or "")
        module_is_forbidden = node.level == 0 and _is_forbidden_module(node.module or "")
        for alias in node.names:
            imported_symbol = alias.asname or alias.name
            if module_is_forbidden:
                violations.append(f"{relative_path}:{node.lineno}: from {module} import {alias.name}")
            elif alias.name in _FORBIDDEN_SYMBOLS or imported_symbol in _FORBIDDEN_SYMBOLS:
                violations.append(f"{relative_path}:{node.lineno}: from {module} import {alias.name}")

    return violations


def _scan_paths(paths: list[Path], *, root: Path) -> list[str]:
    violations: list[str] = []
    for path in paths:
        violations.extend(_scan_imports(path, root=root))
    return violations


def _format_violations(violations: list[str]) -> str:
    return "Agent Core platform imports found:\n" + "\n".join(f"- {item}" for item in violations)


def _legacy_agent_files(root: Path) -> list[Path]:
    paths = sorted((root / "utils" / "agents").rglob("*.py"))
    paths.append(root / "utils" / "agent_context.py")
    return paths


def test_agent_protocol_import_boundary_is_clean():
    """The new protocol package must stay independent of platform SDKs."""

    root = Path(__file__).resolve().parents[2]
    protocol_root = root / "utils" / "agent_protocol"
    if not protocol_root.is_dir():
        pytest.skip("utils/agent_protocol is introduced by the protocol migration")

    paths = sorted(protocol_root.rglob("*.py"))
    orchestration_module = root / "utils" / "agent_orchestration.py"
    if orchestration_module.is_file():
        paths.append(orchestration_module)
    # The compatibility bridge is the first Agent-side runtime module that
    # can be imported by a new platform adapter.  Keep its direct imports
    # clean even while the older cognitive implementation is still migrating.
    for bridge_module in ("neutral_core.py", "runtime_gateway.py"):
        bridge_path = root / "utils" / "agents" / bridge_module
        if bridge_path.is_file():
            paths.append(bridge_path)
    violations = _scan_paths(paths, root=root)
    assert not violations, _format_violations(violations)


@pytest.mark.xfail(
    strict=False,
    reason=(
        "Legacy Agent modules still contain platform imports while the P0-P2 "
        "migration is in progress; tighten this check after handlers move."
    ),
)
def test_legacy_agent_core_import_boundary_is_clean():
    """Track remaining legacy imports without blocking the first migration step."""

    root = Path(__file__).resolve().parents[2]
    violations = _scan_paths(_legacy_agent_files(root), root=root)
    assert not violations, _format_violations(violations)
