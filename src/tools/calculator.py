"""Safe arithmetic evaluator.

We deliberately do NOT use `eval()`. Instead we parse the expression with
`ast` and walk it, allowing only numeric literals, a fixed set of binary and
unary operators, and a small whitelist of math functions. Anything else
raises ValueError.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Any, Dict


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_ALLOWED_FUNCS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        if name not in _ALLOWED_FUNCS:
            raise ValueError(f"Function not allowed: {name}")
        args = [_eval_node(a) for a in node.args]
        return _ALLOWED_FUNCS[name](*args)
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculator(expression: str) -> Dict[str, Any]:
    """Evaluate an arithmetic expression and return a structured result."""
    if not isinstance(expression, str) or not expression.strip():
        return {"ok": False, "error": "expression must be a non-empty string"}
    try:
        tree = ast.parse(expression, mode="eval")
        value = _eval_node(tree)
    except (ValueError, SyntaxError, ZeroDivisionError, TypeError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "expression": expression, "result": value}
