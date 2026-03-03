"""Safe formula evaluation for legacy despiece expressions."""

from __future__ import annotations

import ast
import logging
import operator
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class FormulaError(ValueError):
    """Raised when a formula cannot be evaluated safely."""


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Num):  # pragma: no cover - for older Python ASTs
        return float(node.n)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return float(_ALLOWED_UNARYOPS[type(node.op)](_safe_eval(node.operand)))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return float(_ALLOWED_BINOPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right)))
    raise FormulaError(f"Nodo AST no permitido: {type(node).__name__}")


def evaluar_formula(formula: str, variables: Dict[str, Any]) -> float:
    """
    Evalua una formula reemplazando variables y calculando el resultado.

    Args:
        formula: "([Ancho]+[Alto])*2" o "(ancho+alto)*2"
        variables: {'Ancho': 1200, 'Alto': 1500, 'Cantidad': 2}

    Returns:
        Resultado numerico de la formula.
    """
    if formula is None:
        return 0.0

    expr = str(formula).strip()
    if not expr:
        return 0.0

    # Mapeo de variables (case-insensitive)
    var_map = {
        'ancho': 'Ancho',
        'alto': 'Alto', 
        'cantidad': 'Cantidad',
        'hojas': 'Cantidad',
    }
    variables_ci = {str(k).lower(): v for k, v in variables.items()}

    def _replace_var(match: re.Match) -> str:
        key = match.group(1).strip()
        value = variables.get(key, variables_ci.get(key.lower()))
        if value is None:
            raise FormulaError(f"Variable desconocida: {key}")
        return str(value)

    try:
        # Reemplazar variables con corchetes: [Ancho], [Alto]
        expr = re.sub(r"\[([A-Za-z0-9_]+)\]", _replace_var, expr)
        
        # Reemplazar variables sin corchetes: ancho, alto, hojas
        for var_lower, var_proper in var_map.items():
            if var_lower in expr.lower():
                value = variables.get(var_proper, variables_ci.get(var_lower))
                if value is not None:
                    expr = re.sub(r'\b' + var_lower + r'\b', str(value), expr, flags=re.IGNORECASE)
        
        expr = expr.replace(",", ".")
        expr = re.sub(r"\s+", "", expr)
        parsed = ast.parse(expr, mode="eval")
        return _safe_eval(parsed)
    except FormulaError:
        raise
    except Exception as exc:
        logger.exception("Error evaluando formula %s", formula)
        raise FormulaError(f"Formula invalida: {formula}") from exc
