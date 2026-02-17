def test_feedback_accepted(client):
    resp = client.post("/feedback", json={
        "question": "Solve x + 1 = 3",
        "model_answer": "x = 2",
        "user_label_hallucinated": 0,
    })
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_feedback_with_notes(client):
    resp = client.post("/feedback", json={
        "question": "Solve x + 1 = 3",
        "model_answer": "x = 5",
        "user_label_hallucinated": 1,
        "notes": "Clearly wrong arithmetic",
    })
    assert resp.status_code == 200


def test_feedback_invalid_label(client):
    """user_label_hallucinated must be 0 or 1."""
    resp = client.post("/feedback", json={
        "question": "Solve x + 1 = 3",
        "model_answer": "x = 2",
        "user_label_hallucinated": 5,
    })
    assert resp.status_code == 422
