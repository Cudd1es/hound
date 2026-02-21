from fastapi.testclient import TestClient

from hound_core.api import app


def test_analyze_endpoint_allows_cors_preflight() -> None:
    client = TestClient(app)

    response = client.options(
        "/analyze",
        headers={
            "Origin": "chrome-extension://test-extension-id",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") in {
        "*",
        "chrome-extension://test-extension-id",
    }
