from pathlib import Path
import joblib

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
RISK_MODEL_PATH = MODEL_DIR / "risk_model.joblib"
VEC_PATH = MODEL_DIR / "vectorizer.joblib"


def load_artifacts():
    """
    Load trained model artifacts if they exist and are valid.
    If files are missing/corrupt, return (None, None) so API can fall back to heuristics.
    """
    if not RISK_MODEL_PATH.exists() or not VEC_PATH.exists():
        return None, None

    try:
        model = joblib.load(RISK_MODEL_PATH)
        vec = joblib.load(VEC_PATH)
        return model, vec
    except Exception:
        # Corrupt / partial file, incompatible pickle, etc.
        return None, None
