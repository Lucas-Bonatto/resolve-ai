from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from app.application.simulator import NovaPaySimulator
from app.application.store import InMemoryRepository
from app.config import settings
from app.domain.enums import ApprovalStatus, EvidenceType, Severity, ToolRiskLevel
from app.domain.errors import ApprovalInvalid, ToolExecutionFailed
from app.domain.models import Approval, Evidence, Incident, ToolCall, arguments_hash, utc_now
from app.tools.gateway import ToolGateway


class FailingSimulator(NovaPaySimulator):
    def execute(self, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("Synthetic simulator failure")


def setup_gateway(incident_id: str = "INC-TEST-1") -> tuple[InMemoryRepository, ToolGateway]:
    repository = InMemoryRepository()
    incident = Incident(
        id=incident_id,
        title="Test",
        description="Test",
        severity=Severity.SEV1,
        affected_service="webhook-worker",
    )
    repository.add_incident(incident)
    repository.add_evidence(
        Evidence(
            id="TEST-1",
            incident_id=incident_id,
            source_type=EvidenceType.TEST_RESULT,
            source_reference="permission-test",
            title="Permission test evidence",
            summary="Typed evidence used to bind a test approval.",
            relevance=1,
            correlation_id=incident.correlation_id,
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


def mark_approved(approval: Approval) -> None:
    approval.status = ApprovalStatus.APPROVED
    approval.approved_by = "security-reviewer"
    approval.approved_at = utc_now()


def test_critical_tool_cannot_execute_without_approval() -> None:
    _, gateway, arguments, _, _ = proposed()
    with pytest.raises(ApprovalInvalid):
        gateway.execute_safe("INC-TEST-1", "request_service_rollback", arguments)


def test_expired_approval_is_rejected() -> None:
    _, gateway, _, _, approval = proposed()
    mark_approved(approval)
    approval.expires_at = utc_now() - timedelta(seconds=1)
    with pytest.raises(ApprovalInvalid, match="expired"):
        gateway.execute_approved(approval)


def test_approval_arguments_cannot_be_changed() -> None:
    repository, gateway, _, call, approval = proposed()
    mark_approved(approval)
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


@pytest.mark.parametrize(
    "mutated_arguments",
    [
        {
            "service": "webhook-worker",
            "deployment_id": "dep_184",
            "target_deployment": "dep_183",
            "authorization": "approved",
        },
        {
            "service": "WEBHOOK-WORKER",
            "deployment_id": "dep_184",
            "target_deployment": "dep_183",
        },
        {
            "service": "webhook-worker",
            "deployment_id": "dep_184",
            "target_deployment": 183,
        },
    ],
)
def test_hidden_argument_mutations_fail_closed(
    mutated_arguments: dict[str, object],
) -> None:
    repository, gateway, _, call, approval = proposed()
    mark_approved(approval)
    repository.data(call.incident_id).tool_calls[0] = call.model_copy(
        update={"arguments": mutated_arguments}
    )

    with pytest.raises(ApprovalInvalid, match="changed"):
        gateway.execute_approved(approval)

    assert gateway.simulator.deployment_active == "dep_184"


def test_argument_hash_is_stable_across_object_key_order() -> None:
    first = {
        "service": "webhook-worker",
        "deployment_id": "dep_184",
        "target_deployment": "dep_183",
    }
    reordered = {
        "target_deployment": "dep_183",
        "deployment_id": "dep_184",
        "service": "webhook-worker",
    }

    assert arguments_hash(first) == arguments_hash(reordered)


def test_approval_is_consumed_before_execution_and_cannot_be_replayed() -> None:
    _, gateway, _, _, approval = proposed()
    mark_approved(approval)
    gateway.execute_approved(approval)
    assert approval.status == ApprovalStatus.CONSUMED
    with pytest.raises(ApprovalInvalid, match="CONSUMED"):
        gateway.execute_approved(approval)


def test_concurrent_workers_cannot_consume_one_approval_twice() -> None:
    _, gateway, _, _, approval = proposed()
    mark_approved(approval)

    def attempt() -> bool:
        try:
            gateway.execute_approved(approval)
        except ApprovalInvalid:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt(), range(2)))

    assert results.count(True) == 1
    assert results.count(False) == 1
    assert approval.status == ApprovalStatus.CONSUMED


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
    mark_approved(approval)
    call.incident_id = "INC-TEST-2"
    with pytest.raises(ApprovalInvalid, match="another incident"):
        gateway.execute_approved(approval)


def test_rejected_approval_is_blocked() -> None:
    _, gateway, _, _, approval = proposed()
    approval.status = ApprovalStatus.REJECTED
    with pytest.raises(ApprovalInvalid, match="REJECTED"):
        gateway.execute_approved(approval)


def test_approval_cannot_authorize_a_different_tool() -> None:
    repository, gateway, _, call, approval = proposed()
    mark_approved(approval)
    repository.data(call.incident_id).tool_calls[0] = call.model_copy(
        update={"tool_name": "create_incident_note"}
    )
    with pytest.raises(ApprovalInvalid, match="another tool"):
        gateway.execute_approved(approval)


def test_approval_cannot_authorize_a_different_requested_action() -> None:
    _, gateway, _, _, approval = proposed()
    mark_approved(approval)
    approval.requested_action = "Deploy a different release"
    with pytest.raises(ApprovalInvalid, match="requested action"):
        gateway.execute_approved(approval)


def test_forged_approval_object_cannot_redirect_an_approved_action() -> None:
    repository, gateway, _, _, approval = proposed()
    mark_approved(approval)
    forged_arguments = {
        "service": "webhook-worker",
        "deployment_id": "dep_184",
        "target_deployment": "dep_999",
    }
    forged_call = ToolCall(
        incident_id=approval.incident_id,
        tool_name="request_service_rollback",
        arguments=forged_arguments,
        risk_level=ToolRiskLevel.CRITICAL_WRITE,
        correlation_id=repository.data(approval.incident_id).incident.correlation_id,
    )
    repository.add_tool_call(forged_call)
    forged_approval = approval.model_copy(
        deep=True,
        update={
            "tool_call_id": forged_call.id,
            "requested_action": "Rollback webhook-worker to dep_999",
            "arguments_hash": arguments_hash(forged_arguments),
        },
    )

    with pytest.raises(ApprovalInvalid, match="authoritative"):
        gateway.execute_approved(forged_approval)

    assert gateway.simulator.deployment_active == "dep_184"
    assert approval.status == ApprovalStatus.APPROVED


def test_missing_approved_tool_call_is_blocked() -> None:
    repository, gateway, _, _, approval = proposed()
    mark_approved(approval)
    repository.data(approval.incident_id).tool_calls.clear()
    with pytest.raises(ApprovalInvalid, match="no longer exists"):
        gateway.execute_approved(approval)


def test_approved_status_without_human_decision_metadata_is_blocked() -> None:
    _, gateway, _, _, approval = proposed()
    approval.status = ApprovalStatus.APPROVED
    with pytest.raises(ApprovalInvalid, match="human decision"):
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


def test_tool_schemas_reject_unknown_fields_and_type_coercion() -> None:
    _, gateway = setup_gateway()
    with pytest.raises(ToolExecutionFailed, match="strict schema"):
        gateway.execute_safe(
            "INC-TEST-1",
            "get_service_health",
            {"service": "webhook-worker", "approved": True},
        )
    with pytest.raises(ToolExecutionFailed, match="strict schema"):
        gateway.execute_safe(
            "INC-TEST-1",
            "search_transactions",
            {"limit": "50"},
        )


def test_critical_tool_rejects_unallowlisted_deployment() -> None:
    _, gateway = setup_gateway()
    with pytest.raises(ToolExecutionFailed, match="Deployment.*allowlist"):
        gateway.propose_critical(
            "INC-TEST-1",
            "request_service_rollback",
            {
                "service": "webhook-worker",
                "deployment_id": "dep_184",
                "target_deployment": "dep_999",
            },
            reason="Must fail closed",
            evidence_ids=["TEST-1"],
            impact="None",
        )


def test_tool_call_budget_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    _, gateway = setup_gateway()
    monkeypatch.setattr(settings, "max_tool_calls_per_run", 1)
    gateway.execute_safe("INC-TEST-1", "get_service_health", {"service": "webhook-worker"})
    with pytest.raises(ToolExecutionFailed, match="Maximum tool calls"):
        gateway.execute_safe("INC-TEST-1", "get_service_health", {"service": "webhook-worker"})


def test_tool_failure_is_bounded_audited_and_typed() -> None:
    repository = InMemoryRepository()
    incident = Incident(
        id="INC-TOOL-FAILURE",
        title="Failure contract",
        description="Fictional tool failure",
        severity=Severity.SEV2,
        affected_service="webhook-worker",
    )
    repository.add_incident(incident)
    gateway = ToolGateway(repository, FailingSimulator())

    with pytest.raises(ToolExecutionFailed, match="failed safely"):
        gateway.execute_safe(
            incident.id,
            "get_service_health",
            {"service": "webhook-worker"},
        )

    call = repository.data(incident.id).tool_calls[0]
    assert call.status == "BLOCKED"
    assert call.output_summary == "Tool failed safely (RuntimeError)"
    assert repository.audit[-1].action == "tool.failed"
    assert repository.audit[-1].metadata == {"error_type": "RuntimeError"}


def test_dangerous_general_purpose_tools_are_not_exposed() -> None:
    from app.tools.gateway import TOOL_CATALOG

    forbidden_fragments = {"shell", "sql", "filesystem", "github", "delete_audit"}
    assert all(
        not any(fragment in name.lower() for fragment in forbidden_fragments)
        for name in TOOL_CATALOG
    )
