import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers.score import router as score_router
from backend.app.routers.feedback import router as feedback_router
from backend.app.core.model_store import load_artifacts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hallucination Guard (Math)", version="0.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(score_router)
app.include_router(feedback_router)

@app.get("/health")
def health():
    model, vec = load_artifacts()
    return {"ok": True, "model_loaded": model is not None and vec is not None}
