import re
from typing import List, Tuple, Optional
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

_x = sp.Symbol("x")
_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)
_EQ_RE = re.compile(r"(.+?)=(.+)")


def _to_sympy(expr: str) -> sp.Expr:
    expr = expr.strip().replace("^", "**")
    return parse_expr(expr, local_dict={"x": _x}, transformations=_TRANSFORMS)


def _parse_equation(eq: str) -> Optional[Tuple[sp.Expr, sp.Expr]]:
    eq_clean = re.sub(r"\s+", "", eq)
    m = _EQ_RE.search(eq_clean)
    if not m:
        return None
    try:
        left = _to_sympy(m.group(1))
        right = _to_sympy(m.group(2))
        return left, right
    except Exception:
        return None


def _equiv(eq1: str, eq2: str) -> Tuple[bool, str]:
    """
    Check if two equations are equivalent.
    First tries symbolic simplification; falls back to numeric sampling.
    Uses SymPy (no eval) for safe expression evaluation.
    """
    p1 = _parse_equation(eq1)
    p2 = _parse_equation(eq2)
    if not p1 or not p2:
        return False, "equation_not_supported"

    l1, r1 = p1
    l2, r2 = p2

    # Symbolic check: (l1 - r1) == (l2 - r2) iff they represent the same equation
    try:
        diff = sp.simplify((l1 - r1) - (l2 - r2))
        if diff == 0:
            return True, "equivalent"
    except Exception:
        pass

    # Numeric fallback across 10 test points
    test_xs = [-5.0, -3.0, -1.0, 0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0]
    tol = 1e-6
    try:
        for xv in test_xs:
            r_eq1 = float((l1 - r1).subs(_x, xv))
            r_eq2 = float((l2 - r2).subs(_x, xv))
            eq1_sat = abs(r_eq1) < tol
            eq2_sat = abs(r_eq2) < tol
            if eq1_sat != eq2_sat:
                return False, f"mismatch_at_x={xv}"
        return True, "equivalent"
    except Exception:
        return False, "eval_failed"


def extract_equations_from_steps(answer: str) -> List[str]:
    """
    Extract equations from step-by-step answers.
    Supports separators: '->', newlines, and chained '='.
    """
    parts = re.split(r"(?:->|\n)+", answer)
    eqs: List[str] = []
    for p in parts:
        p = p.strip()
        if "=" in p:
            m = _EQ_RE.search(re.sub(r"\s+", "", p))
            if m:
                eqs.append(p)
    return eqs


def check_step_consistency(answer: str) -> Tuple[int, str]:
    """
    Returns:
      (1, 'steps_consistent') if all consecutive equations are equivalent,
      (0, note) otherwise.
    """
    eqs = extract_equations_from_steps(answer)
    if len(eqs) < 2:
        return 0, "not_enough_equations"

    for i in range(len(eqs) - 1):
        ok, note = _equiv(eqs[i], eqs[i + 1])
        if not ok:
            return 0, f"step_{i}_to_{i+1}_invalid:{note}"
    return 1, "steps_consistent"
