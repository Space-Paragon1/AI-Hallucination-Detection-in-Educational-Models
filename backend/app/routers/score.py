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

    if _model is None or _vec is None:
        risk = heuristic_risk(feats)
    else:
        # remove non-numeric/string fields that DictVectorizer didn't see during training
        feats_numeric = {k: v for k, v in feats.items() if k != "eq_note"}
        X = _vec.transform([feats_numeric])
        risk = float(_model.predict_proba(X)[0, 1])

    label, action = policy_from_risk(risk)
    reasons = reasons_from_signals(feats)

    return ScoreResponse(
        risk=risk,
        label=label,
        action=action,
        reasons=reasons,
        features=feats,
    )
