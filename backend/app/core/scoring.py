from typing import Dict, Any, Tuple
from backend.app.features.algebra_features import math_text_features, detect_final_answer
from backend.app.verifiers.linear_equation import simple_linear_equation_plug_in
from backend.app.verifiers.step_checker import check_step_consistency
from backend.app.verifiers.calculus_verify import verify_calculus, detect_calc_kind



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
    step_ok, step_note = check_step_consistency(answer)
    feats["step_consistent"] = int(step_ok)
    feats["step_note"] = step_note

    # calculus verifier
    calc_kind = detect_calc_kind(question)
    feats["calc_kind"] = calc_kind  # string used only for debugging/explanations
    feats["calc_verified"] = 0
    feats["calc_note"] = "n/a"

    if calc_kind != "unknown":
        ok, note = verify_calculus(question, answer)
        feats["calc_verified"] = int(ok)
        feats["calc_note"] = note

    return feats


def heuristic_risk(features: Dict[str, Any]) -> float:
    # ---------- Calculus-aware overrides ----------
    calc_kind = features.get("calc_kind", "unknown")
    calc_verified = int(features.get("calc_verified", 0))
    calc_note = str(features.get("calc_note", ""))

    # 1) HARD OVERRIDE: symbolic mismatch = almost certainly wrong
    if calc_kind != "unknown" and calc_verified == 0 and calc_note.endswith("mismatch"):
        return 0.95

    # 2) If calculus is verified, keep risk low even if no steps were shown
    if calc_kind != "unknown" and calc_verified == 1:
        return 0.20

    # 3) Calculus detected but verifier couldn't parse → ask to clarify
    if calc_kind != "unknown" and calc_verified == 0 and not calc_note.endswith("mismatch"):
        return 0.55

    # ---------- Algebra / general rules ----------
    if str(features.get("eq_note", "")).startswith("plug_in_failed"):
        return 0.90

    if features.get("has_steps", 0) == 0:
        return 0.60

    return 0.20

