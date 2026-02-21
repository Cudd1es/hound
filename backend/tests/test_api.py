from fastapi.testclient import TestClient

from hound_core.api import app


def test_analyze_endpoint_returns_report_with_suggestions() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "profile": {"skills": ["react", "sql"]},
            "posting_text": "Requirements:\n- React\n- Kubernetes",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["overall_score"], int)
    assert len(payload["rows"]) == 2
    assert isinstance(payload["suggestions"], list)
