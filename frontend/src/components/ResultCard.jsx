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

const ACTION_ICONS = {
  allow: "✓",
  ask_clarifying_or_verify: "?",
  block_and_verify: "✗",
};

// Map reason substrings to icons for at-a-glance reading
const REASON_PATTERNS = [
  ["steps appear invalid", "⚠"],
  ["does not satisfy", "✗"],
  ["step-by-step", "📋"],
  ["unrelated to quantities", "🔢"],
  ["sign", "±"],
  ["symbolic verification", "∑"],
  ["uncertainty markers", "~"],
  ["patterns", "ℹ"],
];

function getReasonIcon(reason) {
  const lower = reason.toLowerCase();
  for (const [key, icon] of REASON_PATTERNS) {
    if (lower.includes(key)) return icon;
  }
  return "ℹ";
}

function getRiskBand(risk) {
  if (risk >= 0.80) return "High Risk";
  if (risk >= 0.50) return "Medium Risk";
  return "Low Risk";
}

// Illustrative ±2% confidence margin (model uncertainty visualization)
function getConfidenceBand(risk) {
  return {
    lo: Math.max(0, risk - 0.02),
    hi: Math.min(1, risk + 0.02),
  };
}

const CIRC = 2 * Math.PI * 50; // circumference for r=50

export default function ResultCard({ result }) {
  const [showFeatures, setShowFeatures] = useState(false);
  if (!result) return null;

  const { risk, label, action, reasons, features } = result;
  const pct = Math.round(risk * 100);
  const color = LABEL_COLORS[label] || "#6b7280";
  const band = getConfidenceBand(risk);

  return (
    <div className="result-card">
      {/* Circular risk gauge with confidence band */}
      <div className="risk-gauge">
        <svg viewBox="0 0 120 120" width="160" height="160">
          {/* Background track */}
          <circle
            cx="60" cy="60" r="50"
            fill="none" stroke="#e5e7eb" strokeWidth="10"
            strokeDasharray={CIRC} strokeDashoffset="0"
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
          />
          {/* Confidence band (wider, transparent arc) */}
          <circle
            cx="60" cy="60" r="50"
            fill="none" stroke={color} strokeWidth="14" opacity="0.18"
            strokeDasharray={CIRC}
            strokeDashoffset={CIRC * (1 - band.hi)}
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
          />
          {/* Main risk arc */}
          <circle
            cx="60" cy="60" r="50"
            fill="none" stroke={color} strokeWidth="10"
            strokeDasharray={CIRC}
            strokeDashoffset={CIRC * (1 - risk)}
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
          <text x="60" y="50" textAnchor="middle" fontSize="26" fontWeight="bold" fill={color}>
            {pct}%
          </text>
          <text x="60" y="66" textAnchor="middle" fontSize="10" fill="#6b7280">
            {getRiskBand(risk)}
          </text>
          <text x="60" y="80" textAnchor="middle" fontSize="8" fill="#9ca3af">
            ±2% confidence
          </text>
        </svg>
      </div>

      <div className="result-details">
        {/* Action badge */}
        <span className="badge" style={{ backgroundColor: color }}>
          {ACTION_ICONS[action]} {ACTION_LABELS[action] || action}
        </span>

        {/* Reason cards */}
        <h3>Why this score?</h3>
        <div className="reasons-list">
          {reasons.map((r, i) => (
            <div
              key={i}
              className="reason-card"
              style={{ borderLeftColor: color }}
            >
              <span className="reason-icon" aria-hidden="true">
                {getReasonIcon(r)}
              </span>
              <span>{r}</span>
            </div>
          ))}
        </div>

        {/* Feature inspector */}
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
