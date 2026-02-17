# Hallucination Guard for Educational Math Models

**Hallucination Guard** is a research-oriented system for **detecting, explaining, and mitigating hallucinations in AI tutoring models**, with support for **Algebra** and **Calculus**.

This project is part of a broader **AI + Education + Systems** research portfolio.
The core idea is to place a *verification and risk-assessment layer* between an educational AI model and a student, reducing the likelihood that **confident but incorrect mathematical answers** are presented as truth.

---

## Problem Motivation

Educational AI systems can produce answers that are:
- Fluent and confident
- Step-by-step and pedagogical
- **Mathematically incorrect**

In learning contexts, these hallucinations are especially harmful because:
- Students may trust incorrect reasoning
- Errors can compound over time
- Models often fail *silently* without expressing uncertainty

This project addresses that gap by detecting hallucination risk **before** an answer reaches the learner.

---

## Project Goals

- Detect hallucinated math answers using **verifiable signals**
- Assign a **calibrated risk score** (0-1)
- Provide **human-interpretable explanations** for why an answer is risky
- Enforce **policies** (allow / ask / block) appropriate for educational settings
- Build a system that scales cleanly from Algebra to Calculus to other STEM domains

---

## System Architecture

```
Question + Model Answer
        |
        v
Feature Extraction (textual + math signals)
        |
        v
Math Verifiers (Algebra + Calculus)
        |
        v
Risk Model (calibrated classifier)
        |
        v
Policy Engine (allow / clarify / block)
        |
        v
Student-Safe Response
```

---

## Features

### Algebra Verification
- **Equation plug-in**: Extracts the final answer, plugs it back into the original equation, checks if it holds
- **Step consistency**: Verifies that each algebraic step is a valid transformation of the previous one
- Handles implicit multiplication (e.g., `2x`, `3(x-2)`)

### Calculus Verification
- **Derivatives**: Symbolically differentiates and compares with the claimed answer (via SymPy)
- **Integrals**: Differentiates the claimed antiderivative to verify
- **Limits**: Evaluates limits symbolically and compares

### ML Risk Model
- Logistic Regression with isotonic calibration
- Trained on 480+ labeled examples (algebra + calculus)
- Features: hedge words, confidence markers, step presence, numeric analysis

### Policy Engine
- `risk >= 0.80` -> **block_and_verify** (high risk)
- `risk >= 0.50` -> **ask_clarifying_or_verify** (medium risk)
- `risk < 0.50` -> **allow** (low risk)

### React Frontend
- Visual risk gauge (color-coded green/yellow/red)
- Input form for question + model answer + student level
- Action badge and interpretable reasons
- Feedback buttons (correct / hallucinated)
- Session history sidebar
- Expandable feature details for debugging

---

## Repository Structure

```
hallucination-detector/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint (CORS enabled)
│   │   ├── routers/             # API endpoints (/score, /feedback)
│   │   ├── core/                # schemas, scoring, model loading
│   │   ├── features/            # algebra feature extraction
│   │   ├── verifiers/           # math verifiers (algebra, calculus)
│   │   ├── policy/              # risk -> action logic
│   │   └── data/                # train/dev datasets
│   ├── models/                  # trained model artifacts (.joblib)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── components/          # ScoreForm, ResultCard, FeedbackButton, HistoryPanel
│   │   └── api/client.js        # API client for /score and /feedback
│   ├── index.html
│   └── package.json
├── experiments/
│   ├── train.py                 # Model training
│   ├── eval.py                  # Evaluation scripts
│   └── ablation.py              # Feature ablation study
├── tests/
│   ├── conftest.py              # pytest fixtures
│   ├── test_score_endpoint.py   # API endpoint tests
│   ├── test_feedback_endpoint.py
│   ├── test_verifiers.py        # Algebra verifier unit tests
│   ├── test_policy.py           # Policy engine tests
│   └── test_features.py         # Feature extraction tests
└── README.md
```

---

## Running the Project

### Requirements
- **Python 3.10+**
- **Node.js 18+**

### Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r backend/requirements.txt

# Start the API
uvicorn backend.app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and the backend API at `http://localhost:8000`.

### Running Tests
```bash
pip install pytest httpx
python -m pytest tests/ -v
```

### Useful Endpoints
- Health check: `GET http://localhost:8000/health`
- Interactive API docs: `http://localhost:8000/docs`
- Score an answer: `POST http://localhost:8000/score`
- Submit feedback: `POST http://localhost:8000/feedback`

---

## Example Request

```json
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

## Evaluation Metrics
- AUROC (hallucination detection)
- F1 score
- Calibration quality (risk ~ true error rate)
- False-positive cost (blocking correct answers)
- False-negative cost (allowing hallucinations)

---

## Research Positioning

This project sits at the intersection of:
- AI Safety
- Educational Technology
- ML Systems
- Human-Centered AI

It is designed to be:
- Reproducible
- Interpretable
- Extensible
- Grounded in verifiable mathematics

---

THIS PROJECT IS STILL IN PROGRESS.
