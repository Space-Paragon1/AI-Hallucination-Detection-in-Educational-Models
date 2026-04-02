import logging
from fastapi import APIRouter, HTTPException
from backend.app.core.schemas import ScoreRequest, ScoreResponse
from backend.app.core.model_store import load_artifacts
from backend.app.core.scoring import build_features, heuristic_risk
from backend.app.policy.decision import policy_from_risk, reasons_from_signals

logger = logging.getLogger(__name__)

router = APIRouter()

_model, _vec = load_artifacts()


@router.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    try:
        feats = build_features(
            req.question,
            req.model_answer,
            student_level=req.student_level,
        )
    except Exception as exc:
        logger.error("Feature extraction failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=422, detail=f"Feature extraction error: {exc}")

    heur = heuristic_risk(feats, student_level=req.student_level)

    if _model is None or _vec is None:
        risk = heur
    else:
        try:
            feats_numeric = {
                k: v
                for k, v in feats.items()
                if k not in ("eq_note", "step_note", "calc_note", "calc_kind")
            }
            X = _vec.transform([feats_numeric])
            ml_risk = float(_model.predict_proba(X)[0, 1])
            # Take the maximum: ML score or heuristic override
            risk = max(ml_risk, heur)
        except Exception as exc:
            logger.warning("ML model failed, using heuristic: %s", exc)
            risk = heur

    label, action = policy_from_risk(risk, student_level=req.student_level)
    reasons = reasons_from_signals(feats)

    return ScoreResponse(
        risk=risk,
        label=label,
        action=action,
        reasons=reasons,
        features=feats,
    )
