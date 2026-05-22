# ruff: noqa: S101

import ast
from pathlib import Path


def _is_content_and_artifact_tool(function: ast.AsyncFunctionDef) -> bool:
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if not (
            isinstance(decorator.func, ast.Name)
            and decorator.func.id == "tool"
            or isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "tool"
        ):
            continue
        for keyword in decorator.keywords:
            if (
                keyword.arg == "response_format"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "content_and_artifact"
            ):
                return True
    return False


def _uses_stage_artifact_response(function: ast.AsyncFunctionDef) -> bool:
    return any(isinstance(node, ast.Name) and node.id == "stage_artifact_response" for node in ast.walk(function))


def test_artifact_tools_return_direct_artifacts_without_staged_handoff():
    repo_root = Path(__file__).resolve().parents[2]
    offenders = []

    for path in sorted((repo_root / "tools").glob("*.py")):
        module_name = path.stem
        if module_name in {"artifact_bridge"} or module_name.startswith("__"):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.AsyncFunctionDef) and _is_content_and_artifact_tool(node):
                if _uses_stage_artifact_response(node):
                    offenders.append(f"{module_name}.{node.name}")

    assert offenders == []
