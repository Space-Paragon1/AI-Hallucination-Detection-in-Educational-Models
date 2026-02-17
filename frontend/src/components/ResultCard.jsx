import { useState } from "react";

const LABEL_COLORS = {
  low_risk: "#22c55e",
  medium_risk: "#f59e0b",
  high_risk: "#ef4444",
};

const ACTION_LABELS = {
  allow: "Allow",
  ask_clarifying_or_verify: "Needs Clarification",
  block_and_verify: "Blocked",
};

export default function ResultCard({ result }) {
  const [showFeatures, setShowFeatures] = useState(false);
  if (!result) return null;

  const { risk, label, action, reasons, features } = result;
  const pct = Math.round(risk * 100);
  const color = LABEL_COLORS[label] || "#6b7280";

  return (
    <div className="result-card">
      <div className="risk-gauge">
        <svg viewBox="0 0 120 120" width="140" height="140">
          {/* background track */}
          <circle
            cx="60" cy="60" r="50"
            fill="none" stroke="#e5e7eb" strokeWidth="12"
            strokeDasharray="235.6" strokeDashoffset="0"
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
          />
          {/* filled arc */}
          <circle
            cx="60" cy="60" r="50"
            fill="none" stroke={color} strokeWidth="12"
            strokeDasharray="235.6"
            strokeDashoffset={235.6 * (1 - risk)}
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
          <text x="60" y="55" textAnchor="middle" fontSize="28" fontWeight="bold" fill={color}>
            {pct}%
          </text>
          <text x="60" y="75" textAnchor="middle" fontSize="11" fill="#6b7280">
            risk
          </text>
        </svg>
      </div>

      <div className="result-details">
        <span className="badge" style={{ backgroundColor: color }}>
          {ACTION_LABELS[action] || action}
        </span>

        <h3>Reasons</h3>
        <ul className="reasons-list">
          {reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>

        <button
          className="toggle-features"
          onClick={() => setShowFeatures(!showFeatures)}
        >
          {showFeatures ? "Hide" : "Show"} Feature Details
        </button>

        {showFeatures && (
          <pre className="features-json">
            {JSON.stringify(features, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
