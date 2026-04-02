"""
experiments/merge_datasets.py

Merges all available labeled datasets into a single stratified train/dev split.

Sources:
  - backend/app/data/calc_all.jsonl        (180 calculus examples)
  - backend/app/data/algebra_hallucination_dataset.jsonl  (300 algebra examples)

Outputs:
  - backend/app/data/train.jsonl  (80% stratified by label)
  - backend/app/data/dev.jsonl    (20% stratified by label)

Run: python experiments/merge_datasets.py
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import json
from collections import Counter
from sklearn.model_selection import train_test_split

SOURCES = [
    Path("backend/app/data/calc_all.jsonl"),
    Path("backend/app/data/algebra_hallucination_dataset.jsonl"),
]
TRAIN_OUT = Path("backend/app/data/train.jsonl")
DEV_OUT = Path("backend/app/data/dev.jsonl")
SEED = 42


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(rows, path: Path):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def main():
    rows = []
    for src in SOURCES:
        if src.exists():
            batch = load_jsonl(src)
            rows.extend(batch)
            print(f"  {src.name}: {len(batch)} examples")
        else:
            print(f"  WARNING: {src} not found — skipping")

    if not rows:
        raise SystemExit("No data found. Generate datasets first.")

    print(f"\nTotal: {len(rows)} examples")
    labels = [r["label_hallucinated"] for r in rows]
    print("Class distribution:", Counter(labels))

    train, dev = train_test_split(
        rows, test_size=0.20, random_state=SEED, stratify=labels
    )

    # Re-assign clean IDs
    for i, r in enumerate(train):
        r["id"] = f"train_{i:04d}"
    for i, r in enumerate(dev):
        r["id"] = f"dev_{i:04d}"

    write_jsonl(train, TRAIN_OUT)
    write_jsonl(dev, DEV_OUT)

    print(f"\nWrote {len(train)} train  -> {TRAIN_OUT}")
    print(f"Wrote {len(dev)} dev    -> {DEV_OUT}")
    print("Train class dist:", Counter(r["label_hallucinated"] for r in train))
    print("Dev class dist:  ", Counter(r["label_hallucinated"] for r in dev))


if __name__ == "__main__":
    main()
