import pytest

from app.agents.providers import DemoAIProvider
from app.application.orchestrator import FLAGSHIP_ID, IncidentCoordinator
from app.application.simulator import NovaPaySimulator
from app.application.store import InMemoryRepository
from app.config import settings
from app.domain.enums import ApprovalStatus, IncidentState
from app.domain.models import Diagnosis, Evidence


class InvalidEvidenceProvider(DemoAIProvider):
    async def diagnose(self, incident_description: str, evidence: list[Evidence]) -> Diagnosis:
        diagnosis = await super().diagnose(incident_description, evidence)
        return diagnosis.model_copy(update={"evidence_ids": ["EVIDENCE-THAT-DOES-NOT-EXIST"]})


@pytest.mark.asyncio
async def test_flagship_flow_requires_approval_then_resolves() -> None:
    repository = InMemoryRepository()
    coordinator = IncidentCoordinator(repository, NovaPaySimulator(), DemoAIProvider())
    coordinator.delay = 0
    incident = await coordinator.inject_flagship()
    await coordinator._tasks[incident.id]

    waiting = repository.snapshot(FLAGSHIP_ID)
    assert waiting.incident.state == IncidentState.AWAITING_APPROVAL
    assert waiting.approval is not None
    assert waiting.approval.status == ApprovalStatus.PENDING
    assert waiting.diagnosis is not None
    assert set(waiting.diagnosis.evidence_ids).issubset({item.id for item in waiting.evidence})
    assert waiting.tool_calls[-1].status == "NOT_EXECUTED"

    await coordinator.approve(FLAGSHIP_ID, waiting.approval.id, "security-reviewer")
    resolved = repository.snapshot(FLAGSHIP_ID)
    assert resolved.incident.state == IncidentState.RESOLVED
    assert resolved.approval is not None
    assert resolved.approval.status == ApprovalStatus.CONSUMED
    assert "TEST-POST-ROLLBACK" in {item.id for item in resolved.evidence}


@pytest.mark.asyncio
async def test_rejected_approval_executes_no_critical_tool() -> None:
    repository = InMemoryRepository()
    coordinator = IncidentCoordinator(repository, NovaPaySimulator(), DemoAIProvider())
    coordinator.delay = 0
    incident = await coordinator.inject_flagship()
    await coordinator._tasks[incident.id]
    approval = repository.data(FLAGSHIP_ID).approval
    assert approval is not None

    await coordinator.reject(FLAGSHIP_ID, approval.id, "security-reviewer")
    snapshot = repository.snapshot(FLAGSHIP_ID)
    assert snapshot.incident.state == IncidentState.ESCALATED
    critical = [call for call in snapshot.tool_calls if call.risk_level == "critical_write"]
    assert all(call.status == "NOT_EXECUTED" for call in critical)


@pytest.mark.asyncio
async def test_investigation_timeout_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = InMemoryRepository()
    coordinator = IncidentCoordinator(repository, NovaPaySimulator(), DemoAIProvider())
    coordinator.delay = 0.05
    monkeypatch.setattr(settings, "max_investigation_seconds", 0.001)

    incident = await coordinator.inject_flagship()
    await coordinator._tasks[incident.id]

    snapshot = repository.snapshot(FLAGSHIP_ID)
    assert snapshot.incident.state == IncidentState.FAILED
    assert snapshot.run is not None
    assert snapshot.run.error == "InvestigationTimeout"


@pytest.mark.asyncio
async def test_unknown_agent_evidence_reference_fails_the_run() -> None:
    repository = InMemoryRepository()
    coordinator = IncidentCoordinator(repository, NovaPaySimulator(), InvalidEvidenceProvider())
    coordinator.delay = 0

    incident = await coordinator.inject_flagship()
    await coordinator._tasks[incident.id]

    snapshot = repository.snapshot(FLAGSHIP_ID)
    assert snapshot.incident.state == IncidentState.FAILED
    assert snapshot.diagnosis is None
    assert snapshot.run is not None
    assert snapshot.run.error == "EvidenceIntegrityError"


@pytest.mark.asyncio
async def test_validation_failure_never_marks_incident_resolved() -> None:
    repository = InMemoryRepository()
    coordinator = IncidentCoordinator(
        repository,
        NovaPaySimulator(validation_should_fail=True),
        DemoAIProvider(),
    )
    coordinator.delay = 0

    incident = await coordinator.inject_flagship()
    await coordinator._tasks[incident.id]
    approval = repository.data(FLAGSHIP_ID).approval
    assert approval is not None

    await coordinator.approve(FLAGSHIP_ID, approval.id, "security-reviewer")
    snapshot = repository.snapshot(FLAGSHIP_ID)
    assert snapshot.incident.state == IncidentState.ESCALATED
    assert snapshot.validation is not None
    assert snapshot.validation.passed is False
    assert snapshot.report is not None
    assert snapshot.report.final_status == IncidentState.ESCALATED
