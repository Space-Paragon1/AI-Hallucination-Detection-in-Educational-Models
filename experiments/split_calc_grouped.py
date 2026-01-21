import json
from pathlib import Path
from collections import defaultdict
import random

SRC = Path("backend/app/data/calc_all.jsonl")
TRAIN = Path("backend/app/data/calc_train.jsonl")
DEV = Path("backend/app/data/calc_dev.jsonl")

SEED = 42
DEV_FRAC = 0.2

def main():
    random.seed(SEED)

    lines = [ln for ln in SRC.read_text(encoding="utf-8").splitlines() if ln.strip()]
    items = [json.loads(ln) for ln in lines]

    # Group by question text so all variants stay together
    groups = defaultdict(list)
    for ex in items:
        groups[ex["question"]].append(ex)

    questions = list(groups.keys())
    random.shuffle(questions)

    n_dev = max(1, int(len(questions) * DEV_FRAC))
    dev_q = set(questions[:n_dev])

    train_lines, dev_lines = [], []
    for q, exs in groups.items():
        for ex in exs:
            if q in dev_q:
                dev_lines.append(json.dumps(ex, ensure_ascii=False))
            else:
                train_lines.append(json.dumps(ex, ensure_ascii=False))

    TRAIN.write_text("\n".join(train_lines) + "\n", encoding="utf-8")
    DEV.write_text("\n".join(dev_lines) + "\n", encoding="utf-8")

    print(f"Groups total: {len(questions)}")
    print(f"Groups dev:   {len(dev_q)}")
    print(f"Train ex:     {len(train_lines)} -> {TRAIN}")
    print(f"Dev ex:       {len(dev_lines)} -> {DEV}")

if __name__ == "__main__":
    main()
