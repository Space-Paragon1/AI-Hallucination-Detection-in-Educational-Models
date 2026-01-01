# Hallucination Guard for Educational Math Models

**Hallucination Guard** is a research-oriented system for **detecting, explaining, and mitigating hallucinations in AI tutoring models**, with an initial focus on **Algebra** and a planned extension to **Calculus**.

This project is part of a broader **AI + Education + Systems** research portfolio.  
The core idea is to place a *verification and risk-assessment layer* between an educational AI model and a student, reducing the likelihood that **confident but incorrect mathematical answers** are presented as truth.

---

## 🚩 Problem Motivation

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

## 🎯 Project Goals

- Detect hallucinated math answers using **verifiable signals**
- Assign a **calibrated risk score** (0–1)
- Provide **human-interpretable explanations** for why an answer is risky
- Enforce **policies** (allow / ask / block) appropriate for educational settings
- Build a system that scales cleanly from Algebra → Calculus → other STEM domains

---

## 🧱 System Architecture (High Level)

Question + Model Answer
│
▼
Feature Extraction (textual + math signals)
│
▼
Math Verifiers (Algebra now, Calculus later)
│
▼
Risk Model (calibrated classifier)
│
▼
Policy Engine (allow / clarify / block)
│
▼
Student-Safe Response


---

## 📐 Phase 1A: Algebra Hallucination Detection (Current)

**Scope**
- Linear equations
- Basic algebraic manipulation
- Arithmetic and reasoning errors

**Key Techniques**
- Numeric answer extraction
- Equation plug-in verification
- Heuristic + ML-based risk estimation
- Controlled error dataset construction

**Outputs**
- `risk`: probability of hallucination
- `label`: low / medium / high risk
- `action`: allow / ask_clarifying / block_and_verify
- `reasons`: interpretable explanations

---

## 📊 Dataset Strategy

There is no off-the-shelf dataset for *educational hallucinations*.

Instead, the dataset is constructed via **controlled error generation**:

- ~100 algebra questions
- For each question:
  - 1 correct solution
  - 2 plausible but incorrect solutions
- Total: **300+ labeled examples**

Each example is stored in JSONL format with:
- hallucination label
- error type
- severity level

---

## 🗂 Repository Structure

hallucination-guard-math/
├── backend/
│ ├── app/
│ │ ├── main.py # FastAPI entrypoint
│ │ ├── routers/ # API endpoints
│ │ ├── core/ # schemas, scoring, model loading
│ │ ├── features/ # algebra feature extraction
│ │ ├── verifiers/ # math verifiers (algebra, calculus stubs)
│ │ ├── policy/ # risk → action logic
│ │ └── data/ # train/dev datasets
│ └── models/ # trained model artifacts
├── experiments/
│ ├── train.py # model training
│ └── eval.py # evaluation scripts
├── docs/
└── README.md


---

## 🚀 Running the Project

### Requirements
- **Python 3.10+**
- Windows / macOS / Linux

### Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r backend/requirements.txt

Start the API
From the repo root: uvicorn backend.app.main:app --reload

Useful Endpoints
Health check:
http://127.0.0.1:8000/health

Interactive API docs:
http://127.0.0.1:8000/docs

Score an answer:
POST /score

🧪 Example Request
{
  "question": "Solve for x: 2x + 5 = 17",
  "model_answer": "2x + 5 = 17 -> 2x = 10 -> x = 5",
  "student_level": "Algebra I"
}

Example Response
{
  "risk": 0.91,
  "label": "high_risk",
  "action": "block_and_verify",
  "reasons": [
    "Final answer does not satisfy the equation when plugged in."
  ]
}

🔬 Evaluation Metrics
AUROC (hallucination detection)
F1 score
Calibration quality (risk ≈ true error rate)
False-positive cost (blocking correct answers)
False-negative cost (allowing hallucinations)

🔮 Planned Extensions (Phase 1B & Beyond)
Symbolic verification using SymPy
Derivative and integral checking (Calculus)
Limit evaluation (symbolic + numeric)
Conceptual explanation quality analysis
Adaptive tutoring policies based on student level
Expansion to Chemistry and Physics domains

📌 Research Positioning
This project sits at the intersection of:
AI Safety
Educational Technology
ML Systems
Human-Centered AI
It is designed to be:
Reproducible
Interpretable
Extensible
Grounded in verifiable mathematics

THIS PROJECT IS STILL IN PROGRESS.
