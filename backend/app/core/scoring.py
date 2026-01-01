from typing import Dict, Any, Tuple
from backend.app.features.algebra_features import math_text_features, detect_final_answer
from backend.app.verifiers.linear_equation import simple_linear_equation_plug_in

def build_features(question: str, answer: str) -> Dict[str, Any]:
    feats = math_text_features(question, answer)

    # verifier signal (algebra)
    final_found, final_val = detect_final_answer(answer)
    feats["eq_plug_ok"] = 0
    feats["eq_note"] = "n/a"

    if final_found and final_val is not None:
        ok, note = simple_linear_equation_plug_in(question, float(final_val))
        feats["eq_plug_ok"] = int(ok)
        feats["eq_note"] = note

    return feats


def heuristic_risk(features: Dict[str, Any]) -> float:
    # If equation plug-in fails in a supported equation → high risk
    if features.get("eq_note", "").startswith("plug_in_failed"):
        return 0.9
    # No steps tends to be riskier
    if features.get("has_steps", 0) == 0:
        return 0.6
    return 0.2
