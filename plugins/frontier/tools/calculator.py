# 安全计算表达式
import ast
import operator as op

from langchain_core.tools import tool
from nonebot import logger

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def safe_eval(expr: str) -> float:
    """使用 AST 安全解析数学表达式，仅支持+ - * / ** 和负号"""
    node = ast.parse(expr, mode="eval").body

    def _eval(n):
        # Python 3.8+: ast.Constant, Python <3.8: ast.Num
        if isinstance(n, ast.Constant):
            if isinstance(n.value, int | float):
                return n.value
            else:
                raise ValueError(f"Unsupported constant: {n.value}")
        if isinstance(n, ast.Constant):
            return n.n
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp):
            return OPS[type(n.op)](_eval(n.operand))
        raise ValueError(f"Unsupported expression: {n}")

    result = _eval(node)
    if not isinstance(result, int | float):
        raise ValueError(f"Expression did not evaluate to a number: {result!r}")
    return float(result)


@tool(response_format="content")
async def simple_calculator(expression: str) -> str:
    """执行简单的数学运算
    Args:
        expression: 数学表达式
    Returns:
        计算结果
    """
    try:
        result = safe_eval(expression)
        return f"🧮 计算结果: {expression} = {result}"
    except Exception as e:
        logger.error("Calc error", exc_info=e)
        return f"❌ 计算失败: {e}"
