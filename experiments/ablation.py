import sys
from pathlib import Path

# Ensure repo root is on path so `import backend...` works on Windows
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import json
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix

from backend.app.core.scoring import build_features

TRAIN_PATH = Path("backend/app/data/train.jsonl")
DEV_PATH = Path("backend/app/data/dev.jsonl")

STRING_FIELDS = {"eq_note", "step_note"}  # never feed strings into DictVectorizer


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def featurize(rows, drop_features=set()):
    X_dict, y = [], []
    for r in rows:
        feats = build_features(r["question"], r["model_answer"])

        # drop strings
        feats = {k: v for k, v in feats.items() if k not in ("eq_note", "step_note", "calc_note", "calc_kind")}

        # ablation: drop selected numeric features
        for k in drop_features:
            feats.pop(k, None)

        X_dict.append(feats)
        y.append(int(r["label_hallucinated"]))
    return X_dict, np.array(y)


def train_and_eval(drop_features=set(), seed=42):
    train_rows = load_jsonl(TRAIN_PATH)
    dev_rows = load_jsonl(DEV_PATH)

    Xtr_dict, ytr = featurize(train_rows, drop_features=drop_features)
    Xdev_dict, ydev = featurize(dev_rows, drop_features=drop_features)

    vec = DictVectorizer(sparse=True)
    Xtr = vec.fit_transform(Xtr_dict)
    Xdev = vec.transform(Xdev_dict)

    base = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed)
    clf = CalibratedClassifierCV(base, method="isotonic", cv=3)
    clf.fit(Xtr, ytr)

    probs = clf.predict_proba(Xdev)[:, 1]
    pred = (probs >= 0.5).astype(int)

    auroc = roc_auc_score(ydev, probs)
    f1 = f1_score(ydev, pred)
    prec = precision_score(ydev, pred, zero_division=0)
    rec = recall_score(ydev, pred, zero_division=0)
    cm = confusion_matrix(ydev, pred)

    return {
        "AUROC": auroc,
        "F1": f1,
        "Precision": prec,
        "Recall": rec,
        "CM": cm,
    }


def main():
    if not TRAIN_PATH.exists() or not DEV_PATH.exists():
        raise SystemExit("Missing train/dev. Make sure train.jsonl and dev.jsonl exist in backend/app/data/")

    configs = [
        ("FULL", set()),
        ("NO_STEP", {"step_consistent"}),
        ("NO_VERIFIERS", {"step_consistent", "eq_plug_ok"}),
    ]

    results = []
    for name, drops in configs:
        m = train_and_eval(drop_features=drops)
        results.append((name, m))

    # Print a nice table
    print("\n=== Ablation Results (train -> dev) ===")
    print("| Setting | AUROC | F1 | Precision | Recall |")
    print("|---|---:|---:|---:|---:|")
    for name, m in results:
        print(f"| {name} | {m['AUROC']:.3f} | {m['F1']:.3f} | {m['Precision']:.3f} | {m['Recall']:.3f} |")

    print("\nConfusion Matrices [ [TN FP], [FN TP] ]:")
    for name, m in results:
        print(f"\n{name}:")
        print(m["CM"])


if __name__ == "__main__":
    main()
