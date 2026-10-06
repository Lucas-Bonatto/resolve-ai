from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agents.providers import DemoAIProvider
from app.application.orchestrator import FLAGSHIP_ID, IncidentCoordinator
from app.application.rate_limit import SlidingWindowRateLimiter
from app.application.showcase import prepare_public_showcase
from app.application.simulator import NovaPaySimulator
from app.application.store import InMemoryRepository
from app.config import Settings, settings
from app.domain.enums import IncidentState
from app.main import app


def public_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "deployment_profile": "public_showcase",
        "cors_allowed_origins": "https://demo.resolveai.example",
        "ai_provider": "demo",
        "enable_real_ai": False,
        "persistence_backend": "memory",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_public_showcase_configuration_is_fail_closed() -> None:
    with pytest.raises(ValidationError, match="AI_PROVIDER=demo"):
        public_settings(ai_provider="openai", enable_real_ai=True)
    with pytest.raises(ValidationError, match="PERSISTENCE_BACKEND=memory"):
        public_settings(persistence_backend="postgres")
    with pytest.raises(ValidationError, match="non-local CORS"):
        public_settings(cors_allowed_origins="http://localhost:3000")
    with pytest.raises(ValidationError, match="HTTPS CORS"):
        public_settings(cors_allowed_origins="http://demo.resolveai.example")
    with pytest.raises(ValidationError, match="explicit origin allowlist"):
        Settings(_env_file=None, cors_allowed_origins="*")
    with pytest.raises(ValidationError, match="explicit origin allowlist"):
        public_settings(cors_allowed_origins="https://*.resolveai.example")


def test_cors_origins_are_normalized_and_reject_credentials() -> None:
    configured = public_settings(
        cors_allowed_origins="https://demo.resolveai.example/, https://portfolio.example"
    )
    assert configured.allowed_cors_origins == [
        "https://demo.resolveai.example",
        "https://portfolio.example",
    ]

    with pytest.raises(ValidationError, match="Invalid CORS origin"):
        public_settings(cors_allowed_origins="https://user:secret@demo.resolveai.example")


@pytest.mark.asyncio
async def test_public_showcase_seed_is_deterministic_and_pauses_before_execution(
    tmp_path: Path,
) -> None:
    repo = InMemoryRepository()
    environment = NovaPaySimulator()
    incident_coordinator = IncidentCoordinator(repo, environment, DemoAIProvider())
    result_path = tmp_path / "latest.json"
    result_path.write_text(
        """{
          "id": "eval_public_test",
          "provider": "demo",
          "model": "deterministic-demo-v1",
          "sample_data": false,
          "suite_version": "resolveai-benchmark-v1",
          "run_kind": "deterministic-contract",
          "code_revision": "test-revision",
          "created_at": "2026-10-06T00:00:00Z",
          "results": [],
          "metrics": {"case_count": 0}
        }""",
        encoding="utf-8",
    )

    await prepare_public_showcase(repo, environment, incident_coordinator, result_path)

    data = repo.data(FLAGSHIP_ID)
    assert data.incident.state == IncidentState.AWAITING_APPROVAL
    assert data.approval is not None
    assert data.approval.status.value == "PENDING"
    assert data.validation is None
    assert repo.evaluation_runs[0].code_revision == "test-revision"
    seed_record = next(record for record in repo.audit if record.actor_id == "public-showcase-seed")
    assert seed_record.actor_type == "SYSTEM"


@pytest.mark.asyncio
async def test_public_showcase_rate_limiter_is_bounded() -> None:
    limiter = SlidingWindowRateLimiter(request_limit=2, window_seconds=10, max_clients=2)

    assert await limiter.retry_after("visitor-a", now=0) is None
    assert await limiter.retry_after("visitor-a", now=1) is None
    assert await limiter.retry_after("visitor-a", now=2) == 8
    assert await limiter.retry_after("visitor-b", now=2) is None
    assert await limiter.retry_after("visitor-c", now=2) is None
    assert limiter.tracked_clients == 2
    assert await limiter.retry_after("visitor-a", now=11) is None


def test_public_showcase_blocks_every_mutation_at_the_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "deployment_profile", "public_showcase")
    try:
        with TestClient(app) as client:
            runtime = client.get("/api/runtime")
            assert runtime.status_code == 200
            assert runtime.json() == {
                "deployment_profile": "public_showcase",
                "interactive": False,
                "mutations_allowed": False,
                "real_ai_enabled": False,
                "fictional_data": True,
            }

            before = client.get(f"/api/incidents/{FLAGSHIP_ID}").json()
            approval_id = before["approval"]["id"]
            attempts = [
                client.post(
                    "/api/chaos/scenarios/payment-webhook-regression/inject"
                ),
                client.post(
                    f"/api/approvals/{approval_id}/approve",
                    json={"actor": "public-visitor"},
                ),
                client.post(
                    f"/api/approvals/{approval_id}/approve",
                    json={"approved": True},
                ),
                client.post(
                    f"/api/approvals/{approval_id}/reject",
                    json={"actor": "public-visitor"},
                ),
                client.post("/api/evals/run"),
                client.post("/api/demo/reset"),
            ]

            assert all(response.status_code == 403 for response in attempts)
            assert all(response.json()["error"] == "ReadOnlyRuntimeError" for response in attempts)
            assert client.get(f"/api/incidents/{FLAGSHIP_ID}").json() == before
            assert len(client.get("/api/evals/runs").json()) == 1
    finally:
        monkeypatch.setattr(settings, "deployment_profile", "local")
        with TestClient(app) as client:
            client.post("/api/demo/reset")


def test_api_responses_include_baseline_security_headers() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=()"
    )
