"""Simple integration test to verify API setup."""

from fastapi.testclient import TestClient


def test_health_endpoint(test_client: TestClient) -> None:
    """Test health check endpoint to verify API is working."""
    response = test_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
