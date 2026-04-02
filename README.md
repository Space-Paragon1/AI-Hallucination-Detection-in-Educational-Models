# Hallucination Guard for Educational Math Models

**Hallucination Guard** is a research system for **detecting, explaining, and mitigating hallucinations in AI tutoring models**, with support for **Algebra** and **Calculus**.

The core idea is to place a *verification and risk-assessment layer* between an educational AI model and a student, reducing the likelihood that **confident but incorrect mathematical answers** are presented as truth.

---

## Problem Motivation

Educational AI systems can produce answers that are:
- Fluent and confident
- Step-by-step and pedagogical
- **Mathematically incorrect**

In learning contexts, these hallucinations are especially harmful because students may trust incorrect reasoning, errors compound over time, and models often fail *silently* without expressing uncertainty.

---

## System Architecture

```
Question + Model Answer
        |
        v
Feature Extraction (textual + math signals)
        |
        v
Math Verifiers (Algebra + Calculus via SymPy)
        |
        v
Risk Model (calibrated RandomForest classifier)
        |
        v
Policy Engine — thresholds vary by student level
        |
        v
Student-Safe Response (allow / clarify / block)
```

---

## Features

### Algebra Verification
- **Equation plug-in**: Extracts the final answer, plugs it back into the original equation, checks if it holds
- **Step consistency**: Verifies that each algebraic step is a valid transformation of the previous one
- Handles implicit multiplication (e.g., `2x`, `3(x-2)`)

### Calculus Verification
- **Derivatives**: Symbolically differentiates and compares with the claimed answer (via SymPy)
- **Indefinite integrals**: Differentiates the claimed antiderivative to verify correctness
- **Definite integrals**: Numerically integrates bounds and compares with claimed value
- **Limits**: Evaluates limits symbolically, handles `∞`, `-∞`, and DNE cases

### ML Risk Model
- Best model: **RandomForest** (selected by 5-fold CV AUROC)
- Trained on **480 labeled examples** (300 algebra + 180 calculus)
- CV AUROC: **1.000** | Dev AUROC: **1.000** | Dev F1: **1.000**
- Hybrid scoring: `risk = max(ml_risk, heuristic_risk)`

### Policy Engine
- Thresholds tighten for lower student levels (Pre-Algebra is strictest)
- `risk ≥ 0.80` → **block_and_verify**
- `risk ≥ 0.50` → **ask_clarifying_or_verify**
- `risk < 0.50` → **allow**

### React Frontend
- Visual risk gauge (SVG, color-coded green/yellow/red) with ±2% confidence band
- Input form: question, model answer, student level
- Action badge and human-readable reason cards with icons
- Feedback buttons (Correct / Hallucinated) with optional notes
- Session history sidebar with CSV export
- Expandable feature inspector for debugging

---

## Repository Structure

```
hallucination-detector/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint (CORS enabled)
│   │   ├── routers/             # /score and /feedback endpoints
│   │   ├── core/                # schemas, scoring pipeline, model loading
│   │   ├── features/            # text + structural feature extraction
│   │   ├── verifiers/           # SymPy-based algebra & calculus verifiers
│   │   ├── policy/              # risk → (label, action) + reason generation
│   │   └── data/                # train.jsonl, dev.jsonl
│   ├── models/                  # trained .joblib artifacts (git-ignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app: state, history, CSV export
│   │   ├── components/          # ScoreForm, ResultCard, FeedbackButton, HistoryPanel
│   │   └── api/client.js        # HTTP client for /score and /feedback
│   └── package.json
├── experiments/
│   ├── run_all.sh               # Full pipeline: merge → train → eval → ablation
│   ├── merge_datasets.py        # Combine sources, 80/20 stratified split
│   ├── train.py                 # 5-fold CV, 3 model comparison, save best
│   ├── eval.py                  # Dev evaluation with per-domain breakdowns
│   ├── ablation.py              # Feature importance study
│   ├── retrain_from_feedback.py # Active learning from user feedback
│   └── results/                 # Output metrics (git-ignored)
├── tests/
│   ├── conftest.py
│   ├── test_score_endpoint.py
│   ├── test_feedback_endpoint.py
│   ├── test_verifiers.py
│   ├── test_policy.py
│   └── test_features.py
├── docs/
│   ├── architecture.md
│   ├── dataset.md
│   ├── experiments.md
│   └── model_card.md
├── Dockerfile
├── Makefile
└── README.md
```

---

## Quick Start

### Requirements
- Python 3.10+
- Node.js 18+

### Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .\.venv\Scripts\Activate.ps1   # Windows PowerShell

# 2. Install Python dependencies
pip install -r backend/requirements.txt
pip install pytest httpx          # for tests

# 3. Install frontend dependencies
make install
```

### Running

```bash
make serve       # Start backend  →  http://localhost:8000
make frontend    # Start frontend →  http://localhost:5173
```

### Testing

```bash
make test        # Run all 37 backend tests
make smoke       # Quick API smoke test (requires backend running)
```

### ML Pipeline

```bash
make train       # merge → train → eval → ablation  (full pipeline)
make retrain     # Retrain from collected user feedback
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Backend health check |
| `POST` | `/score` | Score a question/answer pair |
| `POST` | `/feedback` | Submit a correction label |

Interactive docs: `http://localhost:8000/docs`

### Example Request

```json
POST /score
{
  "question": "Solve for x: 2x + 5 = 17",
  "model_answer": "2x + 5 = 17 -> 2x = 10 -> x = 5",
  "student_level": "Algebra I"
}
```

### Example Response

```json
{
  "risk": 0.91,
  "label": "high_risk",
  "action": "block_and_verify",
  "reasons": [
    "Final answer does not satisfy the equation when plugged in.",
    "One or more algebra steps appear invalid (equations change incorrectly)."
  ]
}
```

---

## Ablation Summary

| Configuration | Dev AUROC | Dev F1 |
|---|---|---|
| Full model | 1.000 | 1.000 |
| No step verifier | 1.000 | 1.000 |
| No calc verifier | 1.000 | 1.000 |
| **No verifiers** | **0.910** | **0.877** |
| **Text only** | **0.910** | **0.877** |

Symbolic verifiers (`eq_plug_ok`, `step_consistent`) are the most important features — removing them drops F1 by ~12 points.

---

## Docker

```bash
docker build -t hallucination-guard .
docker run -p 8000:8000 hallucination-guard
```

---

## Research Positioning

This project sits at the intersection of AI Safety, Educational Technology, ML Systems, and Human-Centered AI. It is designed to be reproducible, interpretable, extensible, and grounded in verifiable mathematics.
