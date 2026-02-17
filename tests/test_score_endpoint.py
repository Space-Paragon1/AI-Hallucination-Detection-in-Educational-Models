def test_score_correct_algebra(client):
    """Correct answer to 2x + 5 = 17 is x = 6."""
    resp = client.post("/score", json={
        "question": "Solve for x: 2x + 5 = 17",
        "model_answer": "2x + 5 = 17 -> 2x = 12 -> x = 6",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert 0.0 <= data["risk"] <= 1.0
    assert data["label"] in ("low_risk", "medium_risk", "high_risk")
    assert data["action"] in ("allow", "ask_clarifying_or_verify", "block_and_verify")
    assert isinstance(data["reasons"], list)
    assert isinstance(data["features"], dict)


def test_score_wrong_algebra(client):
    """x = 5 is wrong for 2x + 5 = 17 (correct is 6). Should get higher risk."""
    resp = client.post("/score", json={
        "question": "Solve for x: 2x + 5 = 17",
        "model_answer": "2x + 5 = 17 -> 2x = 10 -> x = 5",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk"] >= 0.5, "Wrong answer should have elevated risk"


def test_score_missing_fields(client):
    """Missing required fields should return 422."""
    resp = client.post("/score", json={"question": "Solve x + 1 = 3"})
    assert resp.status_code == 422


def test_score_calculus_derivative(client):
    """Test scoring a calculus derivative question."""
    resp = client.post("/score", json={
        "question": "Find the derivative of x^3",
        "model_answer": "The derivative of x^3 is 3x^2",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["features"].get("is_calc_prompt") == 1


def test_score_response_schema(client):
    """All expected fields are present in the response."""
    resp = client.post("/score", json={
        "question": "Solve for x: x + 3 = 7",
        "model_answer": "x + 3 = 7 -> x = 4",
    })
    data = resp.json()
    for key in ("risk", "label", "action", "reasons", "features"):
        assert key in data, f"Missing key: {key}"
