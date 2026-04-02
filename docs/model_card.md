# Model Card: Hallucination Risk Classifier

## Model Overview

**Name:** Hallucination Risk Classifier  
**Version:** 1.0  
**Type:** Binary classifier (hallucinated=1, correct=0)  
**Output:** Calibrated probability (0.0–1.0) representing hallucination risk

## Intended Use

This model is designed to be used as a **verification layer in AI math tutoring systems**. It intercepts AI-generated math answers before they reach students and flags likely hallucinations for review.

**Primary use case:** Educational AI safety — detecting incorrect AI answers in algebra and calculus tutoring (grades 6–12 and introductory college).

**Not intended for:** General-purpose factual verification, non-mathematical domains, or high-stakes automated decisions without human oversight.

## Training Data

- **Domain:** Algebra (linear equations) and Calculus (derivatives, integrals, limits)
- **Size:** ~384 training examples (80% of 480 total)
- **Generation:** Synthetic — programmatically generated correct answers and hallucination variants
- **Class balance:** ~2:1 hallucinated:correct (reflects that AI errors are more common than correct answers in the data generation process)

See `docs/dataset.md` for full details.

## Model Architecture

The risk score is computed as:

```
final_risk = max(heuristic_risk, ml_model_risk) + student_level_adjustment
```

**Heuristic component:** Rule-based overrides from symbolic verifiers (SymPy):
- Calculus symbolic mismatch → 0.95
- Algebra plug-in failure → 0.90
- No steps shown → 0.60

**ML component:** Best of {LogisticRegression + isotonic calibration, RandomForest, GradientBoosting} selected by 5-fold AUROC.

**Probability calibration:** CalibratedClassifierCV (isotonic method) is applied to LogisticRegression to ensure output probabilities are well-calibrated.

## Features

16 features in total — see `docs/experiments.md#feature-description` for the full list. Key features include:
- Symbolic verifier signals (eq_plug_ok, step_consistent, calc_verified)
- Linguistic signals (hedge_count, confident_count, has_steps)
- Student level encoding (ordinal: 0=Pre-Algebra to 3=Calculus)

## Evaluation

Evaluated on a held-out dev set (~96 examples, stratified).

| Metric | Value |
|--------|-------|
| AUROC | Run `python experiments/eval.py` |
| F1 | Run `python experiments/eval.py` |
| Calibration | See `experiments/results/eval_results.json` |

Per-domain and per-error-type breakdowns are available in `experiments/results/eval_results.json` after running the pipeline.

## Limitations

1. **Synthetic data only.** The training data was programmatically generated. Performance on real AI tutor outputs has not been measured.
2. **Limited algebra coverage.** Only solves for single variable x. Does not handle systems of equations, polynomial factoring, or inequalities.
3. **Calculus scope.** Handles single-variable derivatives, indefinite/definite integrals, and limits. No support for multivariable calculus, series, or differential equations.
4. **Small training set.** ~384 examples is small for production. The model benefits significantly from feedback-driven retraining (`experiments/retrain_from_feedback.py`).
5. **Expression parsing fragility.** SymPy-based verification may fail on non-standard notation or ambiguous expressions, falling back to heuristic scoring.
6. **Student level is ordinal only.** The model encodes student level as 0–3. The relationship between level and error rate is assumed monotonic and may not hold for all topics.

## Ethical Considerations

- **False positives** (blocking a correct answer) may frustrate students and undermine trust in the tutoring system. Monitor precision carefully.
- **False negatives** (passing a hallucinated answer) may mislead students, which is the primary harm this system is designed to prevent.
- **Feedback collection** is used only for model improvement. No personally identifiable information should be included in feedback notes.
- This model should be used as a **support tool** for educators and system designers, not as an autonomous gatekeeper without human oversight.

## How to Update the Model

```bash
# 1. Collect feedback via the /feedback endpoint (stored in backend/data/feedback.jsonl)
# 2. Retrain incorporating feedback + uncertainty sampling:
python experiments/retrain_from_feedback.py

# 3. Or run the full pipeline fresh:
bash experiments/run_all.sh
```
