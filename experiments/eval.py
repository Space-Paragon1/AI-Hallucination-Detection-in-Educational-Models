# experiments/eval.py
"""
Evaluates the trained risk model on the dev set.

Computes:
  - Overall AUROC, F1, Precision, Recall, Confusion Matrix
  - Calibration curve (10 bins)
  - Per-domain breakdown (algebra vs calculus)
  - Per-error-type breakdown
  - Per-severity breakdown

Saves:
  - experiments/results/eval_results.json
  - experiments/results/predictions.csv

Run: python experiments/eval.py
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import json
import csv
import numpy as np
import joblib

from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report,
)

from backend.app.core.scoring import build_features
from backend.app.verifiers.calculus_verify import detect_calc_kind

DEV = Path("backend/app/data/dev.jsonl")
MODEL_PATH = Path("backend/models/risk_model.joblib")
VEC_PATH = Path("backend/models/vectorizer.joblib")
RESULTS_DIR = Path("experiments/results")
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


def bucket_calibration(probs, y, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    out = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (
            (probs >= lo) & (probs < hi)
            if i < n_bins - 1
            else (probs >= lo) & (probs <= hi)
        )
        if mask.sum() == 0:
            continue
        out.append({
            "bin_lo": float(lo),
            "bin_hi": float(hi),
            "n": int(mask.sum()),
            "avg_pred": float(probs[mask].mean()),
            "emp_rate": float(y[mask].mean()),
        })
    return out


def infer_domain(question: str) -> str:
    return "calculus" if detect_calc_kind(question) != "unknown" else "algebra"


def breakdown(y, probs, pred, meta, key):
    results = {}
    for val in sorted(set(m[key] for m in meta)):
        idx = np.array([m[key] == val for m in meta])
        if idx.sum() < 5:
            continue
        au = (
            roc_auc_score(y[idx], probs[idx])
            if len(set(y[idx])) > 1
            else float("nan")
        )
        f1 = f1_score(y[idx], pred[idx], zero_division=0)
        results[str(val)] = {"n": int(idx.sum()), "auroc": float(au), "f1": float(f1)}
    return results


def main():
    if not DEV.exists():
        raise SystemExit("Missing dev set. Run: python experiments/merge_datasets.py")

    rows = load_jsonl(DEV)
    print(f"Dev examples: {len(rows)}")

    model = joblib.load(MODEL_PATH)
    vec = joblib.load(VEC_PATH)

    X_dict, y, meta = [], [], []
    for r in rows:
        feats = build_features(
            r["question"], r["model_answer"],
            student_level=r.get("student_level"),
        )
        feats_num = {k: v for k, v in feats.items() if k not in STRING_FIELDS}
        X_dict.append(feats_num)
        y.append(int(r["label_hallucinated"]))
        meta.append({
            "error_type": r.get("error_type", "unknown"),
            "severity": int(r.get("severity", 0)),
            "domain": infer_domain(r["question"]),
        })

    y = np.array(y)
    X = vec.transform(X_dict)
    probs = model.predict_proba(X)[:, 1]
    pred = (probs >= 0.5).astype(int)

    # Overall metrics
    overall = {
        "n": len(y),
        "auroc": float(roc_auc_score(y, probs)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }

    print("\n=== Overall Metrics (Dev) ===")
    for k, v in overall.items():
        if k != "confusion_matrix":
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    print("  Confusion Matrix [[TN FP], [FN TP]]:", overall["confusion_matrix"])

    # Calibration
    cal = bucket_calibration(probs, y)
    print("\n=== Calibration (10 bins) ===")
    for b in cal:
        print(
            f"  [{b['bin_lo']:.1f},{b['bin_hi']:.1f}]  n={b['n']:3d}"
            f"  avg_pred={b['avg_pred']:.3f}  emp_rate={b['emp_rate']:.3f}"
        )

    # Breakdowns
    domain_res = breakdown(y, probs, pred, meta, "domain")
    error_res = breakdown(y, probs, pred, meta, "error_type")
    sev_res = breakdown(y, probs, pred, meta, "severity")

    print("\n=== Breakdown by Domain ===")
    for k, v in domain_res.items():
        print(f"  {k:12s} n={v['n']:3d}  AUROC={v['auroc']:.3f}  F1={v['f1']:.3f}")

    print("\n=== Breakdown by Error Type ===")
    for k, v in error_res.items():
        print(f"  {k:20s} n={v['n']:3d}  AUROC={v['auroc']:.3f}  F1={v['f1']:.3f}")

    print("\n=== Breakdown by Severity ===")
    for k, v in sev_res.items():
        print(f"  severity={k:<2s} n={v['n']:3d}  AUROC={v['auroc']:.3f}  F1={v['f1']:.3f}")

    print("\n", classification_report(y, pred, zero_division=0))

    # Save JSON results
    results = {
        "overall": overall,
        "calibration": cal,
        "by_domain": domain_res,
        "by_error_type": error_res,
        "by_severity": sev_res,
    }
    json_path = RESULTS_DIR / "eval_results.json"
    with json_path.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"Results -> {json_path}")

    # Save predictions CSV
    csv_path = RESULTS_DIR / "predictions.csv"
    fieldnames = [
        "id", "question", "true_label", "pred_label",
        "risk_score", "domain", "error_type", "severity",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for i, (r, m) in enumerate(zip(rows, meta)):
            w.writerow({
                "id": r.get("id", str(i)),
                "question": r["question"][:80].replace("\n", " "),
                "true_label": int(y[i]),
                "pred_label": int(pred[i]),
                "risk_score": round(float(probs[i]), 4),
                "domain": m["domain"],
                "error_type": m["error_type"],
                "severity": m["severity"],
            })
    print(f"Predictions CSV -> {csv_path}")


if __name__ == "__main__":
    main()
