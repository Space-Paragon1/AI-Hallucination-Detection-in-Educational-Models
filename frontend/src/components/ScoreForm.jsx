import { useState } from "react";

export default function ScoreForm({ onSubmit, loading }) {
  const [question, setQuestion] = useState("");
  const [modelAnswer, setModelAnswer] = useState("");
  const [studentLevel, setStudentLevel] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim() || !modelAnswer.trim()) return;
    onSubmit({ question, modelAnswer, studentLevel });
  };

  return (
    <form className="score-form" onSubmit={handleSubmit}>
      <h2>Check an AI Answer</h2>

      <label>
        Question
        <textarea
          rows={3}
          placeholder="e.g. Solve for x: 2x + 5 = 17"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          required
        />
      </label>

      <label>
        Model Answer
        <textarea
          rows={4}
          placeholder="e.g. 2x + 5 = 17 -> 2x = 12 -> x = 6"
          value={modelAnswer}
          onChange={(e) => setModelAnswer(e.target.value)}
          required
        />
      </label>

      <label>
        Student Level <span className="optional">(optional)</span>
        <select value={studentLevel} onChange={(e) => setStudentLevel(e.target.value)}>
          <option value="">-- select --</option>
          <option value="Pre-Algebra">Pre-Algebra</option>
          <option value="Algebra I">Algebra I</option>
          <option value="Algebra II">Algebra II</option>
          <option value="Calculus">Calculus</option>
        </select>
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Answer"}
      </button>
    </form>
  );
}
