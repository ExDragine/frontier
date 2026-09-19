# ruff: noqa: S101
"""Check actual diagnostic output and prevent mixing the two logging APIs."""

import ast
import re
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_media_failure_log_includes_exception_and_literal_braces():
    from nonebot import logger

    from utils.message import download_media

    messages = []
    sink = logger.add(lambda message: messages.append(message.record["message"]), level="WARNING")

    async def broken_download():
        raise OSError("download {image} failed at 50%")

    try:
        assert await download_media(image_items=[broken_download]) == ([], [], [])
    finally:
        logger.remove(sink)
    assert "下载媒体失败: OSError: download {image} failed at 50%" in messages


def test_loguru_calls_do_not_use_logging_percent_placeholders():
    root = Path(__file__).resolve().parents[2]
    failures = []
    for directory in ("plugins", "utils", "tools"):
        for path in (root / directory).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            aliases = {
                alias.asname or alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module in {"nonebot", "loguru"}
                for alias in node.names if alias.name == "logger"
            }
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id in aliases
                    and node.func.attr in {"trace", "debug", "info", "success", "warning", "error", "exception", "critical"}
                    and len(node.args) > 1 and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    continue
                if re.search(r"%(?:\.\d+)?[sdrf]", node.args[0].value):
                    failures.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not failures, f"Use Loguru brace placeholders: {failures}"
