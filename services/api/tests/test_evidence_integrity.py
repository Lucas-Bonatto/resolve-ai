import pytest
from pydantic import ValidationError

from app.agents.providers import DemoAIProvider
from app.application.store import InMemoryRepository
from app.domain.enums import DiagnosisOutcome, EvidenceType, Severity
from app.domain.errors import EvidenceIntegrityError
from app.domain.models import Diagnosis, Evidence, Hypothesis, Incident


def _incident(repository: InMemoryRepository, incident_id: str) -> Incident:
    incident = Incident(
        id=incident_id,
        title="Evidence contract test",
        description="Fictional incident",
        severity=Severity.SEV2,
        affected_service="webhook-worker",
    )
    repository.add_incident(incident)
    return incident


def _evidence(repository: InMemoryRepository, incident: Incident, evidence_id: str) -> Evidence:
    evidence = Evidence(
        id=evidence_id,
        incident_id=incident.id,
        source_type=EvidenceType.LOG,
        source_reference="fixture",
        title="Fixture evidence",
        summary="A bounded fictional record.",
        relevance=0.8,
        correlation_id=incident.correlation_id,
    )
    repository.add_evidence(evidence)
    return evidence


def _diagnosis(evidence_ids: list[str]) -> Diagnosis:
    return Diagnosis(
        summary="Evidence-backed diagnosis",
        probable_root_cause="Fixture root cause",
        confidence=0.8,
        evidence_ids=evidence_ids,
        affected_services=["webhook-worker"],
        recommended_next_step="Verify the fixture.",
    )


def test_supported_diagnosis_requires_at_least_one_evidence_reference() -> None:
    with pytest.raises(ValidationError, match="must reference evidence"):
        _diagnosis([])


def test_diagnosis_rejects_unknown_structured_output_fields() -> None:
    payload = _diagnosis(["EVIDENCE-1"]).model_dump(mode="json")
    payload["model_reasoning"] = "Private reasoning must not enter the domain contract."
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Diagnosis.model_validate(payload)


def test_diagnosis_rejects_unknown_and_cross_incident_evidence() -> None:
    repository = InMemoryRepository()
    first = _incident(repository, "INC-EVIDENCE-1")
    second = _incident(repository, "INC-EVIDENCE-2")
    _evidence(repository, first, "EVIDENCE-1")
    _evidence(repository, second, "EVIDENCE-2")

    repository.set_diagnosis(first.id, _diagnosis(["EVIDENCE-1"]))
    with pytest.raises(EvidenceIntegrityError, match="EVIDENCE-MISSING"):
        repository.set_diagnosis(first.id, _diagnosis(["EVIDENCE-MISSING"]))
    with pytest.raises(EvidenceIntegrityError, match="EVIDENCE-2"):
        repository.set_diagnosis(first.id, _diagnosis(["EVIDENCE-2"]))


def test_hypothesis_rejects_cross_incident_evidence() -> None:
    repository = InMemoryRepository()
    first = _incident(repository, "INC-HYP-1")
    second = _incident(repository, "INC-HYP-2")
    _evidence(repository, first, "HYP-EVIDENCE-1")
    _evidence(repository, second, "HYP-EVIDENCE-2")

    with pytest.raises(EvidenceIntegrityError, match="HYP-EVIDENCE-2"):
        repository.add_hypothesis(
            Hypothesis(
                incident_id=first.id,
                title="Cross-incident claim",
                description="Must fail closed.",
                confidence=0.4,
                evidence_for=["HYP-EVIDENCE-2"],
                verification_strategy="Check incident ownership.",
            )
        )


@pytest.mark.asyncio
async def test_demo_provider_reports_insufficient_evidence_without_forcing_a_cause() -> None:
    diagnosis = await DemoAIProvider().diagnose("Fictional incident", [])
    assert diagnosis.outcome == DiagnosisOutcome.INSUFFICIENT_EVIDENCE
    assert diagnosis.probable_root_cause == DiagnosisOutcome.INSUFFICIENT_EVIDENCE
    assert diagnosis.confidence <= 0.25
