from typing import Dict, Any, List, Tuple, Optional

# Risk thresholds per student level.
# Lower levels get stricter gates: a hallucination reaching a beginner is more harmful.
_HIGH_THRESH: Dict[str, float] = {
    "pre-algebra": 0.65,
    "algebra i":   0.70,
    "algebra ii":  0.75,
    "calculus":    0.80,
}
_MED_THRESH: Dict[str, float] = {
    "pre-algebra": 0.35,
    "algebra i":   0.40,
    "algebra ii":  0.45,
    "calculus":    0.50,
}


def policy_from_risk(
    risk: float,
    student_level: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Map a risk score to a (label, action) pair.
    Thresholds are tightened for lower student levels.
    """
    level = (student_level or "").lower()
    high = _HIGH_THRESH.get(level, 0.80)
    med = _MED_THRESH.get(level, 0.50)

    if risk >= high:
        return "high_risk", "block_and_verify"
    if risk >= med:
        return "medium_risk", "ask_clarifying_or_verify"
    return "low_risk", "allow"


def reasons_from_signals(features: Dict[str, Any]) -> List[str]:
    """
    Generate human-readable explanations from feature signals.
    Each reason maps to a specific detectable failure mode.
    """
    reasons = []

    if (
        features.get("step_consistent", 1) == 0
        and str(features.get("step_note", "")).startswith("step_")
    ):
        reasons.append(
            "One or more algebra steps appear invalid (equations change incorrectly)."
        )

    if "plug_in_failed" in str(features.get("eq_note", "")):
        reasons.append(
            "Final answer does not satisfy the equation when plugged in."
        )

    if features.get("has_steps", 0) == 0:
        reasons.append("No clear step-by-step work shown.")

    if features.get("new_final", 0) == 1:
        reasons.append(
            "Final value appears unrelated to quantities in the question."
        )

    if features.get("sign_error_hint", 0) == 1:
        reasons.append(
            "Final answer may have an incorrect sign (common sign-flip error)."
        )

    calc_note = str(features.get("calc_note", ""))
    if features.get("calc_verified", 0) == 0 and calc_note.endswith("mismatch"):
        kind = features.get("calc_kind", "calculus")
        reasons.append(
            f"Symbolic verification failed: {kind} result does not match the correct answer."
        )

    if features.get("hedge_count", 0) >= 2:
        reasons.append(
            "Answer contains multiple uncertainty markers, suggesting low model confidence."
        )

    if not reasons:
        reasons.append("Risk inferred from overall answer patterns.")

    return reasons
