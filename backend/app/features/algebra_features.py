import re
from typing import Dict, Any, Tuple, Optional

_NUM_RE = re.compile(r"(?<!\w)(-?\d+(?:\.\d+)?)(?!\w)")
_EQ_RE = re.compile(r"(.+?)=(.+)")

HEDGES = {
    "maybe", "might", "possibly", "i think", "not sure",
    "approximately", "roughly", "around", "unclear", "uncertain",
    "i believe", "could be", "seems like", "probably",
}
CONFIDENT = {
    "definitely", "always", "clearly", "obviously", "certainly",
    "without a doubt", "must be", "guaranteed", "absolutely", "of course",
    "it is", "the answer is",
}

# Ordinal encoding for student level (-1 = not provided)
STUDENT_LEVEL_MAP = {
    "pre-algebra": 0,
    "algebra i": 1,
    "algebra ii": 2,
    "calculus": 3,
}


def extract_numbers(text: str):
    return [float(x) for x in _NUM_RE.findall(text)]


def detect_final_answer(text: str) -> Tuple[bool, Optional[float]]:
    """
    Detect a final numeric answer from the model response.
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


def math_text_features(
    question: str,
    answer: str,
    student_level: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract linguistic and structural features from a question-answer pair.

    Features include:
    - Hedge/confidence word counts
    - Step presence and count
    - Number counts in question vs answer
    - Final answer detection
    - Sign-error hint
    - Calculus keyword detection
    - Student level encoding
    """
    q = question.lower()
    a = answer.lower()

    hedge_count = sum(1 for h in HEDGES if h in a)
    confident_count = sum(1 for c in CONFIDENT if c in a)

    has_steps = ("->" in answer) or ("\n" in answer) or ("=" in answer)
    # Count distinct step transitions for richer signal
    step_count = len(re.split(r"(?:->|\n)+", answer.strip()))

    nums_q = extract_numbers(question)
    nums_a = extract_numbers(answer)

    final_found, final_val = detect_final_answer(answer)

    # Heuristic: final value appears "new" (not in question numbers)
    new_final = 0
    if final_found and final_val is not None and nums_q:
        new_final = int(all(abs(final_val - n) > 1e-9 for n in nums_q))

    # Sign-error hint: final is the negative of a question number
    sign_error_hint = 0
    if final_found and final_val is not None and nums_q:
        sign_error_hint = int(any(abs(final_val + n) < 1e-9 for n in nums_q))

    # Calculus keyword detection
    calc_keywords = ["derivative", "differentiate", "integral", "∫", "limit", "d/dx", "dy/dx"]
    is_calc = int(any(k in q for k in calc_keywords))

    # Student level as ordinal feature
    level_enc = -1
    if student_level:
        level_enc = STUDENT_LEVEL_MAP.get(student_level.lower(), -1)

    return {
        "hedge_count": hedge_count,
        "confident_count": confident_count,
        "has_steps": int(has_steps),
        "step_count": step_count,
        "num_count_q": len(nums_q),
        "num_count_a": len(nums_a),
        "final_found": int(final_found),
        "final_val": float(final_val) if final_val is not None else 0.0,
        "new_final": new_final,
        "sign_error_hint": sign_error_hint,
        "answer_len": len(answer),
        "is_calc_prompt": is_calc,
        "student_level_enc": level_enc,
    }
