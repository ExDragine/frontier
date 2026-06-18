# ruff: noqa: S101

import pytest

# ── safe_eval ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("1 + 2", 3.0),
        ("3 - 1", 2.0),
        ("4 * 5", 20.0),
        ("10 / 2", 5.0),
        ("2 ** 3", 8.0),
        ("-5", -5.0),
        ("-1 + 3", 2.0),
        ("+5", 5.0),
        ("1 + +2", 3.0),
        ("(1 + 2) * 3", 9.0),
        ("2 ** 3 + 1", 9.0),
        ("10 / 3", 10 / 3),
        ("0.1 + 0.2", 0.1 + 0.2),
    ],
)
def test_safe_eval_valid_expressions(load_tool_module, expr, expected):
    mod = load_tool_module("calculator")
    assert mod.safe_eval(expr) == expected


@pytest.mark.parametrize(
    ("expr", "exc"),
    [
        ("__import__('os')", ValueError),
        ("xyz", ValueError),
        ("[1, 2]", ValueError),
        ('"hello"', ValueError),
        ("lambda x: x", ValueError),
    ],
)
def test_safe_eval_rejects_unsafe_expressions(load_tool_module, expr, exc):
    mod = load_tool_module("calculator")
    with pytest.raises(exc):
        mod.safe_eval(expr)


def test_safe_eval_syntax_error(load_tool_module):
    mod = load_tool_module("calculator")
    with pytest.raises(SyntaxError):
        mod.safe_eval("1 +")


# ── simple_calculator ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_simple_calculator_returns_result(load_tool_module):
    mod = load_tool_module("calculator")
    result = await mod.simple_calculator("2 + 3")
    assert result == "🧮 计算结果: 2 + 3 = 5.0"


@pytest.mark.asyncio
async def test_simple_calculator_returns_error_on_bad_input(load_tool_module):
    mod = load_tool_module("calculator")
    result = await mod.simple_calculator("x + 1")
    assert result.startswith("❌ 计算失败:")
