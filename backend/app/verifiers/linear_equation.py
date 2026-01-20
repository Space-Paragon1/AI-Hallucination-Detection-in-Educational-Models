import re
from typing import Tuple

_EQ_RE = re.compile(r"(.+?)=(.+)")

def simple_linear_equation_plug_in(question: str, x_value: float) -> Tuple[bool, str]:
    """
    Lightweight verifier:
    - Looks for one equation '...=...' in the question
    - Supports basic arithmetic with variable x: + - * / () and numbers
    - Plugs x_value and checks equality
    """
    eq = question.replace(" ", "")

# Convert implicit multiplication like 3(x-2) -> 3*(x-2)
    eq = re.sub(r"(\d)(\()", r"\1*\2", eq)
# Convert x(x+1) -> x*(x+1)
    eq = re.sub(r"(x)(\()", r"\1*\2", eq)
# Convert )( -> )*(
    eq = re.sub(r"(\))(\()", r"\1*\2", eq)
    m = _EQ_RE.search(eq)
    if not m:
        return False, "no_equation_found"

    left, right = m.group(1), m.group(2)

    # allow only safe characters
    if not re.fullmatch(r"[0-9x\+\-\*\/\.\(\)]+", left):
        return False, "left_not_supported"
    if not re.fullmatch(r"[0-9x\+\-\*\/\.\(\)]+", right):
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
