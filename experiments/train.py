import json
from pathlib import Path
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.feature_extraction import DictVectorizer

from backend.app.core.scoring import build_features

DATA = Path("backend/app/data/train.jsonl")
MODEL_DIR = Path("backend/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def main():
    rows = load_jsonl(DATA)
    if len(rows) < 20:
        print("Add at least ~20 examples before training (Phase 1A warmup).")
        return

    X_dict = []
    y = []
    for r in rows:
        feats = build_features(r["question"], r["model_answer"])
        feats = {k: v for k, v in feats.items() if k != "eq_note"}  # drop string field
        X_dict.append(feats)
        y.append(int(r["label_hallucinated"]))

    y = np.array(y)

    vec = DictVectorizer(sparse=True)
    X = vec.fit_transform(X_dict)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    base = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf = CalibratedClassifierCV(base, method="isotonic", cv=3)
    clf.fit(Xtr, ytr)

    p = clf.predict_proba(Xte)[:, 1]
    pred = (p >= 0.5).astype(int)

    print("AUROC:", roc_auc_score(yte, p))
    print("F1:", f1_score(yte, pred))

    joblib.dump(clf, MODEL_DIR / "risk_model.joblib")
    joblib.dump(vec, MODEL_DIR / "vectorizer.joblib")
    print("Saved -> backend/models/risk_model.joblib and vectorizer.joblib")

if __name__ == "__main__":
    main()
