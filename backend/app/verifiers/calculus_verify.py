import re
from typing import Tuple, Optional
import sympy as sp

x = sp.Symbol("x")

# Basic patterns to detect task type
DERIV_PAT = re.compile(r"(differentiate|derivative|d/dx|dy/dx)", re.I)
INTEG_PAT = re.compile(r"(integrate|integral|∫)", re.I)
LIMIT_PAT = re.compile(r"(limit|lim)", re.I)

def _clean(s: str) -> str:
    return s.strip()

def _extract_final_expr(answer: str) -> Optional[str]:
    """
    Try to extract a final expression from model answer.
    Supports:
      - 'final answer: ...'
      - 'Answer: ...'
      - 'y = ...' or 'f(x) = ...'
    Falls back to last line.
    """
    a = answer.strip()

    m = re.search(r"(?:final\s*answer|answer)\s*[:is]*\s*(.+)$", a, re.I | re.M)
    if m:
        return m.group(1).strip()

    m = re.search(r"(?:y|f\(x\)|g\(x\))\s*=\s*(.+)$", a, re.I | re.M)
    if m:
        return m.group(1).strip()

    # last line fallback
    lines = [ln.strip() for ln in a.splitlines() if ln.strip()]
    if lines:
        return lines[-1]
    return None

def _to_sympy(expr: str) -> sp.Expr:
    """
    Convert a string expression into a SymPy expression.
    Handles '^' -> '**' and common function names.
    """
    expr = expr.replace("^", "**")
    # allow implicit multiplication like 3x -> 3*x
    expr = re.sub(r"(\d)(x)", r"\1*\2", expr)
    expr = re.sub(r"(x)(\d)", r"\1*\2", expr)
    return sp.sympify(expr, locals={"x": x})

def _equiv_expr(e1: sp.Expr, e2: sp.Expr) -> bool:
    """
    Check if expressions are equivalent by simplification.
    """
    try:
        return sp.simplify(e1 - e2) == 0
    except Exception:
        return False

def _extract_prompt_expression(question: str, kind: str) -> Optional[str]:
    """
    Extract the target expression from a calculus prompt.
    Very lightweight. Works best if question contains something like:
      - 'Differentiate: x^2 + 3x'
      - 'Integrate: 2x'
      - 'Find lim x->0 (sin x)/x'
    """
    q = question.strip()

    if kind == "derivative":
        # take text after ':' if present
        if ":" in q:
            return q.split(":", 1)[1].strip()
    if kind == "integral":
        if ":" in q:
            return q.split(":", 1)[1].strip()

    if kind == "limit":
        # try to extract lim_{x->a} (...) or "lim x->a (...)"
        m = re.search(r"lim(?:it)?\s*(?:_{\s*x\s*->\s*([-\d\.]+)\s*})?\s*(.*)$", q, re.I)
        if m:
            return m.group(2).strip()

    # fallback: last token-ish chunk
    return None

def detect_calc_kind(question: str) -> str:
    q = question.lower()
    if LIMIT_PAT.search(q):
        return "limit"
    if INTEG_PAT.search(q):
        return "integral"
    if DERIV_PAT.search(q):
        return "derivative"
    # heuristic: presence of "∫" indicates integral
    if "∫" in question:
        return "integral"
    return "unknown"

def verify_calculus(question: str, answer: str) -> Tuple[int, str]:
    """
    Returns (ok, note):
      ok=1 if verified, else 0
    """
    kind = detect_calc_kind(question)
    final_expr_str = _extract_final_expr(answer)
    if kind == "unknown":
        return 0, "calc_kind_unknown"
    if not final_expr_str:
        return 0, "no_final_expression"

    try:
        final_expr = _to_sympy(final_expr_str)
    except Exception:
        return 0, "final_expr_parse_failed"

    if kind in ("derivative", "integral"):
        target_str = _extract_prompt_expression(question, kind)
        if not target_str:
            return 0, "prompt_expr_missing"

        try:
            target_expr = _to_sympy(target_str)
        except Exception:
            return 0, "prompt_expr_parse_failed"

        if kind == "derivative":
            # verify: d/dx (original) == claimed
            claimed = final_expr
            true_deriv = sp.diff(target_expr, x)
            ok = _equiv_expr(claimed, true_deriv)
            return (1, "derivative_verified") if ok else (0, "derivative_mismatch")

        if kind == "integral":
            # verify: d/dx (claimed antiderivative) == integrand
            antideriv = final_expr
            recovered = sp.diff(antideriv, x)
            ok = _equiv_expr(recovered, target_expr)
            return (1, "integral_verified") if ok else (0, "integral_mismatch")

    if kind == "limit":
        # For limits, we need a point a. We'll try common forms x->0, x->1 etc.
        m = re.search(r"x\s*->\s*([-\d\.]+)", question.replace(" ", ""))
        a = 0.0
        if m:
            try:
                a = float(m.group(1))
            except Exception:
                a = 0.0

        # extract expression inside parentheses if possible
        expr_part = _extract_prompt_expression(question, "limit")
        if not expr_part:
            return 0, "limit_expr_missing"

        try:
            expr = _to_sympy(expr_part)
        except Exception:
            return 0, "limit_expr_parse_failed"

        try:
            true_lim = sp.limit(expr, x, a)
        except Exception:
            return 0, "limit_symbolic_failed"

        # claimed final expression should be numeric
        try:
            claimed_val = sp.N(final_expr)
            ok = sp.simplify(claimed_val - true_lim) == 0
            return (1, "limit_verified") if ok else (0, "limit_mismatch")
        except Exception:
            return 0, "limit_claim_parse_failed"

    return 0, "unhandled_case"
        