import json
from pathlib import Path
import random

SRC = Path("backend/app/data/train.jsonl")
OUT_TRAIN = Path("backend/app/data/train.jsonl")
OUT_DEV = Path("backend/app/data/dev.jsonl")

SEED = 42
DEV_FRAC = 0.2  # 20% dev

def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

def main():
    rows = load_jsonl(SRC)
    if len(rows) < 50:
        raise SystemExit("Need at least 50 rows to split reliably.")

    random.seed(SEED)
    random.shuffle(rows)

    n_dev = int(len(rows) * DEV_FRAC)
    dev = rows[:n_dev]
    train = rows[n_dev:]

    write_jsonl(OUT_TRAIN, train)
    write_jsonl(OUT_DEV, dev)

    print(f"Total: {len(rows)}")
    print(f"Train: {len(train)} -> {OUT_TRAIN}")
    print(f"Dev:   {len(dev)} -> {OUT_DEV}")

if __name__ == "__main__":
    main()
