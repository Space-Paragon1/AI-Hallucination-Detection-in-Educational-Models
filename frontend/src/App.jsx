import { useState, useEffect } from "react";
import ScoreForm from "./components/ScoreForm";
import ResultCard from "./components/ResultCard";
import FeedbackButton from "./components/FeedbackButton";
import HistoryPanel from "./components/HistoryPanel";
import { scoreAnswer, healthCheck } from "./api/client";
import "./App.css";

function exportHistoryCSV(history) {
  if (!history.length) return;
  const headers = ["question", "model_answer", "risk", "label", "action", "reasons"];
  const rows = history.map((item) => [
    `"${item.question.replace(/"/g, '""')}"`,
    `"${item.modelAnswer.replace(/"/g, '""')}"`,
    item.result.risk.toFixed(4),
    item.result.label,
    item.result.action,
    `"${item.result.reasons.join("; ").replace(/"/g, '""')}"`,
  ]);
  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "hallucination_guard_session.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [currentInput, setCurrentInput] = useState({ question: "", modelAnswer: "" });
  const [backendUp, setBackendUp] = useState(null);

  useEffect(() => {
    healthCheck()
      .then((data) => setBackendUp(data.ok))
      .catch(() => setBackendUp(false));
  }, []);

  const handleSubmit = async ({ question, modelAnswer, studentLevel }) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentInput({ question, modelAnswer });
    try {
      const data = await scoreAnswer(question, modelAnswer, studentLevel);
      setResult(data);
      setHistory((prev) => [{ question, modelAnswer, result: data }, ...prev]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleHistorySelect = (item) => {
    setCurrentInput({ question: item.question, modelAnswer: item.modelAnswer });
    setResult(item.result);
  };

  return (
    <div className="app-layout">
      <HistoryPanel
        history={history}
        onSelect={handleHistorySelect}
        onExport={() => exportHistoryCSV(history)}
      />

      <main className="main-content">
        <header className="app-header">
          <h1>Hallucination Guard</h1>
          <p className="subtitle">AI Math Answer Verification System</p>

          {backendUp === false && (
            <div className="banner banner-error">
              Backend is not reachable. Start the server with:{" "}
              <code>uvicorn backend.app.main:app --reload</code>
            </div>
          )}
          {backendUp === true && (
            <div className="banner banner-ok">Backend connected</div>
          )}
        </header>

        <ScoreForm onSubmit={handleSubmit} loading={loading} />

        {error && <div className="error-box">{error}</div>}

        {result && (
          <>
            <ResultCard result={result} />
            <FeedbackButton
              question={currentInput.question}
              modelAnswer={currentInput.modelAnswer}
            />
          </>
        )}
      </main>
    </div>
  );
}
