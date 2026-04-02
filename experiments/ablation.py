# experiments/ablation.py
"""
Feature ablation study for the hallucination risk model.

Measures the impact of removing verifier features:
  FULL        — all features
  NO_STEP     — drop step_consistent
  NO_VERIFIERS — drop step_consistent + eq_plug_ok
  NO_CALC     — drop calc_verified
  TEXT_ONLY   — only linguistic features (drop all verifiers)

Results saved to experiments/results/ablation_results.json (and printed as a table).

Run: python experiments/ablation.py
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import json
import numpy as np

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score

from backend.app.core.scoring import build_features

TRAIN_PATH = Path("backend/app/data/train.jsonl")
DEV_PATH = Path("backend/app/data/dev.jsonl")
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


def featurize(rows, drop_features=frozenset()):
    X_dict, y = [], []
    for r in rows:
        feats = build_features(
            r["question"], r["model_answer"],
            student_level=r.get("student_level"),
        )
        feats = {k: v for k, v in feats.items() if k not in STRING_FIELDS}
        for k in drop_features:
            feats.pop(k, None)
        X_dict.append(feats)
        y.append(int(r["label_hallucinated"]))
    return X_dict, np.array(y)


def run_config(train_rows, dev_rows, drop_features=frozenset(), seed=42):
    Xtr_dict, ytr = featurize(train_rows, drop_features)
    Xdev_dict, ydev = featurize(dev_rows, drop_features)

    vec = DictVectorizer(sparse=True)
    Xtr = vec.fit_transform(Xtr_dict)
    Xdev = vec.transform(Xdev_dict)

    base = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed)
    clf = CalibratedClassifierCV(base, method="isotonic", cv=3)

    # 5-fold CV on train
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cv_auroc = cross_val_score(clf, Xtr, ytr, cv=cv, scoring="roc_auc", n_jobs=-1)

    clf.fit(Xtr, ytr)
    probs = clf.predict_proba(Xdev)[:, 1]
    pred = (probs >= 0.5).astype(int)

    return {
        "cv_auroc_mean": float(cv_auroc.mean()),
        "cv_auroc_std": float(cv_auroc.std()),
        "dev_auroc": float(roc_auc_score(ydev, probs)),
        "dev_f1": float(f1_score(ydev, pred, zero_division=0)),
        "dev_precision": float(precision_score(ydev, pred, zero_division=0)),
        "dev_recall": float(recall_score(ydev, pred, zero_division=0)),
    }


def main():
    if not TRAIN_PATH.exists() or not DEV_PATH.exists():
        raise SystemExit(
            "Missing train/dev. Run: python experiments/merge_datasets.py"
        )

    train_rows = load_jsonl(TRAIN_PATH)
    dev_rows = load_jsonl(DEV_PATH)

    configs = [
        ("FULL",         frozenset()),
        ("NO_STEP",      frozenset({"step_consistent"})),
        ("NO_VERIFIERS", frozenset({"step_consistent", "eq_plug_ok"})),
        ("NO_CALC",      frozenset({"calc_verified"})),
        ("TEXT_ONLY",    frozenset({"step_consistent", "eq_plug_ok", "calc_verified"})),
    ]

    results = {}
    print("\n=== Ablation Study (train -> dev) ===")
    header = f"{'Setting':<15} {'CV-AUROC':>12} {'Dev-AUROC':>10} {'F1':>8} {'Prec':>8} {'Rec':>8}"
    print(header)
    print("-" * len(header))

    for name, drops in configs:
        m = run_config(train_rows, dev_rows, drop_features=drops)
        results[name] = m
        print(
            f"{name:<15} "
            f"{m['cv_auroc_mean']:.3f}±{m['cv_auroc_std']:.3f}  "
            f"{m['dev_auroc']:>9.3f}  "
            f"{m['dev_f1']:>7.3f}  "
            f"{m['dev_precision']:>7.3f}  "
            f"{m['dev_recall']:>7.3f}"
        )

    # Markdown table for copy-paste into paper
    print("\n=== Markdown Table (for paper) ===")
    print("| Setting | CV AUROC | Dev AUROC | F1 | Precision | Recall |")
    print("|---------|:--------:|:---------:|:--:|:---------:|:------:|")
    for name, m in results.items():
        print(
            f"| {name} "
            f"| {m['cv_auroc_mean']:.3f}±{m['cv_auroc_std']:.3f} "
            f"| {m['dev_auroc']:.3f} "
            f"| {m['dev_f1']:.3f} "
            f"| {m['dev_precision']:.3f} "
            f"| {m['dev_recall']:.3f} |"
        )

    out_path = RESULTS_DIR / "ablation_results.json"
    with out_path.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults -> {out_path}")


if __name__ == "__main__":
    main()
