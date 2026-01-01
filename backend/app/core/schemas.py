from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ScoreRequest(BaseModel):
    question: str
    model_answer: str
    student_level: Optional[str] = None


class ScoreResponse(BaseModel):
    risk: float = Field(..., ge=0.0, le=1.0)
    label: str
    action: str
    reasons: List[str]
    features: Dict[str, Any]


class FeedbackRequest(BaseModel):
    question: str
    model_answer: str
    student_level: Optional[str] = None
    user_label_hallucinated: int = Field(..., ge=0, le=1)
    notes: Optional[str] = None
