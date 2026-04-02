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

DERIV_PAT = re.compile(r"(differentiate|derivative|d/dx|dy/dx)", re.I)
INTEG_PAT = re.compile(r"(integrate|integral|∫|compute\s*:?\s*∫)", re.I)
LIMIT_PAT = re.compile(r"(limit|lim\b)", re.I)


def _to_sympy(expr: str) -> sp.Expr:
    """Robustly parse a string to SymPy expression using parse_expr (no eval)."""
    expr = expr.strip()
    expr = expr.replace("^", "**")
    expr = re.sub(r"\bsqrt\s*\(", "sqrt(", expr)
    return parse_expr(
        expr,
        local_dict={"x": _x, "e": sp.E, "pi": sp.pi},
        transformations=_TRANSFORMS,
    )


def _equiv_expr(e1: sp.Expr, e2: sp.Expr) -> bool:
    """Check symbolic equivalence, including trig identities."""
    try:
        diff = sp.simplify(e1 - e2)
        if diff == 0:
            return True
        if sp.trigsimp(diff) == 0:
            return True
        return False
    except Exception:
        return False


def _extract_final_expr(answer: str) -> Optional[str]:
    """
    Extract the final claimed expression from the model answer.
    Priority: 'Answer: ...' > 'f(x) = ...' > last '-> ...' > last line.
    """
    a = answer.strip()

    m = re.search(r"(?:final\s*answer|answer)\s*[:=is]*\s*(.+?)(?:\n|$)", a, re.I | re.M)
    if m:
        return m.group(1).strip()

    m = re.search(r"(?:y|f\(x\)|g\(x\))\s*=\s*(.+?)(?:\n|$)", a, re.I | re.M)
    if m:
        return m.group(1).strip()

    m = re.search(r"->\s*(?:Answer:\s*)?(.+?)(?:\n|$)", a, re.I | re.M)
    if m:
        return m.group(1).strip()

    lines = [ln.strip() for ln in a.splitlines() if ln.strip()]
    return lines[-1] if lines else None


def _extract_prompt_expression(question: str, kind: str) -> Optional[str]:
    """
    Extract the target expression from a calculus question.
    Handles 'Differentiate: expr', 'd/dx (expr)', '∫ expr dx', 'lim x->a expr'.
    """
    q = question.strip()

    if kind in ("derivative", "integral"):
        if ":" in q:
            part = q.split(":", 1)[1].strip()
            # Strip 'd/dx' wrapper
            part = re.sub(r"d/dx\s*[\(\[]?", "", part).strip().rstrip(")]")
            # Strip integral symbol and dx
            part = re.sub(r"∫|dx\s*$|d[a-z]\s*$", "", part).strip()
            # Strip definite integral bounds like _{0}^{1}
            part = re.sub(r"_?\{?-?[\d\.]+\}?\s*\^?\{?-?[\d\.]+\}?", "", part).strip()
            return part if part else None

        m = re.search(r"d/dx\s*[\(\[](.+?)[\)\]]", q)
        if m:
            return m.group(1).strip()

    if kind == "limit":
        # lim_{x->a} expr or lim x->a expr
        m = re.search(
            r"lim(?:it)?\s*(?:_?\{?\s*x\s*->\s*[-\d\.∞]+\s*\}?)?\s*(.+)$",
            q, re.I
        )
        if m:
            part = m.group(1).strip()
            if part.startswith("(") and part.endswith(")"):
                part = part[1:-1]
            return part if part else None

    return None


def _extract_definite_bounds(question: str) -> Optional[Tuple[float, float]]:
    """Extract integration bounds [a, b] from '∫_a^b' or 'from a to b'."""
    m = re.search(r"∫\s*_?\{?(-?[\d\.]+)\}?\s*\^?\{?(-?[\d\.]+)\}?", question)
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except Exception:
            pass

    m = re.search(r"from\s+(-?[\d\.]+)\s+to\s+(-?[\d\.]+)", question, re.I)
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except Exception:
            pass

    return None


def _is_definite_integral(question: str) -> bool:
    return bool(
        re.search(r"∫\s*_?\{?-?[\d\.]", question)
        or re.search(r"from\s+-?[\d\.]+\s+to\s+-?[\d\.]", question, re.I)
    )


def detect_calc_kind(question: str) -> str:
    q = question.lower()
    if LIMIT_PAT.search(q):
        return "limit"
    if INTEG_PAT.search(q) or "∫" in question:
        return "integral"
    if DERIV_PAT.search(q):
        return "derivative"
    return "unknown"


def verify_calculus(question: str, answer: str) -> Tuple[int, str]:
    """
    Symbolically verify a calculus answer.

    Returns (ok, note):
      ok=1 if verified, 0 otherwise.

    Handles:
      - Derivatives (including chain/product rule results)
      - Indefinite integrals (differentiates claimed antiderivative)
      - Definite integrals (numeric comparison of bounds)
      - Limits (including DNE, infinity, and numeric evaluation)
      - Trig identities via trigsimp
    """
    kind = detect_calc_kind(question)
    final_expr_str = _extract_final_expr(answer)

    if kind == "unknown":
        return 0, "calc_kind_unknown"
    if not final_expr_str:
        return 0, "no_final_expression"

    # --- Derivative ---
    if kind == "derivative":
        try:
            final_expr = _to_sympy(final_expr_str)
        except Exception:
            return 0, "final_expr_parse_failed"

        target_str = _extract_prompt_expression(question, "derivative")
        if not target_str:
            return 0, "prompt_expr_missing"
        try:
            target_expr = _to_sympy(target_str)
        except Exception:
            return 0, "prompt_expr_parse_failed"

        true_deriv = sp.diff(target_expr, _x)
        ok = _equiv_expr(final_expr, true_deriv)
        return (1, "derivative_verified") if ok else (0, "derivative_mismatch")

    # --- Integral ---
    if kind == "integral":
        if _is_definite_integral(question):
            bounds = _extract_definite_bounds(question)
            target_str = _extract_prompt_expression(question, "integral")
            if not target_str or bounds is None:
                return 0, "definite_integral_parse_failed"
            try:
                target_expr = _to_sympy(target_str)
            except Exception:
                return 0, "prompt_expr_parse_failed"
            try:
                a, b = bounds
                true_val = float(sp.integrate(target_expr, (_x, a, b)))
                claimed_val = float(sp.N(_to_sympy(final_expr_str)))
                ok = abs(true_val - claimed_val) < 1e-4
                return (1, "definite_integral_verified") if ok else (0, "definite_integral_mismatch")
            except Exception:
                return 0, "definite_integral_eval_failed"

        # Indefinite integral: d/dx(antiderivative) == integrand
        target_str = _extract_prompt_expression(question, "integral")
        if not target_str:
            return 0, "prompt_expr_missing"
        try:
            target_expr = _to_sympy(target_str)
        except Exception:
            return 0, "prompt_expr_parse_failed"

        # Strip constant of integration before parsing
        antideriv_str = re.sub(r"\+?\s*C\b", "", final_expr_str).strip()
        try:
            antideriv = _to_sympy(antideriv_str)
        except Exception:
            try:
                antideriv = _to_sympy(final_expr_str)
            except Exception:
                return 0, "final_expr_parse_failed"

        recovered = sp.diff(antideriv, _x)
        ok = _equiv_expr(recovered, target_expr)
        return (1, "integral_verified") if ok else (0, "integral_mismatch")

    # --- Limit ---
    if kind == "limit":
        # Extract limit point (supports x->0, x->∞, x->-∞)
        a_sym = sp.S.Zero
        m = re.search(r"x\s*->\s*([-\d\.∞]+)", question.replace(" ", ""))
        if m:
            a_str = m.group(1)
            if "∞" in a_str:
                a_sym = sp.S.NegativeInfinity if a_str.startswith("-") else sp.S.Infinity
            else:
                try:
                    a_sym = sp.Rational(a_str) if "." not in a_str else sp.Float(a_str)
                except Exception:
                    a_sym = sp.S.Zero

        expr_part = _extract_prompt_expression(question, "limit")
        if not expr_part:
            return 0, "limit_expr_missing"
        try:
            expr = _to_sympy(expr_part)
        except Exception:
            return 0, "limit_expr_parse_failed"
        try:
            true_lim = sp.limit(expr, _x, a_sym)
        except Exception:
            return 0, "limit_symbolic_failed"

        # Handle "Does not exist" / "DNE" claims
        final_lower = final_expr_str.lower()
        if "does not exist" in final_lower or "dne" in final_lower:
            dne = true_lim in (sp.S.Infinity, sp.S.NegativeInfinity, sp.S.NaN)
            return (1, "limit_verified_dne") if dne else (0, "limit_mismatch")

        try:
            claimed_val = float(sp.N(_to_sympy(final_expr_str)))
            true_val = float(sp.N(true_lim))
            ok = abs(claimed_val - true_val) < 1e-4
            return (1, "limit_verified") if ok else (0, "limit_mismatch")
        except Exception:
            # Symbolic fallback
            try:
                final_sym = _to_sympy(final_expr_str)
                ok = _equiv_expr(final_sym, true_lim)
                return (1, "limit_verified") if ok else (0, "limit_claim_parse_failed")
            except Exception:
                return 0, "limit_claim_parse_failed"

    return 0, "unhandled_case"
