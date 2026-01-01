from fastapi import APIRouter
from pathlib import Path
import json
from datetime import datetime
from backend.app.core.schemas import FeedbackRequest

router = APIRouter()

FEEDBACK_PATH = Path(__file__).resolve().parents[2] / "data" / "feedback.jsonl"
FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

@router.post("/feedback")
def feedback(req: FeedbackRequest):
    record = req.model_dump()
    record["ts"] = datetime.utcnow().isoformat()

    with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {"ok": True}
