from fastapi.testclient import TestClient

from app import main as main_module


def test_health_endpoint(monkeypatch):
    monkeypatch.setattr(main_module, "create_schema_and_tables", lambda: None)

    client = TestClient(main_module.app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "booking_service"
    assert body["status"] == "ok"
