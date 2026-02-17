import re
from typing import Tuple

_SAFE = re.compile(r"^[0-9x\+\-\*\/\.\(\)]+$")
_EQ_RE = re.compile(r"(.+?)=(.+)")


def _apply_implicit_multiply(s: str) -> str:
    s = re.sub(r"(\d)(x)", r"\1*\2", s)
    s = re.sub(r"(x)(\d)", r"\1*\2", s)
    s = re.sub(r"(\d)(\()", r"\1*\2", s)
    s = re.sub(r"(x)(\()", r"\1*\2", s)
    s = re.sub(r"(\))(\()", r"\1*\2", s)
    s = re.sub(r"(\))(x)", r"\1*\2", s)
    return s


def _extract_equation(text: str) -> str | None:
    """Extract the math equation from question text, stripping prose prefixes."""
    # If there's a colon, take everything after the last colon
    if ":" in text:
        text = text.rsplit(":", 1)[1]
    # Strip common prefixes
    text = re.sub(r"(?i)^(solve|find|simplify|evaluate|compute)\b\s*", "", text.strip())
    text = re.sub(r"(?i)^for\s+[a-z]\s*:\s*", "", text.strip())
    text = text.strip()
    if "=" in text:
        return text
    return None


def simple_linear_equation_plug_in(question: str, x_value: float) -> Tuple[bool, str]:
    """
    Lightweight verifier:
    - Looks for one equation '...=...' in the question
    - Supports basic arithmetic with variable x: + - * / () and numbers
    - Plugs x_value and checks equality
    """
    eq_text = _extract_equation(question)
    if not eq_text:
        return False, "no_equation_found"

    eq = eq_text.replace(" ", "")
    eq = _apply_implicit_multiply(eq)

    m = _EQ_RE.search(eq)
    if not m:
        return False, "no_equation_found"

    left, right = m.group(1), m.group(2)

    if not _SAFE.fullmatch(left):
        return False, "left_not_supported"
    if not _SAFE.fullmatch(right):
        return False, "right_not_supported"

    def safe_eval(expr: str, x: float) -> float:
        expr = expr.replace("x", f"({x})")
        return float(eval(expr, {"__builtins__": {}}, {}))

    try:
        lv = safe_eval(left, x_value)
        rv = safe_eval(right, x_value)
        ok = abs(lv - rv) < 1e-6
        if ok:
            return True, "plug_in_ok"
        return False, f"plug_in_failed: {lv} != {rv}"
    except Exception:
        return False, "eval_failed"
