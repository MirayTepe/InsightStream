"""Health endpoint tests."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Health check returns ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
