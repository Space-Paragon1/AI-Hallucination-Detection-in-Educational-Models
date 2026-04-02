# experiments/retrain_from_feedback.py
"""
Retrains the risk model by combining original training data with
user-submitted feedback labels (backend/data/feedback.jsonl).

Also performs uncertainty sampling: identifies predictions in the
[UNCERTAINTY_LO, UNCERTAINTY_HI] band that benefit most from human review.

Run: python experiments/retrain_from_feedback.py
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import roc_auc_score, f1_score

from backend.app.core.scoring import build_features

TRAIN_PATH = Path("backend/app/data/train.jsonl")
FEEDBACK_PATH = Path("backend/data/feedback.jsonl")
MODEL_DIR = Path("backend/models")
RESULTS_DIR = Path("experiments/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

STRING_FIELDS = {"eq_note", "step_note", "calc_note", "calc_kind"}
UNCERTAINTY_LO = 0.40
UNCERTAINTY_HI = 0.60


def load_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def feedback_to_example(fb: dict):
    """Convert a feedback record to a training example. Returns None if malformed."""
    required = ("question", "model_answer", "user_label_hallucinated")
    if not all(k in fb for k in required):
        return None
    return {
        "question": fb["question"],
        "model_answer": fb["model_answer"],
        "label_hallucinated": int(fb["user_label_hallucinated"]),
        "student_level": fb.get("student_level"),
        "error_type": "feedback",
        "severity": 1,
    }


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


def main():
    train_rows = load_jsonl(TRAIN_PATH)
    print(f"Base training examples: {len(train_rows)}")

    fb_raw = load_jsonl(FEEDBACK_PATH)
    fb_examples = [ex for fb in fb_raw if (ex := feedback_to_example(fb)) is not None]
    print(f"Feedback examples (valid): {len(fb_examples)}")

    all_rows = train_rows + fb_examples
    print(f"Combined: {len(all_rows)} examples")
    print("Class dist:", Counter(r["label_hallucinated"] for r in all_rows))

    if len(all_rows) < 20:
        print("Not enough data to retrain. Collect more feedback first.")
        return

    X_dict, y = featurize(all_rows)
    vec = DictVectorizer(sparse=True)
    X = vec.fit_transform(X_dict)

    clf_base = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
    clf = CalibratedClassifierCV(clf_base, method="isotonic", cv=3)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auroc_cv = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    f1_cv = cross_val_score(clf, X, y, cv=cv, scoring="f1", n_jobs=-1)
    print(f"\n5-Fold CV  AUROC: {auroc_cv.mean():.3f} ± {auroc_cv.std():.3f}")
    print(f"5-Fold CV  F1:    {f1_cv.mean():.3f} ± {f1_cv.std():.3f}")

    clf.fit(X, y)
    probs = clf.predict_proba(X)[:, 1]

    # --- Uncertainty sampling ---
    uncertain_mask = (probs >= UNCERTAINTY_LO) & (probs <= UNCERTAINTY_HI)
    print(
        f"\nUncertainty band [{UNCERTAINTY_LO}, {UNCERTAINTY_HI}]: "
        f"{uncertain_mask.sum()} examples flagged for human review"
    )

    uncertain_examples = []
    for i, (row, p) in enumerate(zip(all_rows, probs)):
        if uncertain_mask[i]:
            uncertain_examples.append({
                "question": row["question"],
                "model_answer": row["model_answer"],
                "risk_score": round(float(p), 4),
                "source": "feedback" if i >= len(train_rows) else "train",
                "true_label": int(y[i]),
            })

    if uncertain_examples:
        upath = RESULTS_DIR / "uncertain_samples.json"
        with upath.open("w") as f:
            json.dump(uncertain_examples, f, indent=2)
        print(f"Uncertainty samples -> {upath}")

    # Save updated model
    joblib.dump(clf, MODEL_DIR / "risk_model.joblib")
    joblib.dump(vec, MODEL_DIR / "vectorizer.joblib")
    print("\nUpdated models saved -> backend/models/")

    results = {
        "n_train_base": len(train_rows),
        "n_feedback": len(fb_examples),
        "n_total": len(all_rows),
        "cv_auroc_mean": float(auroc_cv.mean()),
        "cv_auroc_std": float(auroc_cv.std()),
        "cv_f1_mean": float(f1_cv.mean()),
        "cv_f1_std": float(f1_cv.std()),
        "n_uncertain": int(uncertain_mask.sum()),
    }
    rpath = RESULTS_DIR / "retrain_results.json"
    with rpath.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"Results -> {rpath}")


if __name__ == "__main__":
    main()
