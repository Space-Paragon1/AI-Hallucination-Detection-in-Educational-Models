import { useState } from "react";
import { submitFeedback } from "../api/client";

export default function FeedbackButton({ question, modelAnswer }) {
  const [sent, setSent] = useState(null); // null | "correct" | "hallucinated"
  const [error, setError] = useState(null);

  if (!question || !modelAnswer) return null;

  const send = async (hallucinated) => {
    try {
      setError(null);
      await submitFeedback(question, modelAnswer, hallucinated);
      setSent(hallucinated ? "hallucinated" : "correct");
    } catch {
      setError("Failed to send feedback");
    }
  };

  if (sent) {
    return (
      <div className="feedback-sent">
        Feedback recorded: <strong>{sent}</strong>
      </div>
    );
  }

  return (
    <div className="feedback-buttons">
      <span>Was this answer correct?</span>
      <button className="btn-correct" onClick={() => send(false)}>
        Correct
      </button>
      <button className="btn-hallucinated" onClick={() => send(true)}>
        Hallucinated
      </button>
      {error && <span className="feedback-error">{error}</span>}
    </div>
  );
}
