from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field

from app.domain.enums import ApprovalStatus, DiagnosisOutcome
from app.domain.errors import ApprovalInvalid, EvidenceIntegrityError, IncidentNotFound
from app.domain.models import (
    AgentRun,
    Approval,
    AuditRecord,
    Diagnosis,
    EvaluationRun,
    Evidence,
    Hypothesis,
    Incident,
    IncidentEvent,
    IncidentReport,
    IncidentSnapshot,
    RemediationPlan,
    ToolCall,
    ValidationResult,
    utc_now,
)


@dataclass
class IncidentData:
    incident: Incident
    events: list[IncidentEvent] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    diagnosis: Diagnosis | None = None
    remediation_plan: RemediationPlan | None = None
    approval: Approval | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    run: AgentRun | None = None
    validation: ValidationResult | None = None
    report: IncidentReport | None = None


class InMemoryRepository:
    """Replayable demo repository; replaceable through the repository boundary."""

    def __init__(self) -> None:
        self.incidents: dict[str, IncidentData] = {}
        self.audit: list[AuditRecord] = []
        self.evaluation_runs: list[EvaluationRun] = []
        self._subscribers: dict[str, set[asyncio.Queue[IncidentEvent]]] = {}
        self._lock = asyncio.Lock()
        self._approval_lock = threading.Lock()

    async def reset(self) -> None:
        async with self._lock:
            self.incidents.clear()
            self.audit.clear()
            self.evaluation_runs.clear()
            self._subscribers.clear()

    def add_incident(self, incident: Incident) -> None:
        self.incidents[incident.id] = IncidentData(incident=incident)

    def remove_incident(self, incident_id: str) -> None:
        self.incidents.pop(incident_id, None)

    def save_incident(self, incident: Incident) -> None:
        self.data(incident.id).incident = incident

    def data(self, incident_id: str) -> IncidentData:
        try:
            return self.incidents[incident_id]
        except KeyError as exc:
            raise IncidentNotFound(incident_id) from exc

    def snapshot(self, incident_id: str) -> IncidentSnapshot:
        data = self.data(incident_id)
        return IncidentSnapshot(
            incident=data.incident,
            events=data.events,
            evidence=data.evidence,
            hypotheses=data.hypotheses,
            diagnosis=data.diagnosis,
            remediation_plan=data.remediation_plan,
            approval=data.approval,
            tool_calls=data.tool_calls,
            run=data.run,
            validation=data.validation,
            report=data.report,
        ).model_copy(deep=True)

    def _assert_evidence_owned(self, incident_id: str, evidence_ids: list[str]) -> None:
        if not evidence_ids:
            return
        owned = {item.id for item in self.data(incident_id).evidence}
        unknown = sorted(set(evidence_ids) - owned)
        if unknown:
            raise EvidenceIntegrityError(
                f"Evidence does not belong to incident {incident_id}: {', '.join(unknown)}"
            )

    def add_evidence(self, evidence: Evidence) -> None:
        data = self.data(evidence.incident_id)
        if evidence.id not in {item.id for item in data.evidence}:
            data.evidence.append(evidence.model_copy(deep=True))

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self._assert_evidence_owned(
            hypothesis.incident_id, hypothesis.evidence_for + hypothesis.evidence_against
        )
        self.data(hypothesis.incident_id).hypotheses.append(hypothesis)

    def save_hypothesis(self, hypothesis: Hypothesis) -> None:
        self._assert_evidence_owned(
            hypothesis.incident_id, hypothesis.evidence_for + hypothesis.evidence_against
        )
        hypothesis.updated_at = utc_now()
        hypotheses = self.data(hypothesis.incident_id).hypotheses
        for index, current in enumerate(hypotheses):
            if current.id == hypothesis.id:
                hypotheses[index] = hypothesis
                return
        raise EvidenceIntegrityError("Hypothesis does not belong to the incident")

    def set_diagnosis(self, incident_id: str, diagnosis: Diagnosis) -> None:
        if diagnosis.outcome == DiagnosisOutcome.SUPPORTED_ROOT_CAUSE:
            self._assert_evidence_owned(incident_id, diagnosis.evidence_ids)
        self.data(incident_id).diagnosis = diagnosis

    def set_remediation_plan(self, plan: RemediationPlan) -> None:
        self.data(plan.incident_id).remediation_plan = plan

    def add_tool_call(self, call: ToolCall) -> None:
        self.data(call.incident_id).tool_calls.append(call)

    def save_tool_call(self, call: ToolCall) -> None:
        calls = self.data(call.incident_id).tool_calls
        for index, current in enumerate(calls):
            if current.id == call.id:
                calls[index] = call
                return
        raise IncidentNotFound(f"Tool call {call.id}")

    def set_approval(self, approval: Approval) -> None:
        self._assert_evidence_owned(approval.incident_id, approval.evidence_ids)
        self.data(approval.incident_id).approval = approval

    def save_approval(self, approval: Approval) -> None:
        current = self.data(approval.incident_id).approval
        if current is None or current.id != approval.id:
            raise ApprovalInvalid("Approval does not belong to this incident")
        self.data(approval.incident_id).approval = approval

    def consume_approval(self, approval: Approval) -> None:
        with self._approval_lock:
            current = self.data(approval.incident_id).approval
            if current is None or current.id != approval.id:
                raise ApprovalInvalid("Approval does not belong to this incident")
            if current.status != ApprovalStatus.APPROVED:
                raise ApprovalInvalid(f"Approval status is {current.status}")
            current.status = ApprovalStatus.CONSUMED
            current.consumed_at = utc_now()
            approval.status = current.status
            approval.consumed_at = current.consumed_at

    def set_run(self, run: AgentRun) -> None:
        self.data(run.incident_id).run = run

    def save_run(self, run: AgentRun) -> None:
        current = self.data(run.incident_id).run
        if current is None or current.id != run.id:
            raise IncidentNotFound(f"Agent run {run.id}")
        self.data(run.incident_id).run = run

    def set_validation(self, validation: ValidationResult) -> None:
        self._assert_evidence_owned(validation.incident_id, validation.evidence_ids)
        self.data(validation.incident_id).validation = validation

    def set_report(self, report: IncidentReport) -> None:
        self._assert_evidence_owned(report.incident_id, report.evidence_ids)
        self.data(report.incident_id).report = report

    def append_audit(self, record: AuditRecord) -> None:
        self.audit.append(record)

    def append_evaluation_run(self, run: EvaluationRun) -> None:
        self.evaluation_runs.append(run)

    def incident_for_approval(self, approval_id: str) -> Incident | None:
        return next(
            (
                data.incident
                for data in self.incidents.values()
                if data.approval and data.approval.id == approval_id
            ),
            None,
        )

    def find_run(self, run_id: str) -> AgentRun | None:
        return next(
            (data.run for data in self.incidents.values() if data.run and data.run.id == run_id),
            None,
        )

    async def publish(self, event: IncidentEvent) -> None:
        self.data(event.incident_id).events.append(event)
        for queue in tuple(self._subscribers.get(event.incident_id, set())):
            await queue.put(event)

    def subscribe(self, incident_id: str) -> asyncio.Queue[IncidentEvent]:
        self.data(incident_id)
        queue: asyncio.Queue[IncidentEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(incident_id, set()).add(queue)
        return queue

    def unsubscribe(self, incident_id: str, queue: asyncio.Queue[IncidentEvent]) -> None:
        self._subscribers.get(incident_id, set()).discard(queue)


def configured_repository() -> InMemoryRepository:
    from app.config import settings

    if settings.persistence_backend == "memory":
        return InMemoryRepository()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required when PERSISTENCE_BACKEND=postgres")

    from app.infrastructure.postgres_repository import PostgresRepository

    return PostgresRepository.from_url(settings.database_url.get_secret_value())


repository = configured_repository()
