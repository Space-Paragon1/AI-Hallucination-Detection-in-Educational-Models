import json
from pathlib import Path
import numpy as np
import joblib

from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)

from backend.app.core.scoring import build_features

DEV = Path("backend/app/data/dev.jsonl")
MODEL_PATH = Path("backend/models/risk_model.joblib")
VEC_PATH = Path("backend/models/vectorizer.joblib")

def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def bucket_calibration(probs, y, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    out = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (probs >= lo) & (probs < hi) if i < n_bins - 1 else (probs >= lo) & (probs <= hi)
        if mask.sum() == 0:
            continue
        avg_p = float(probs[mask].mean())
        emp = float(y[mask].mean())
        out.append((lo, hi, mask.sum(), avg_p, emp))
    return out

def main():
    if not DEV.exists():
        raise SystemExit("Missing dev set. Run: python experiments/split_data.py")

    rows = load_jsonl(DEV)
    print(f"Loaded dev examples: {len(rows)}")

    model = joblib.load(MODEL_PATH)
    vec = joblib.load(VEC_PATH)

    X_dict = []
    y = []
    meta = []
    for r in rows:
        feats = build_features(r["question"], r["model_answer"])
        feats = {k: v for k, v in feats.items() if k not in ("eq_note", "step_note", "calc_note", "calc_kind")}
        X_dict.append(feats)
        y.append(int(r["label_hallucinated"]))
        meta.append((r.get("error_type", "unknown"), int(r.get("severity", 0))))

    y = np.array(y)
    X = vec.transform(X_dict)

    probs = model.predict_proba(X)[:, 1]
    pred = (probs >= 0.5).astype(int)

    print("\n=== Overall Metrics (Dev) ===")
    print("AUROC:", roc_auc_score(y, probs))
    print("F1:", f1_score(y, pred))
    print("Precision:", precision_score(y, pred, zero_division=0))
    print("Recall:", recall_score(y, pred, zero_division=0))

    cm = confusion_matrix(y, pred)
    print("\nConfusion Matrix [ [TN FP], [FN TP] ]:")
    print(cm)

    print("\nClassification report:")
    print(classification_report(y, pred, zero_division=0))

    print("\n=== Calibration (10 bins) ===")
    for lo, hi, n, avg_p, emp in bucket_calibration(probs, y, n_bins=10):
        print(f"[{lo:.1f},{hi:.1f}] n={n:3d}  avg_pred={avg_p:.3f}  emp_rate={emp:.3f}")

    # Breakdown by error_type
    print("\n=== Breakdown by error_type ===")
    types = sorted(set(t for t, _ in meta))
    for t in types:
        idx = np.array([tt == t for tt, _ in meta])
        if idx.sum() < 5:
            continue
        au = roc_auc_score(y[idx], probs[idx]) if len(set(y[idx])) > 1 else float("nan")
        f1 = f1_score(y[idx], pred[idx])
        print(f"{t:15s} n={idx.sum():3d}  AUROC={au:.3f}  F1={f1:.3f}")

    # Breakdown by severity
    print("\n=== Breakdown by severity ===")
    sevs = sorted(set(s for _, s in meta))
    for s in sevs:
        idx = np.array([ss == s for _, ss in meta])
        if idx.sum() < 5:
            continue
        au = roc_auc_score(y[idx], probs[idx]) if len(set(y[idx])) > 1 else float("nan")
        f1 = f1_score(y[idx], pred[idx])
        print(f"severity={s:<2d} n={idx.sum():3d}  AUROC={au:.3f}  F1={f1:.3f}")

if __name__ == "__main__":
    main()
