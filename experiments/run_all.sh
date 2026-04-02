#!/usr/bin/env bash
# experiments/run_all.sh
# -------------------------------------------------------
# Reproducible pipeline for AI Hallucination Guard.
# Runs: merge -> train -> eval -> ablation
#
# Usage:  bash experiments/run_all.sh
# -------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "=== AI Hallucination Guard: Experiment Pipeline ==="
echo "    Repo: $REPO_ROOT"
echo ""

cd "$REPO_ROOT"

# Step 1: Merge all source datasets
echo "--- Step 1/4: Merging datasets ---"
python experiments/merge_datasets.py
echo ""

# Step 2: Train with 5-fold CV and model comparison
echo "--- Step 2/4: Training (5-fold CV, model comparison) ---"
python experiments/train.py
echo ""

# Step 3: Evaluate on dev set
echo "--- Step 3/4: Evaluating on dev set ---"
python experiments/eval.py
echo ""

# Step 4: Ablation study
echo "--- Step 4/4: Ablation study ---"
python experiments/ablation.py
echo ""

echo "=== Done. Results in experiments/results/ ==="
ls -lh experiments/results/ 2>/dev/null || true
