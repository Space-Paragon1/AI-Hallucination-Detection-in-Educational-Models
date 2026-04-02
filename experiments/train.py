# experiments/train.py
"""
Trains the hallucination risk model with:
  - 5-fold stratified cross-validation
  - Multi-model comparison (LogisticRegression, RandomForest, GradientBoosting)
  - Best model saved to backend/models/
  - Results saved to experiments/results/train_results.json

Run: python experiments/train.py
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import json
import numpy as np
import joblib
from collections import Counter

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.feature_extraction import DictVectorizer

from backend.app.core.scoring import build_features

DATA = Path("backend/app/data/train.jsonl")
MODEL_DIR = Path("backend/models")
RESULTS_DIR = Path("experiments/results")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

STRING_FIELDS = {"eq_note", "step_note", "calc_note", "calc_kind"}


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def featurize(rows):
    X_dict, y = [], []
    for r in rows:
        feats = build_features(
            r["question"], r["model_answer"],
            student_level=r.get("student_level"),
        )
        feats = {k: v for k, v in feats.items() if k not in STRING_FIELDS}
        X_dict.append(feats)
        y.append(int(r["label_hallucinated"]))
    return X_dict, np.array(y)


def build_candidate_models():
    return {
        "LogisticRegression": CalibratedClassifierCV(
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
            method="isotonic",
            cv=3,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }


def main():
    if not DATA.exists():
        raise SystemExit(
            f"Missing {DATA}. Run: python experiments/merge_datasets.py"
        )

    rows = load_jsonl(DATA)
    if len(rows) < 20:
        print("Add at least 20 examples before training.")
        return

    print(f"Loaded {len(rows)} training examples")
    print("Class dist:", Counter(r["label_hallucinated"] for r in rows))

    X_dict, y = featurize(rows)
    vec = DictVectorizer(sparse=True)
    X = vec.fit_transform(X_dict)

    candidates = build_candidate_models()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    cv_results = {}
    best_name, best_auroc = None, -1.0

    print(f"\n=== 5-Fold Stratified Cross-Validation (n={len(rows)}) ===")
    print(f"{'Model':<25} {'AUROC':>12} {'F1':>12}")
    print("-" * 52)

    for name, clf in candidates.items():
        auroc_scores = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
        f1_scores = cross_val_score(clf, X, y, cv=cv, scoring="f1", n_jobs=-1)

        auroc_m, auroc_s = auroc_scores.mean(), auroc_scores.std()
        f1_m, f1_s = f1_scores.mean(), f1_scores.std()

        print(f"{name:<25} {auroc_m:.3f}±{auroc_s:.3f}  {f1_m:.3f}±{f1_s:.3f}")

        cv_results[name] = {
            "auroc_mean": float(auroc_m),
            "auroc_std": float(auroc_s),
            "f1_mean": float(f1_m),
            "f1_std": float(f1_s),
        }

        if auroc_m > best_auroc:
            best_auroc = auroc_m
            best_name = name

    print(f"\nBest model: {best_name} (AUROC={best_auroc:.3f})")

    # Retrain best model on full training set
    best_clf = candidates[best_name]
    best_clf.fit(X, y)

    joblib.dump(best_clf, MODEL_DIR / "risk_model.joblib")
    joblib.dump(vec, MODEL_DIR / "vectorizer.joblib")
    print(f"Saved -> backend/models/ (best: {best_name})")

    out = {
        "best_model": best_name,
        "best_auroc_cv": float(best_auroc),
        "n_train": len(rows),
        "n_features": X.shape[1],
        "cv_results": cv_results,
    }
    out_path = RESULTS_DIR / "train_results.json"
    with out_path.open("w") as f:
        json.dump(out, f, indent=2)
    print(f"Results -> {out_path}")


if __name__ == "__main__":
    main()
