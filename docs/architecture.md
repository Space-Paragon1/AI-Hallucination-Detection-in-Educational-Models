# System Architecture

## Overview

Hallucination Guard is a verification layer placed between an AI tutoring model and a student. It intercepts the AI's answer, runs symbolic and statistical checks, and returns a calibrated risk score with human-readable explanations before the answer is displayed.

```
Student Input
    │
    ▼
AI Tutoring Model
    │
    ▼ (question, model_answer, student_level)
┌───────────────────────────────────────────┐
│           Hallucination Guard API          │
│                                           │
│  ┌──────────────────────────────────┐     │
│  │       Feature Extraction         │     │
│  │  - Text features (hedges, steps) │     │
│  │  - Number extraction             │     │
│  │  - Student level encoding        │     │
│  └──────────────┬───────────────────┘     │
│                 │                         │
│  ┌──────────────▼───────────────────┐     │
│  │       Symbolic Verifiers         │     │
│  │  - Algebra plug-in (SymPy)       │     │
│  │  - Step consistency (SymPy)      │     │
│  │  - Calculus verifier (SymPy)     │     │
│  │    • Derivatives                 │     │
│  │    • Indefinite integrals        │     │
│  │    • Definite integrals          │     │
│  │    • Limits (incl. ∞, DNE)       │     │
│  └──────────────┬───────────────────┘     │
│                 │                         │
│  ┌──────────────▼───────────────────┐     │
│  │         Risk Scoring             │     │
│  │  - Heuristic overrides           │     │
│  │  - ML model (LR/RF/GBM)          │     │
│  │  - Student-level adjustment      │     │
│  │  - max(heuristic, ML)            │     │
│  └──────────────┬───────────────────┘     │
│                 │                         │
│  ┌──────────────▼───────────────────┐     │
│  │         Policy Engine            │     │
│  │  - Risk → (label, action)        │     │
│  │  - Student-level thresholds      │     │
│  │  - Reason generation             │     │
│  └──────────────┬───────────────────┘     │
└─────────────────┼─────────────────────────┘
                  │
    ┌─────────────▼─────────────┐
    │   ScoreResponse            │
    │   risk: 0.0–1.0            │
    │   label: low/med/high_risk │
    │   action: allow/clarify/   │
    │           block            │
    │   reasons: [...]           │
    │   features: {...}          │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │   React Frontend           │
    │   - Risk gauge (±2% band)  │
    │   - Reason cards           │
    │   - Feedback collection    │
    │   - Session history + CSV  │
    └───────────────────────────┘
          │
          ▼ (feedback)
    feedback.jsonl → retrain_from_feedback.py
```

## Component Responsibilities

### Backend (`backend/app/`)

| Module | Responsibility |
|--------|---------------|
| `routers/score.py` | POST /score endpoint — orchestrates feature extraction, scoring, policy |
| `routers/feedback.py` | POST /feedback — appends user labels to `feedback.jsonl` |
| `core/scoring.py` | `build_features()`, `heuristic_risk()` with student-level adjustment |
| `core/model_store.py` | Loads trained models from `backend/models/` |
| `features/algebra_features.py` | Text + structural feature extraction; student level encoding |
| `verifiers/linear_equation.py` | SymPy-based equation plug-in verification |
| `verifiers/step_checker.py` | SymPy-based step consistency checking |
| `verifiers/calculus_verify.py` | SymPy-based derivative/integral/limit verification |
| `policy/decision.py` | Risk → action mapping with per-level thresholds; reason generation |

### ML Pipeline (`experiments/`)

| Script | Purpose |
|--------|---------|
| `merge_datasets.py` | Merges all source datasets into stratified train/dev |
| `train.py` | 5-fold CV, model comparison, saves best model |
| `eval.py` | Dev set evaluation with per-domain/error/severity breakdowns |
| `ablation.py` | Measures importance of each verifier feature group |
| `retrain_from_feedback.py` | Active learning loop: feedback + uncertainty sampling |
| `run_all.sh` | Single script for full reproducible pipeline |

### Frontend (`frontend/src/`)

| Component | Responsibility |
|-----------|---------------|
| `App.jsx` | State management, submit handler, CSV export |
| `ScoreForm.jsx` | Q+A input form with student level selector |
| `ResultCard.jsx` | Risk gauge (with confidence band), reason cards |
| `FeedbackButton.jsx` | Correct/Hallucinated buttons + optional notes field |
| `HistoryPanel.jsx` | Session history sidebar with CSV download |

## Risk Score Formula

```
risk = max(ml_risk, heuristic_risk) + student_level_adjustment

Heuristic overrides (applied before ML):
  calculus mismatch    → 0.95
  calculus verified    → 0.20
  calc parse unclear   → 0.55
  algebra plug-in fail → 0.90
  no steps shown       → 0.60
  default              → 0.20

Student-level adjustments:
  Pre-Algebra   +0.10  (strictest)
  Algebra I     +0.05
  Algebra II    +0.00
  Calculus      -0.05  (most lenient)
```

## Risk Thresholds (by Student Level)

| Level | High Threshold | Medium Threshold |
|-------|---------------|-----------------|
| Pre-Algebra | 0.65 | 0.35 |
| Algebra I | 0.70 | 0.40 |
| Algebra II | 0.75 | 0.45 |
| Calculus | 0.80 | 0.50 |
