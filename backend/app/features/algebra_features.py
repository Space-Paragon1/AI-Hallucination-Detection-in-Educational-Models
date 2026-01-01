import re
from typing import Dict, Any, Tuple

_NUM_RE = re.compile(r"(?<!\w)(-?\d+(?:\.\d+)?)(?!\w)")
_EQ_RE = re.compile(r"(.+?)=(.+)")

HEDGES = {"maybe", "might", "possibly", "i think", "not sure", "approximately"}
CONFIDENT = {"definitely", "always", "clearly", "obviously", "certainly"}


def extract_numbers(text: str):
    return [float(x) for x in _NUM_RE.findall(text)]


def detect_final_answer(text: str) -> Tuple[bool, float | None]:
    """
    Detect a final numeric answer.
    Tries: 'Answer: 3', 'final answer is 3', 'x = 3', otherwise last number.
    """
    m = re.search(r"(?:final\s*answer|answer)\s*[:is]*\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if m:
        return True, float(m.group(1))

    m = re.search(r"\b([a-zA-Z])\s*=\s*(-?\d+(?:\.\d+)?)\b", text)
    if m:
        return True, float(m.group(2))

    nums = extract_numbers(text)
    if nums:
        return True, float(nums[-1])

    return False, None


def math_text_features(question: str, answer: str) -> Dict[str, Any]:
    q = question.lower()
    a = answer.lower()

    hedge_count = sum(1 for h in HEDGES if h in a)
    confident_count = sum(1 for c in CONFIDENT if c in a)

    has_steps = ("->" in answer) or ("\n" in answer) or ("=" in answer)

    nums_q = extract_numbers(question)
    nums_a = extract_numbers(answer)

    final_found, final_val = detect_final_answer(answer)

    # Simple heuristic: final appears "new" relative to question numbers
    new_final = 0
    if final_found and final_val is not None and nums_q:
        new_final = int(all(abs(final_val - n) > 1e-9 for n in nums_q))

    # Calc-ready: detect if question looks like derivative/integral/limit
    is_calc = int(any(k in q for k in ["derivative", "differentiate", "integral", "∫", "limit", "d/dx"]))

    return {
        "hedge_count": hedge_count,
        "confident_count": confident_count,
        "has_steps": int(has_steps),
        "num_count_q": len(nums_q),
        "num_count_a": len(nums_a),
        "final_found": int(final_found),
        "final_val": float(final_val) if final_val is not None else 0.0,
        "new_final": new_final,
        "answer_len": len(answer),
        "is_calc_prompt": is_calc,
    }
