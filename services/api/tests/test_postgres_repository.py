import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.application.simulator import NovaPaySimulator
from app.domain.enums import ApprovalStatus, EvidenceType, Severity
from app.domain.errors import ApprovalInvalid
from app.domain.models import Approval, Diagnosis, Evidence, Hypothesis, Incident
from app.infrastructure.database import Base
from app.infrastructure.postgres_repository import PostgresRepository
from app.tools.gateway import ToolGateway


def test_repository_rehydrates_incident_evidence_hypotheses_and_diagnosis(
    tmp_path: Path,
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'repository-contract.db'}")
    Base.metadata.create_all(engine)
    repository = PostgresRepository(engine, load_existing=False)
    incident = Incident(
        id="INC-PERSIST-1",
        title="Persistence contract",
        description="Fictional persistence verification",
        severity=Severity.SEV2,
        affected_service="webhook-worker",
    )
    repository.add_incident(incident)
    repository.add_evidence(
        Evidence(
            id="PERSIST-EVIDENCE-1",
            incident_id=incident.id,
            source_type=EvidenceType.LOG,
            source_reference="fixture",
            title="Persisted evidence",
            summary="A fictional structured record.",
            relevance=0.9,
            correlation_id=incident.correlation_id,
        )
    )
    repository.add_hypothesis(
        Hypothesis(
            incident_id=incident.id,
            title="Persisted hypothesis",
            description="A typed hypothesis.",
            confidence=0.7,
            evidence_for=["PERSIST-EVIDENCE-1"],
            verification_strategy="Reload the repository.",
        )
    )
    repository.set_diagnosis(
        incident.id,
        Diagnosis(
            summary="Persisted diagnosis",
            probable_root_cause="Fixture root cause",
            confidence=0.8,
            evidence_ids=["PERSIST-EVIDENCE-1"],
            affected_services=["webhook-worker"],
            recommended_next_step="Verify persistence.",
        ),
    )

    reloaded = PostgresRepository(engine)
    snapshot = reloaded.snapshot(incident.id)
    assert snapshot.incident.correlation_id == incident.correlation_id
    assert [item.id for item in snapshot.evidence] == ["PERSIST-EVIDENCE-1"]
    assert len(snapshot.hypotheses) == 1
    assert snapshot.diagnosis is not None
    assert snapshot.diagnosis.evidence_ids == ["PERSIST-EVIDENCE-1"]


def test_stale_repository_cannot_reopen_a_consumed_approval(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'approval-cas-contract.db'}")
    Base.metadata.create_all(engine)
    first_repository = PostgresRepository(engine, load_existing=False)
    incident = Incident(
        id="INC-STALE-APPROVAL",
        title="Stale approval contract",
        description="Fictional compare-and-set verification",
        severity=Severity.SEV2,
        affected_service="webhook-worker",
    )
    first_repository.add_incident(incident)
    first_repository.add_evidence(
        Evidence(
            id="STALE-EVIDENCE-1",
            incident_id=incident.id,
            source_type=EvidenceType.TEST_RESULT,
            source_reference="approval-cas-contract",
            title="Stale approval evidence",
            summary="A bounded fictional test result.",
            relevance=1,
            correlation_id=incident.correlation_id,
        )
    )
    first_gateway = ToolGateway(first_repository, NovaPaySimulator())
    _, approval = first_gateway.propose_critical(
        incident.id,
        "request_service_rollback",
        {
            "service": "webhook-worker",
            "deployment_id": "dep_184",
            "target_deployment": "dep_183",
        },
        reason="Verify stale decision protection",
        evidence_ids=["STALE-EVIDENCE-1"],
        impact="One simulated rollback",
    )
    stale_repository = PostgresRepository(engine)
    stale_approval = stale_repository.data(incident.id).approval
    assert stale_approval is not None

    approval.status = ApprovalStatus.APPROVED
    approval.approved_by = "first-reviewer"
    approval.approved_at = approval.requested_at
    first_repository.save_approval(approval)
    first_gateway.execute_approved(approval)

    stale_approval.status = ApprovalStatus.APPROVED
    stale_approval.approved_by = "stale-reviewer"
    stale_approval.approved_at = stale_approval.requested_at
    with pytest.raises(ApprovalInvalid, match="stale"):
        stale_repository.save_approval(stale_approval)

    reloaded = PostgresRepository(engine)
    persisted = reloaded.data(incident.id).approval
    assert persisted is not None
    assert persisted.status == ApprovalStatus.CONSUMED
    assert persisted.approved_by == "first-reviewer"


@pytest.mark.postgres
def test_postgres_consumes_one_approval_across_repository_instances() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for the real PostgreSQL concurrency test")

    engine = create_engine(database_url, pool_pre_ping=True)
    first_repository = PostgresRepository(engine)
    incident = Incident(
        id="INC-POSTGRES-CONCURRENCY",
        title="PostgreSQL concurrency contract",
        description="Fictional exact-action approval test",
        severity=Severity.SEV2,
        affected_service="webhook-worker",
    )
    first_repository.remove_incident(incident.id)
    first_repository.add_incident(incident)
    first_repository.add_evidence(
        Evidence(
            id="POSTGRES-EVIDENCE-1",
            incident_id=incident.id,
            source_type=EvidenceType.TEST_RESULT,
            source_reference="postgres-contract",
            title="Concurrency evidence",
            summary="A bounded fictional test result.",
            relevance=1,
            correlation_id=incident.correlation_id,
        )
    )
    first_gateway = ToolGateway(first_repository, NovaPaySimulator())
    _, approval = first_gateway.propose_critical(
        incident.id,
        "request_service_rollback",
        {
            "service": "webhook-worker",
            "deployment_id": "dep_184",
            "target_deployment": "dep_183",
        },
        reason="Verify atomic consumption",
        evidence_ids=["POSTGRES-EVIDENCE-1"],
        impact="One simulated rollback",
    )
    approval.status = ApprovalStatus.APPROVED
    approval.approved_by = "postgres-contract-test"
    approval.approved_at = approval.requested_at
    first_repository.save_approval(approval)

    second_repository = PostgresRepository(engine)
    second_approval = second_repository.data(incident.id).approval
    assert second_approval is not None
    gateways = [
        (first_gateway, approval),
        (ToolGateway(second_repository, NovaPaySimulator()), second_approval),
    ]

    def attempt(item: tuple[ToolGateway, Approval]) -> bool:
        gateway, candidate = item
        try:
            gateway.execute_approved(candidate)
        except ApprovalInvalid:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, gateways))

    assert results.count(True) == 1
    assert results.count(False) == 1
