import re
from typing import List, Tuple, Optional

_EQ_RE = re.compile(r"(.+?)=(.+)")
_ALLOWED = re.compile(r"^[0-9x\+\-\*\/\.\(\)]+$")

def _normalize_expr(s: str) -> str:
    return s.replace(" ", "")

def _implicit_multiply_fix(s: str) -> str:
    # 3(x-2) -> 3*(x-2), x(x+1)->x*(x+1), )( -> )*(
    s = re.sub(r"(\d)(\()", r"\1*\2", s)
    s = re.sub(r"(x)(\()", r"\1*\2", s)
    s = re.sub(r"(\))(\()", r"\1*\2", s)
    return s

def _safe_eval(expr: str, x: float) -> float:
    expr = expr.replace("x", f"({x})")
    return float(eval(expr, {"__builtins__": {}}, {}))

def _parse_equation(eq: str) -> Optional[Tuple[str, str]]:
    eq = _implicit_multiply_fix(_normalize_expr(eq))
    m = _EQ_RE.search(eq)
    if not m:
        return None
    left, right = m.group(1), m.group(2)
    if not _ALLOWED.fullmatch(left) or not _ALLOWED.fullmatch(right):
        return None
    return left, right

def _equiv(eq1: str, eq2: str) -> Tuple[bool, str]:
    """
    Numeric equivalence check: sample multiple x values and compare LHS-RHS.
    If both equations are equivalent, their residual functions should match.
    """
    p1 = _parse_equation(eq1)
    p2 = _parse_equation(eq2)
    if not p1 or not p2:
        return False, "equation_not_supported"

    l1, r1 = p1
    l2, r2 = p2

    test_xs = [-3.0, -1.0, 0.5, 2.0, 5.0]
    try:
        for x in test_xs:
            f1 = _safe_eval(l1, x) - _safe_eval(r1, x)
            f2 = _safe_eval(l2, x) - _safe_eval(r2, x)
            if abs(f1 - f2) > 1e-6:
                return False, f"mismatch_at_x={x}"
        return True, "equivalent"
    except Exception:
        return False, "eval_failed"

def extract_equations_from_steps(answer: str) -> List[str]:
    """
    Extract equations from step-by-step answers.
    Supports separators like '->', newlines, and chained '='.
    """
    # split steps
    parts = re.split(r"(?:->|\n)+", answer)
    eqs: List[str] = []
    for p in parts:
        p = p.strip()
        if "=" in p:
            # take the first equation-looking substring
            m = _EQ_RE.search(p.replace(" ", ""))
            if m:
                # reconstruct eq substring from normalized
                eqs.append(p)
    return eqs

def check_step_consistency(answer: str) -> Tuple[int, str]:
    """
    Returns:
      step_ok: 1 if all consecutive equations are equivalent, else 0
      note: explanation
    """
    eqs = extract_equations_from_steps(answer)
    if len(eqs) < 2:
        return 0, "not_enough_equations"

    for i in range(len(eqs) - 1):
        ok, note = _equiv(eqs[i], eqs[i + 1])
        if not ok:
            return 0, f"step_{i}_to_{i+1}_invalid:{note}"
    return 1, "steps_consistent"
