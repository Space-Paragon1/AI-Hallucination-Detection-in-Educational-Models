import re
from typing import Tuple, Optional
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

_x = sp.Symbol("x")
_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

_EQ_RE = re.compile(r"(.+?)=(.+)")


def _extract_equation(text: str) -> Optional[str]:
    """Extract the math equation from question text, stripping prose prefixes."""
    if ":" in text:
        text = text.rsplit(":", 1)[1]
    text = re.sub(r"(?i)^(solve|find|simplify|evaluate|compute)\b\s*", "", text.strip())
    text = re.sub(r"(?i)^for\s+[a-z]\s*:\s*", "", text.strip())
    text = text.strip()
    if "=" in text:
        return text
    return None


def _to_sympy(expr: str) -> sp.Expr:
    """Safely parse an expression string to SymPy using parse_expr (no eval)."""
    expr = expr.strip().replace("^", "**")
    return parse_expr(
        expr,
        local_dict={"x": _x},
        transformations=_TRANSFORMS,
    )


def simple_linear_equation_plug_in(question: str, x_value: float) -> Tuple[bool, str]:
    """
    Verifies an algebra answer by substituting the claimed x_value
    into the original equation and checking LHS == RHS.

    Uses SymPy parse_expr (no eval) for safe expression parsing.
    Supports multi-variable-style expressions but solves for x only.
    """
    eq_text = _extract_equation(question)
    if not eq_text:
        return False, "no_equation_found"

    m = _EQ_RE.search(eq_text)
    if not m:
        return False, "no_equation_found"

    left_str = m.group(1).strip()
    right_str = m.group(2).strip()

    try:
        left_expr = _to_sympy(left_str)
        right_expr = _to_sympy(right_str)
    except Exception:
        return False, "parse_failed"

    try:
        lv = float(left_expr.subs(_x, x_value))
        rv = float(right_expr.subs(_x, x_value))
        ok = abs(lv - rv) < 1e-6
        if ok:
            return True, "plug_in_ok"
        return False, f"plug_in_failed: {lv:.4f} != {rv:.4f}"
    except Exception:
        return False, "eval_failed"
