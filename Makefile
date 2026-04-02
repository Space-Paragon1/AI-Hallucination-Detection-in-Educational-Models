.PHONY: test serve frontend install train retrain smoke

# Run all backend tests
test:
	python -m pytest tests/ -v

# Start the FastAPI backend (http://localhost:8000)
serve:
	uvicorn backend.app.main:app --reload

# Start the React dev server (http://localhost:5173)
frontend:
	cd frontend && npm run dev

# Install frontend dependencies
install:
	cd frontend && npm install

# Run full ML pipeline: merge → train → eval → ablation
train:
	bash experiments/run_all.sh

# Retrain model from collected user feedback
retrain:
	python experiments/retrain_from_feedback.py

# Quick API smoke test (requires backend running)
smoke:
	curl -s -X POST http://localhost:8000/score \
	  -H "Content-Type: application/json" \
	  -d "{\"question\":\"Solve: 2x+5=17\",\"model_answer\":\"2x=12 -> x=6\",\"student_level\":\"Algebra I\"}" \
	  | python -m json.tool
