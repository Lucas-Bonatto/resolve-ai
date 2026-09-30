from datetime import timedelta

import pytest

from app.application.simulator import NovaPaySimulator
from app.application.store import InMemoryRepository
from app.config import settings
from app.domain.enums import ApprovalStatus, Severity
from app.domain.errors import ApprovalInvalid, ToolExecutionFailed
from app.domain.models import Incident, utc_now
from app.tools.gateway import ToolGateway


def setup_gateway(incident_id: str = "INC-TEST-1") -> tuple[InMemoryRepository, ToolGateway]:
    repository = InMemoryRepository()
    repository.add_incident(
        Incident(
            id=incident_id,
            title="Test",
            description="Test",
            severity=Severity.SEV1,
            affected_service="webhook-worker",
        )
    )
    return repository, ToolGateway(repository, NovaPaySimulator())


def proposed(incident_id: str = "INC-TEST-1"):
    repository, gateway = setup_gateway(incident_id)
    arguments = {
        "service": "webhook-worker",
        "deployment_id": "dep_184",
        "target_deployment": "dep_183",
    }
    call, approval = gateway.propose_critical(
        incident_id,
        "request_service_rollback",
        arguments,
        reason="Test",
        evidence_ids=["TEST-1"],
        impact="Test impact",
    )
    return repository, gateway, arguments, call, approval


def test_critical_tool_cannot_execute_without_approval() -> None:
    _, gateway, arguments, _, _ = proposed()
    with pytest.raises(ApprovalInvalid):
        gateway.execute_safe("INC-TEST-1", "request_service_rollback", arguments)


def test_expired_approval_is_rejected() -> None:
    _, gateway, _, _, approval = proposed()
    approval.status = ApprovalStatus.APPROVED
    approval.expires_at = utc_now() - timedelta(seconds=1)
    with pytest.raises(ApprovalInvalid, match="expired"):
        gateway.execute_approved(approval)


def test_approval_arguments_cannot_be_changed() -> None:
    repository, gateway, _, call, approval = proposed()
    approval.status = ApprovalStatus.APPROVED
    repository.data("INC-TEST-1").tool_calls[0] = call.model_copy(
        update={
            "arguments": {
                "service": "webhook-worker",
                "deployment_id": "dep_184",
                "target_deployment": "dep_999",
            }
        }
    )
    with pytest.raises(ApprovalInvalid, match="changed"):
        gateway.execute_approved(approval)


def test_approval_is_consumed_before_execution_and_cannot_be_replayed() -> None:
    _, gateway, _, _, approval = proposed()
    approval.status = ApprovalStatus.APPROVED
    gateway.execute_approved(approval)
    assert approval.status == ApprovalStatus.CONSUMED
    with pytest.raises(ApprovalInvalid, match="CONSUMED"):
        gateway.execute_approved(approval)


def test_approval_cannot_cross_incidents() -> None:
    repository, gateway, _, call, approval = proposed()
    repository.add_incident(
        Incident(
            id="INC-TEST-2",
            title="Other",
            description="Other",
            severity=Severity.SEV2,
            affected_service="auth-service",
        )
    )
    approval.status = ApprovalStatus.APPROVED
    call.incident_id = "INC-TEST-2"
    with pytest.raises(ApprovalInvalid, match="another incident"):
        gateway.execute_approved(approval)


def test_malicious_tool_parameters_are_rejected() -> None:
    repository, gateway = setup_gateway()
    with pytest.raises(ToolExecutionFailed, match="dangerous"):
        gateway.execute_safe(
            "INC-TEST-1",
            "query_application_logs",
            {"service": "webhook-worker", "query": "error; DROP TABLE incidents"},
        )
    assert repository.audit[-1].result == "BLOCKED"
    assert repository.audit[-1].metadata["reason"] == "dangerous_arguments"


def test_unauthorized_service_is_rejected() -> None:
    _, gateway = setup_gateway()
    with pytest.raises(ToolExecutionFailed, match="allowlist"):
        gateway.execute_safe(
            "INC-TEST-1", "get_service_health", {"service": "arbitrary-production-host"}
        )


def test_tool_call_budget_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    _, gateway = setup_gateway()
    monkeypatch.setattr(settings, "max_tool_calls_per_run", 1)
    gateway.execute_safe("INC-TEST-1", "get_service_health", {"service": "webhook-worker"})
    with pytest.raises(ToolExecutionFailed, match="Maximum tool calls"):
        gateway.execute_safe("INC-TEST-1", "get_service_health", {"service": "webhook-worker"})


def test_dangerous_general_purpose_tools_are_not_exposed() -> None:
    from app.tools.gateway import TOOL_CATALOG

    forbidden_fragments = {"shell", "sql", "filesystem", "github", "delete_audit"}
    assert all(
        not any(fragment in name.lower() for fragment in forbidden_fragments)
        for name in TOOL_CATALOG
    )
