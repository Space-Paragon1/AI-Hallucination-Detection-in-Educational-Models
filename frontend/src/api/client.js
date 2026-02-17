const BASE = "http://localhost:8000";

export async function scoreAnswer(question, modelAnswer, studentLevel) {
  const body = { question, model_answer: modelAnswer };
  if (studentLevel) body.student_level = studentLevel;

  const res = await fetch(`${BASE}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Score request failed");
  }
  return res.json();
}

export async function submitFeedback(question, modelAnswer, hallucinated, notes) {
  const body = {
    question,
    model_answer: modelAnswer,
    user_label_hallucinated: hallucinated ? 1 : 0,
  };
  if (notes) body.notes = notes;

  const res = await fetch(`${BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Feedback submission failed");
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}
