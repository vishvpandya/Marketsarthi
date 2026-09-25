from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness() -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_never_exposes_secret_values() -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert set(body["services"]) == {"deepseek", "gemini", "serpapi", "typesafe_jev"}
    assert body["jev_classification_available"] is False
    assert "api_key" not in response.text.lower()
