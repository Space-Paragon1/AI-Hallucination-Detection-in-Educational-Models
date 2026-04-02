import { useState } from "react";
import { submitFeedback } from "../api/client";

export default function FeedbackButton({ question, modelAnswer }) {
  const [sent, setSent] = useState(null);       // null | "correct" | "hallucinated"
  const [error, setError] = useState(null);
  const [notes, setNotes] = useState("");
  const [showNotes, setShowNotes] = useState(false);

  if (!question || !modelAnswer) return null;

  const send = async (hallucinated) => {
    try {
      setError(null);
      await submitFeedback(
        question,
        modelAnswer,
        hallucinated,
        notes.trim() || undefined,
      );
      setSent(hallucinated ? "hallucinated" : "correct");
    } catch {
      setError("Failed to send feedback. Is the backend running?");
    }
  };

  if (sent) {
    return (
      <div className="feedback-sent">
        Feedback recorded: <strong>{sent}</strong>
        {notes && <span className="feedback-notes-badge"> (with notes)</span>}
      </div>
    );
  }

  return (
    <div className="feedback-buttons">
      <span className="feedback-label">Was this answer correct?</span>

      <div className="feedback-actions">
        <button className="btn-correct" onClick={() => send(false)}>
          ✓ Correct
        </button>
        <button className="btn-hallucinated" onClick={() => send(true)}>
          ✗ Hallucinated
        </button>
        <button
          className="btn-notes-toggle"
          onClick={() => setShowNotes(!showNotes)}
          title="Add optional notes about the error"
        >
          {showNotes ? "Hide notes" : "+ Notes"}
        </button>
      </div>

      {showNotes && (
        <textarea
          className="feedback-notes-input"
          rows={2}
          placeholder="Optional: describe the specific error (e.g. sign error, wrong formula)..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      )}

      {error && <span className="feedback-error">{error}</span>}
    </div>
  );
}
