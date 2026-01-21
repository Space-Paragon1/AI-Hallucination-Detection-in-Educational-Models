from pathlib import Path

SRC = Path("backend/app/data/calc_all.jsonl")
TRAIN = Path("backend/app/data/calc_train.jsonl")
DEV = Path("backend/app/data/calc_dev.jsonl")

# simple deterministic split: every 5th example goes to dev (~20%)
def main():
    lines = SRC.read_text(encoding="utf-8").splitlines()
    train_lines, dev_lines = [], []

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if i % 5 == 0:
            dev_lines.append(line)
        else:
            train_lines.append(line)

    TRAIN.write_text("\n".join(train_lines) + "\n", encoding="utf-8")
    DEV.write_text("\n".join(dev_lines) + "\n", encoding="utf-8")

    print(f"Total: {len(lines)}")
    print(f"Train: {len(train_lines)} -> {TRAIN}")
    print(f"Dev:   {len(dev_lines)} -> {DEV}")

if __name__ == "__main__":
    main()
