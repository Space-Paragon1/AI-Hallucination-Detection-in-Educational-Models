const LABEL_COLORS = {
  low_risk: "#22c55e",
  medium_risk: "#f59e0b",
  high_risk: "#ef4444",
};

export default function HistoryPanel({ history, onSelect, onExport }) {
  if (history.length === 0) return null;

  return (
    <aside className="history-panel">
      <div className="history-header">
        <h3>Session History</h3>
        {history.length > 0 && (
          <button
            className="btn-export"
            onClick={onExport}
            title="Export session as CSV"
          >
            ↓ CSV
          </button>
        )}
      </div>

      <ul>
        {history.map((item, i) => (
          <li key={i} onClick={() => onSelect(item)} className="history-item">
            <span
              className="history-dot"
              style={{ backgroundColor: LABEL_COLORS[item.result.label] }}
            />
            <div className="history-text">
              <span className="history-q">
                {item.question.length > 50
                  ? item.question.slice(0, 50) + "…"
                  : item.question}
              </span>
              <span
                className="history-risk"
                style={{ color: LABEL_COLORS[item.result.label] }}
              >
                {Math.round(item.result.risk * 100)}% risk
              </span>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
