from typing import Dict, Any, List, Tuple

def policy_from_risk(risk: float) -> Tuple[str, str]:
    if risk >= 0.80:
        return "high_risk", "block_and_verify"
    if risk >= 0.50:
        return "medium_risk", "ask_clarifying_or_verify"
    return "low_risk", "allow"


def reasons_from_signals(features: Dict[str, Any]) -> List[str]:
    reasons = []

    if features.get("eq_note") and "plug_in_failed" in str(features["eq_note"]):
        reasons.append("Final answer does not satisfy the equation when plugged in.")

    if features.get("has_steps", 0) == 0:
        reasons.append("No clear step-by-step work shown.")

    if features.get("new_final", 0) == 1:
        reasons.append("Final value appears unrelated to quantities in the question.")

    if not reasons:
        reasons.append("Risk inferred from overall answer patterns.")
    return reasons
