from typing import Dict, Any, Tuple, Optional
from backend.app.features.algebra_features import math_text_features, detect_final_answer
from backend.app.verifiers.linear_equation import simple_linear_equation_plug_in
from backend.app.verifiers.step_checker import check_step_consistency
from backend.app.verifiers.calculus_verify import verify_calculus, detect_calc_kind


def build_features(
    question: str,
    answer: str,
    student_level: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build the full feature dictionary for a question-answer pair.
    Includes text/structural features, algebra verifier signals,
    and calculus verifier signals.
    """
    feats = math_text_features(question, answer, student_level=student_level)

    # Algebra plug-in verifier
    final_found, final_val = detect_final_answer(answer)
    feats["eq_plug_ok"] = 0
    feats["eq_note"] = "n/a"

    if final_found and final_val is not None:
        ok, note = simple_linear_equation_plug_in(question, float(final_val))
        feats["eq_plug_ok"] = int(ok)
        feats["eq_note"] = note

    # Step consistency verifier
    step_ok, step_note = check_step_consistency(answer)
    feats["step_consistent"] = int(step_ok)
    feats["step_note"] = step_note

    # Calculus symbolic verifier
    calc_kind = detect_calc_kind(question)
    feats["calc_kind"] = calc_kind
    feats["calc_verified"] = 0
    feats["calc_note"] = "n/a"

    if calc_kind != "unknown":
        ok, note = verify_calculus(question, answer)
        feats["calc_verified"] = int(ok)
        feats["calc_note"] = note

    return feats


# Risk adjustment by student level: lower levels receive stricter gates
# because a hallucination reaching a beginner is more harmful.
_LEVEL_RISK_ADJUST = {
    "pre-algebra": +0.10,
    "algebra i":   +0.05,
    "algebra ii":  +0.00,
    "calculus":    -0.05,
}


def heuristic_risk(
    features: Dict[str, Any],
    student_level: Optional[str] = None,
) -> float:
    """
    Compute a heuristic risk score (0.0–1.0) from symbolic verifier signals.
    Falls back to text-pattern signals when symbolic verification is unavailable.
    Applies a student-level adjustment (+0.10 for Pre-Algebra, -0.05 for Calculus).
    """
    calc_kind = features.get("calc_kind", "unknown")
    calc_verified = int(features.get("calc_verified", 0))
    calc_note = str(features.get("calc_note", ""))

    # Calculus-first overrides
    if calc_kind != "unknown" and calc_verified == 0 and calc_note.endswith("mismatch"):
        base = 0.95  # symbolic mismatch = almost certainly wrong
    elif calc_kind != "unknown" and calc_verified == 1:
        base = 0.20  # verified correct
    elif calc_kind != "unknown" and not calc_note.endswith("mismatch"):
        base = 0.55  # calculus detected but verifier could not parse — ask for clarification

    # Algebra / general rules
    elif str(features.get("eq_note", "")).startswith("plug_in_failed"):
        base = 0.90  # failed plug-in = very likely wrong
    elif features.get("has_steps", 0) == 0:
        base = 0.60  # no work shown
    else:
        base = 0.20  # looks okay

    # Student-level adjustment
    if student_level:
        adj = _LEVEL_RISK_ADJUST.get(student_level.lower(), 0.0)
        base = min(1.0, max(0.0, base + adj))

    return base
