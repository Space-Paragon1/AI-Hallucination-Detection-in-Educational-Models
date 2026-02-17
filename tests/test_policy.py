from backend.app.policy.decision import policy_from_risk, reasons_from_signals


class TestPolicyFromRisk:
    def test_high_risk(self):
        label, action = policy_from_risk(0.85)
        assert label == "high_risk"
        assert action == "block_and_verify"

    def test_medium_risk(self):
        label, action = policy_from_risk(0.60)
        assert label == "medium_risk"
        assert action == "ask_clarifying_or_verify"

    def test_low_risk(self):
        label, action = policy_from_risk(0.30)
        assert label == "low_risk"
        assert action == "allow"

    def test_boundary_high(self):
        label, _ = policy_from_risk(0.80)
        assert label == "high_risk"

    def test_boundary_medium(self):
        label, _ = policy_from_risk(0.50)
        assert label == "medium_risk"


class TestReasonsFromSignals:
    def test_plug_in_failed(self):
        feats = {"eq_note": "plug_in_failed: 15 != 17", "has_steps": 1}
        reasons = reasons_from_signals(feats)
        assert any("equation" in r.lower() for r in reasons)

    def test_no_steps(self):
        feats = {"has_steps": 0}
        reasons = reasons_from_signals(feats)
        assert any("step" in r.lower() for r in reasons)

    def test_calc_mismatch(self):
        feats = {"calc_verified": 0, "calc_note": "derivative_mismatch", "has_steps": 1}
        reasons = reasons_from_signals(feats)
        assert any("symbolic" in r.lower() for r in reasons)

    def test_default_reason(self):
        feats = {"has_steps": 1}
        reasons = reasons_from_signals(feats)
        assert len(reasons) >= 1
