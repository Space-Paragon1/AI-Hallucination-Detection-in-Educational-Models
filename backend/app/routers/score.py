from fastapi import APIRouter
from backend.app.core.schemas import ScoreRequest, ScoreResponse
from backend.app.core.model_store import load_artifacts
from backend.app.core.scoring import build_features, heuristic_risk
from backend.app.policy.decision import policy_from_risk, reasons_from_signals

router = APIRouter()

_model, _vec = load_artifacts()

@router.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    feats = build_features(req.question, req.model_answer)

    heur = heuristic_risk(feats)

    if _model is None or _vec is None:
        risk = heur
    else:
        # remove string fields not seen during training
        feats_numeric = {
            k: v
            for k, v in feats.items()
            if k not in ("eq_note", "step_note", "calc_note", "calc_kind")
        }
        X = _vec.transform([feats_numeric])
        ml_risk = float(_model.predict_proba(X)[0, 1])

        # IMPORTANT: let verifier/heuristics override ML when needed
        risk = max(ml_risk, heur)

    label, action = policy_from_risk(risk)
    reasons = reasons_from_signals(feats)

    return ScoreResponse(
        risk=risk,
        label=label,
        action=action,
        reasons=reasons,
        features=feats,
    )
