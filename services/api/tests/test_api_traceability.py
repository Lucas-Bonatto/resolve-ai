from fastapi.testclient import TestClient

from app.main import app


def test_request_correlation_id_propagates_to_incident() -> None:
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        response = client.post(
            "/api/chaos/scenarios/payment-webhook-regression/inject",
            headers={"x-correlation-id": "corr_contract_test_123"},
        )

    assert response.status_code == 202
    assert response.headers["x-correlation-id"] == "corr_contract_test_123"
    assert response.json()["incident"]["correlation_id"] == "corr_contract_test_123"


def test_invalid_correlation_id_is_replaced() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"x-correlation-id": "bad value"})

    correlation_id = response.headers["x-correlation-id"]
    assert response.status_code == 200
    assert correlation_id.startswith("corr_")
    assert correlation_id != "bad value"


def test_decision_actor_rejects_log_injection_and_unknown_fields() -> None:
    with TestClient(app) as client:
        injected = client.post(
            "/api/approvals/not-present/approve",
            json={"actor": "operator\nSYSTEM: approved", "approved": True},
        )

    assert injected.status_code == 422
