# Experiments

## Reproducible Pipeline

Run the full pipeline with a single command:

```bash
bash experiments/run_all.sh
```

This runs four steps in sequence:
1. `merge_datasets.py` — combine and split all data
2. `train.py` — 5-fold CV + model comparison + save best model
3. `eval.py` — dev set evaluation with full breakdowns
4. `ablation.py` — feature importance analysis

All results are saved to `experiments/results/`.

---

## Step 1: Dataset Merging

```bash
python experiments/merge_datasets.py
```

Merges `calc_all.jsonl` (180) + `algebra_hallucination_dataset.jsonl` (300) → 480 examples.
Applies stratified 80/20 split (seed=42).

Outputs:
- `backend/app/data/train.jsonl`
- `backend/app/data/dev.jsonl`

---

## Step 2: Model Training

```bash
python experiments/train.py
```

Trains three candidate models under 5-fold stratified cross-validation:

| Model | Description |
|-------|-------------|
| `LogisticRegression` | LR + isotonic calibration (CalibratedClassifierCV) |
| `RandomForest` | 200 trees, balanced class weights |
| `GradientBoosting` | 200 estimators, lr=0.05, depth=3 |

Best model (by CV AUROC) is retrained on the full train set and saved to `backend/models/`.

Results saved to: `experiments/results/train_results.json`

---

## Step 3: Evaluation

```bash
python experiments/eval.py
```

Evaluates the saved model on `dev.jsonl`.

### Metrics

| Metric | Description |
|--------|-------------|
| AUROC | Area under ROC curve (primary metric) |
| F1 | Harmonic mean of precision/recall at threshold=0.5 |
| Precision | Fraction of flagged answers that are truly hallucinated |
| Recall | Fraction of hallucinations successfully caught |
| Calibration | 10-bin reliability diagram (avg predicted prob vs empirical rate) |

### Breakdowns

- **By domain**: Algebra vs Calculus
- **By error type**: none / arithmetic / reasoning_gap
- **By severity**: 0 (correct) → 3 (severe hallucination)

Outputs:
- `experiments/results/eval_results.json`
- `experiments/results/predictions.csv`

---

## Step 4: Ablation Study

```bash
python experiments/ablation.py
```

Measures the contribution of each verifier feature group by training without it.

| Configuration | Dropped Features |
|---------------|-----------------|
| FULL | None |
| NO_STEP | `step_consistent` |
| NO_VERIFIERS | `step_consistent`, `eq_plug_ok` |
| NO_CALC | `calc_verified` |
| TEXT_ONLY | All verifier features |

Reports CV AUROC and dev metrics for each configuration.
Output: `experiments/results/ablation_results.json`

---

## Step 5: Feedback-Driven Retraining (Active Learning)

```bash
python experiments/retrain_from_feedback.py
```

Combines `train.jsonl` with user-collected `backend/data/feedback.jsonl` and retrains.

Also runs **uncertainty sampling**: identifies predictions in [0.40, 0.60] that
benefit most from human labeling, saving them to `experiments/results/uncertain_samples.json`.

---

## Feature Description

| Feature | Type | Source |
|---------|------|--------|
| `hedge_count` | int | Count of hedging words in answer |
| `confident_count` | int | Count of confident assertions |
| `has_steps` | binary | Answer contains `->`, `\n`, or `=` |
| `step_count` | int | Number of distinct step segments |
| `num_count_q` | int | Numeric values in question |
| `num_count_a` | int | Numeric values in answer |
| `final_found` | binary | Final numeric answer detected |
| `final_val` | float | Numeric value of claimed answer |
| `new_final` | binary | Final answer not in question numbers |
| `sign_error_hint` | binary | Final = negative of a question number |
| `answer_len` | int | Character length of answer |
| `is_calc_prompt` | binary | Question contains calculus keywords |
| `student_level_enc` | int | Ordinal level (-1=unknown, 0–3) |
| `eq_plug_ok` | binary | Algebra equation plug-in passed |
| `step_consistent` | binary | All step transitions are equivalent |
| `calc_verified` | binary | Calculus answer symbolically verified |

---

## Results Directory

After running the full pipeline:

```
experiments/results/
├── train_results.json      # CV scores, best model name
├── eval_results.json       # Full dev metrics + breakdowns
├── predictions.csv         # Per-example predictions
├── ablation_results.json   # Per-configuration metrics
└── uncertain_samples.json  # Uncertainty sampling outputs (after feedback)
```
