from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import overload

from sqlalchemy import Engine, create_engine, delete, select, update
from sqlalchemy.orm import Session

from app.application.store import InMemoryRepository
from app.domain.enums import (
    ApprovalStatus,
    DiagnosisOutcome,
    EvidenceType,
    ExecutionStatus,
    IncidentState,
    Severity,
    ToolRiskLevel,
)
from app.domain.errors import ApprovalInvalid
from app.domain.models import (
    AgentRun,
    Approval,
    AuditRecord,
    Diagnosis,
    EvaluationCaseResult,
    EvaluationRun,
    Evidence,
    Hypothesis,
    Incident,
    IncidentEvent,
    IncidentReport,
    RemediationPlan,
    RemediationStep,
    ToolCall,
    ValidationResult,
    utc_now,
)
from app.infrastructure.database import (
    AgentRunRow,
    ApprovalRow,
    AuditLogRow,
    Base,
    DiagnosisRow,
    EvaluationCaseResultRow,
    EvaluationRunRow,
    EvidenceRow,
    HypothesisRow,
    IncidentEventRow,
    IncidentReportRow,
    IncidentRow,
    RemediationPlanRow,
    RemediationStepRow,
    ToolCallRow,
    ValidationResultRow,
)


def _value(value: object) -> object:
    return getattr(value, "value", value)


@overload
def _utc(value: datetime) -> datetime: ...


@overload
def _utc(value: None) -> None: ...


def _utc(value: datetime | None) -> datetime | None:
    """Normalize timestamps returned by drivers such as SQLite in contract tests."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


class PostgresRepository(InMemoryRepository):
    """PostgreSQL-backed repository with an in-process cache for SSE delivery.

    PostgreSQL is the system of record. The cache keeps the existing single-process
    coordinator efficient and is rehydrated on startup. Approval consumption is always
    decided atomically in PostgreSQL, so separate workers cannot reuse one approval.
    """

    def __init__(self, engine: Engine, *, load_existing: bool = True) -> None:
        super().__init__()
        self.engine = engine
        if load_existing:
            self._load()

    @classmethod
    def from_url(cls, database_url: str) -> PostgresRepository:
        return cls(create_engine(database_url, pool_pre_ping=True))

    def _load(self) -> None:
        with Session(self.engine) as session:
            for incident_row in session.scalars(select(IncidentRow)).all():
                super().add_incident(
                    Incident(
                        id=incident_row.id,
                        title=incident_row.title,
                        description=incident_row.description,
                        severity=Severity(incident_row.severity),
                        state=IncidentState(incident_row.state),
                        affected_service=incident_row.affected_service,
                        affected_customers=incident_row.affected_customers,
                        execution_status=ExecutionStatus(incident_row.execution_status),
                        correlation_id=incident_row.correlation_id,
                        created_at=_utc(incident_row.created_at),
                        updated_at=_utc(incident_row.updated_at),
                    )
                )

            for event_row in session.scalars(select(IncidentEventRow)).all():
                self.data(event_row.incident_id).events.append(
                    IncidentEvent(
                        id=event_row.id,
                        incident_id=event_row.incident_id,
                        type=event_row.type,
                        title=event_row.title,
                        summary=event_row.summary,
                        status=ExecutionStatus(event_row.execution_status),
                        metadata=event_row.metadata_json,
                        correlation_id=event_row.correlation_id,
                        agent_run_id=event_row.agent_run_id,
                        tool_call_id=event_row.tool_call_id,
                        approval_id=event_row.approval_id,
                        created_at=_utc(event_row.created_at),
                    )
                )

            for evidence_row in session.scalars(select(EvidenceRow)).all():
                self.data(evidence_row.incident_id).evidence.append(
                    Evidence(
                        id=evidence_row.id,
                        incident_id=evidence_row.incident_id,
                        source_type=EvidenceType(evidence_row.source_type),
                        source_reference=evidence_row.source_reference,
                        title=evidence_row.title,
                        summary=evidence_row.summary,
                        raw_payload=evidence_row.raw_payload,
                        relevance=evidence_row.relevance,
                        correlation_id=evidence_row.correlation_id,
                        created_at=_utc(evidence_row.created_at),
                    )
                )

            for hypothesis_row in session.scalars(select(HypothesisRow)).all():
                self.data(hypothesis_row.incident_id).hypotheses.append(
                    Hypothesis(
                        id=hypothesis_row.id,
                        incident_id=hypothesis_row.incident_id,
                        title=hypothesis_row.title,
                        description=hypothesis_row.description,
                        confidence=hypothesis_row.confidence,
                        evidence_for=hypothesis_row.evidence_for,
                        evidence_against=hypothesis_row.evidence_against,
                        verification_strategy=hypothesis_row.verification_strategy,
                        status=hypothesis_row.status,
                        created_at=_utc(hypothesis_row.created_at),
                        updated_at=_utc(hypothesis_row.updated_at),
                    )
                )

            for diagnosis_row in session.scalars(select(DiagnosisRow)).all():
                self.data(diagnosis_row.incident_id).diagnosis = Diagnosis(
                    outcome=DiagnosisOutcome(diagnosis_row.outcome),
                    summary=diagnosis_row.summary,
                    probable_root_cause=diagnosis_row.probable_root_cause,
                    confidence=diagnosis_row.confidence,
                    evidence_ids=diagnosis_row.evidence_ids,
                    affected_services=diagnosis_row.affected_services,
                    recommended_next_step=diagnosis_row.recommended_next_step,
                )

            plans = {
                plan_row.id: plan_row
                for plan_row in session.scalars(select(RemediationPlanRow)).all()
            }
            steps_by_plan: dict[str, list[RemediationStepRow]] = {}
            for step_row in session.scalars(
                select(RemediationStepRow).order_by(RemediationStepRow.sequence)
            ).all():
                steps_by_plan.setdefault(step_row.plan_id, []).append(step_row)
            for plan_id, plan_row in plans.items():
                self.data(plan_row.incident_id).remediation_plan = RemediationPlan(
                    id=plan_row.id,
                    incident_id=plan_row.incident_id,
                    summary=plan_row.summary,
                    steps=[
                        RemediationStep(
                            id=step.id,
                            title=step.title,
                            description=step.description,
                            tool_name=step.tool_name,
                            arguments=step.arguments,
                            risk_level=ToolRiskLevel(step.risk_level),
                            status=ExecutionStatus(step.execution_status),
                        )
                        for step in steps_by_plan.get(plan_id, [])
                    ],
                    risk_level=ToolRiskLevel(plan_row.risk_level),
                    rollback_plan=plan_row.rollback_plan,
                    validation_plan=plan_row.validation_plan,
                )

            for run_row in session.scalars(
                select(AgentRunRow).order_by(AgentRunRow.started_at)
            ).all():
                self.data(run_row.incident_id).run = AgentRun(
                    id=run_row.id,
                    incident_id=run_row.incident_id,
                    provider=run_row.provider,
                    model=run_row.model,
                    workflow=run_row.workflow,
                    status=run_row.status,
                    trace_id=run_row.trace_id,
                    correlation_id=run_row.correlation_id,
                    started_at=_utc(run_row.started_at),
                    completed_at=_utc(run_row.completed_at),
                    tool_call_count=run_row.tool_call_count,
                    input_tokens=run_row.input_tokens,
                    output_tokens=run_row.output_tokens,
                    estimated_cost_usd=run_row.estimated_cost_usd,
                    error=run_row.error,
                )

            for call_row in session.scalars(
                select(ToolCallRow).order_by(ToolCallRow.created_at)
            ).all():
                self.data(call_row.incident_id).tool_calls.append(
                    ToolCall(
                        id=call_row.id,
                        incident_id=call_row.incident_id,
                        tool_name=call_row.tool_name,
                        arguments=call_row.arguments,
                        risk_level=ToolRiskLevel(call_row.risk_level),
                        status=ExecutionStatus(call_row.execution_status),
                        evidence_ids=call_row.evidence_ids,
                        duration_ms=call_row.duration_ms,
                        output_summary=call_row.output_summary,
                        created_at=_utc(call_row.created_at),
                        correlation_id=call_row.correlation_id,
                        agent_run_id=call_row.agent_run_id,
                    )
                )

            approval_rows = session.scalars(
                select(ApprovalRow).order_by(ApprovalRow.requested_at)
            ).all()
            for approval_row in approval_rows:
                self.data(approval_row.incident_id).approval = Approval(
                    id=approval_row.id,
                    incident_id=approval_row.incident_id,
                    tool_call_id=approval_row.tool_call_id,
                    tool_name=approval_row.tool_name,
                    requested_action=approval_row.requested_action,
                    arguments_hash=approval_row.arguments_hash,
                    reason=approval_row.reason,
                    evidence_ids=approval_row.evidence_ids,
                    potential_impact=approval_row.potential_impact,
                    requested_at=_utc(approval_row.requested_at),
                    expires_at=_utc(approval_row.expires_at),
                    approved_by=approval_row.approved_by,
                    approved_at=_utc(approval_row.approved_at),
                    status=ApprovalStatus(approval_row.status),
                    consumed_at=_utc(approval_row.consumed_at),
                    correlation_id=approval_row.correlation_id,
                    agent_run_id=approval_row.agent_run_id,
                )

            for validation_row in session.scalars(select(ValidationResultRow)).all():
                self.data(validation_row.incident_id).validation = ValidationResult(
                    incident_id=validation_row.incident_id,
                    passed=validation_row.passed,
                    summary=validation_row.summary,
                    evidence_ids=validation_row.evidence_ids,
                    checks_passed=validation_row.checks_passed,
                    checks_failed=validation_row.checks_failed,
                    recovered_transactions=validation_row.recovered_transactions,
                    created_at=_utc(validation_row.created_at),
                )

            for report_row in session.scalars(select(IncidentReportRow)).all():
                self.data(report_row.incident_id).report = IncidentReport.model_validate(
                    report_row.payload
                )

            audit_rows = session.scalars(
                select(AuditLogRow).order_by(AuditLogRow.timestamp.desc()).limit(200)
            ).all()
            self.audit = [self._audit_from_row(audit_row) for audit_row in reversed(audit_rows)]
            self.evaluation_runs = self._load_evaluation_runs(session)

    @staticmethod
    def _audit_from_row(row: AuditLogRow) -> AuditRecord:
        return AuditRecord(
            id=row.id,
            timestamp=_utc(row.timestamp),
            actor_type=row.actor_type,
            actor_id=row.actor_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            result=row.result,
            risk_level=ToolRiskLevel(row.risk_level) if row.risk_level else None,
            metadata=row.metadata_json,
            correlation_id=row.correlation_id,
            incident_id=row.incident_id,
            agent_run_id=row.agent_run_id,
            tool_call_id=row.tool_call_id,
            approval_id=row.approval_id,
        )

    @staticmethod
    def _load_evaluation_runs(session: Session) -> list[EvaluationRun]:
        runs: list[EvaluationRun] = []
        for row in session.scalars(
            select(EvaluationRunRow).order_by(EvaluationRunRow.created_at)
        ).all():
            result_rows = session.scalars(
                select(EvaluationCaseResultRow).where(
                    EvaluationCaseResultRow.run_id == row.id
                )
            ).all()
            results = [
                EvaluationCaseResult(
                    case_id=result.case_id,
                    passed=result.passed,
                    failure_reason=result.failure_reason,
                    **result.metrics,
                )
                for result in result_rows
            ]
            runs.append(
                EvaluationRun(
                    id=row.id,
                    provider=row.provider,
                    model=row.model,
                    sample_data=row.sample_data,
                    suite_version=row.suite_version,
                    run_kind=row.run_kind,
                    code_revision=row.code_revision,
                    created_at=row.created_at,
                    metrics=row.metrics,
                    results=results,
                )
            )
        return runs

    async def reset(self) -> None:
        with self.engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(delete(table))
        await super().reset()

    def add_incident(self, incident: Incident) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(
                IncidentRow(
                    id=incident.id,
                    title=incident.title,
                    description=incident.description,
                    severity=_value(incident.severity),
                    state=_value(incident.state),
                    affected_service=incident.affected_service,
                    affected_customers=incident.affected_customers,
                    execution_status=_value(incident.execution_status),
                    correlation_id=incident.correlation_id,
                    created_at=incident.created_at,
                    updated_at=incident.updated_at,
                )
            )
        super().add_incident(incident)

    def remove_incident(self, incident_id: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(delete(IncidentRow).where(IncidentRow.id == incident_id))
        super().remove_incident(incident_id)

    def save_incident(self, incident: Incident) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                update(IncidentRow)
                .where(IncidentRow.id == incident.id)
                .values(
                    state=_value(incident.state),
                    affected_customers=incident.affected_customers,
                    execution_status=_value(incident.execution_status),
                    updated_at=incident.updated_at,
                )
            )
        super().save_incident(incident)

    async def publish(self, event: IncidentEvent) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(
                IncidentEventRow(
                    id=event.id,
                    incident_id=event.incident_id,
                    type=event.type,
                    title=event.title,
                    summary=event.summary,
                    execution_status=_value(event.status),
                    metadata_json=event.metadata,
                    correlation_id=event.correlation_id,
                    agent_run_id=event.agent_run_id,
                    tool_call_id=event.tool_call_id,
                    approval_id=event.approval_id,
                    created_at=event.created_at,
                )
            )
        await super().publish(event)

    def add_evidence(self, evidence: Evidence) -> None:
        self.data(evidence.incident_id)
        with Session(self.engine) as session, session.begin():
            session.add(
                EvidenceRow(
                    id=evidence.id,
                    incident_id=evidence.incident_id,
                    source_type=_value(evidence.source_type),
                    source_reference=evidence.source_reference,
                    title=evidence.title,
                    summary=evidence.summary,
                    raw_payload=evidence.raw_payload,
                    relevance=evidence.relevance,
                    correlation_id=evidence.correlation_id,
                    created_at=evidence.created_at,
                )
            )
        super().add_evidence(evidence)

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self._assert_evidence_owned(
            hypothesis.incident_id, hypothesis.evidence_for + hypothesis.evidence_against
        )
        with Session(self.engine) as session, session.begin():
            session.add(self._hypothesis_row(hypothesis))
        super().add_hypothesis(hypothesis)

    @staticmethod
    def _hypothesis_row(hypothesis: Hypothesis) -> HypothesisRow:
        return HypothesisRow(
            id=hypothesis.id,
            incident_id=hypothesis.incident_id,
            title=hypothesis.title,
            description=hypothesis.description,
            confidence=hypothesis.confidence,
            evidence_for=hypothesis.evidence_for,
            evidence_against=hypothesis.evidence_against,
            verification_strategy=hypothesis.verification_strategy,
            status=hypothesis.status,
            created_at=hypothesis.created_at,
            updated_at=hypothesis.updated_at,
        )

    def save_hypothesis(self, hypothesis: Hypothesis) -> None:
        hypothesis.updated_at = utc_now()
        self._assert_evidence_owned(
            hypothesis.incident_id, hypothesis.evidence_for + hypothesis.evidence_against
        )
        with self.engine.begin() as connection:
            connection.execute(
                update(HypothesisRow)
                .where(HypothesisRow.id == hypothesis.id)
                .values(
                    confidence=hypothesis.confidence,
                    evidence_for=hypothesis.evidence_for,
                    evidence_against=hypothesis.evidence_against,
                    status=hypothesis.status,
                    updated_at=hypothesis.updated_at,
                )
            )
        super().save_hypothesis(hypothesis)

    def set_diagnosis(self, incident_id: str, diagnosis: Diagnosis) -> None:
        if diagnosis.outcome == DiagnosisOutcome.SUPPORTED_ROOT_CAUSE:
            self._assert_evidence_owned(incident_id, diagnosis.evidence_ids)
        with Session(self.engine) as session, session.begin():
            session.merge(
                DiagnosisRow(
                    id=f"diagnosis-{incident_id}",
                    incident_id=incident_id,
                    summary=diagnosis.summary,
                    probable_root_cause=diagnosis.probable_root_cause,
                    confidence=diagnosis.confidence,
                    evidence_ids=diagnosis.evidence_ids,
                    affected_services=diagnosis.affected_services,
                    recommended_next_step=diagnosis.recommended_next_step,
                    outcome=_value(diagnosis.outcome),
                )
            )
        super().set_diagnosis(incident_id, diagnosis)

    def set_remediation_plan(self, plan: RemediationPlan) -> None:
        with Session(self.engine) as session, session.begin():
            existing = session.scalar(
                select(RemediationPlanRow).where(RemediationPlanRow.incident_id == plan.incident_id)
            )
            if existing:
                session.execute(
                    delete(RemediationStepRow).where(RemediationStepRow.plan_id == existing.id)
                )
                session.delete(existing)
                session.flush()
            session.add(
                RemediationPlanRow(
                    id=plan.id,
                    incident_id=plan.incident_id,
                    summary=plan.summary,
                    risk_level=_value(plan.risk_level),
                    rollback_plan=plan.rollback_plan,
                    validation_plan=plan.validation_plan,
                )
            )
            session.add_all(
                [
                    RemediationStepRow(
                        id=step.id,
                        plan_id=plan.id,
                        sequence=index,
                        title=step.title,
                        description=step.description,
                        tool_name=step.tool_name,
                        arguments=step.arguments,
                        risk_level=_value(step.risk_level),
                        execution_status=_value(step.status),
                    )
                    for index, step in enumerate(plan.steps)
                ]
            )
        super().set_remediation_plan(plan)

    def add_tool_call(self, call: ToolCall) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(self._tool_call_row(call))
        super().add_tool_call(call)

    @staticmethod
    def _tool_call_row(call: ToolCall) -> ToolCallRow:
        return ToolCallRow(
            id=call.id,
            incident_id=call.incident_id,
            tool_name=call.tool_name,
            arguments=call.arguments,
            risk_level=_value(call.risk_level),
            execution_status=_value(call.status),
            evidence_ids=call.evidence_ids,
            duration_ms=call.duration_ms,
            output_summary=call.output_summary,
            correlation_id=call.correlation_id,
            agent_run_id=call.agent_run_id,
            created_at=call.created_at,
        )

    def save_tool_call(self, call: ToolCall) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                update(ToolCallRow)
                .where(ToolCallRow.id == call.id)
                .values(
                    execution_status=_value(call.status),
                    evidence_ids=call.evidence_ids,
                    duration_ms=call.duration_ms,
                    output_summary=call.output_summary,
                )
            )
        super().save_tool_call(call)

    def set_approval(self, approval: Approval) -> None:
        self._assert_evidence_owned(approval.incident_id, approval.evidence_ids)
        with Session(self.engine) as session, session.begin():
            session.add(self._approval_row(approval))
        super().set_approval(approval)

    @staticmethod
    def _approval_row(approval: Approval) -> ApprovalRow:
        return ApprovalRow(
            id=approval.id,
            incident_id=approval.incident_id,
            tool_call_id=approval.tool_call_id,
            tool_name=approval.tool_name,
            requested_action=approval.requested_action,
            arguments_hash=approval.arguments_hash,
            reason=approval.reason,
            evidence_ids=approval.evidence_ids,
            potential_impact=approval.potential_impact,
            requested_at=approval.requested_at,
            expires_at=approval.expires_at,
            approved_by=approval.approved_by,
            approved_at=approval.approved_at,
            status=_value(approval.status),
            consumed_at=approval.consumed_at,
            correlation_id=approval.correlation_id,
            agent_run_id=approval.agent_run_id,
        )

    def save_approval(self, approval: Approval) -> None:
        if approval.status in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
            allowed_current_statuses = [ApprovalStatus.PENDING.value]
        elif approval.status == ApprovalStatus.EXPIRED:
            allowed_current_statuses = [
                ApprovalStatus.PENDING.value,
                ApprovalStatus.APPROVED.value,
            ]
        else:
            raise ApprovalInvalid(
                "Approval decisions must move from pending to approved, rejected, or expired"
            )
        with self.engine.begin() as connection:
            result = connection.execute(
                update(ApprovalRow)
                .where(
                    ApprovalRow.id == approval.id,
                    ApprovalRow.incident_id == approval.incident_id,
                    ApprovalRow.status.in_(allowed_current_statuses),
                )
                .values(
                    status=_value(approval.status),
                    approved_by=approval.approved_by,
                    approved_at=approval.approved_at,
                    consumed_at=approval.consumed_at,
                )
            )
            if result.rowcount != 1:
                raise ApprovalInvalid("Approval is stale, invalid, or already decided")
        super().save_approval(approval)

    def consume_approval(self, approval: Approval) -> None:
        now = utc_now()
        with self.engine.begin() as connection:
            result = connection.execute(
                update(ApprovalRow)
                .where(
                    ApprovalRow.id == approval.id,
                    ApprovalRow.incident_id == approval.incident_id,
                    ApprovalRow.tool_call_id == approval.tool_call_id,
                    ApprovalRow.tool_name == approval.tool_name,
                    ApprovalRow.requested_action == approval.requested_action,
                    ApprovalRow.arguments_hash == approval.arguments_hash,
                    ApprovalRow.status == ApprovalStatus.APPROVED.value,
                    ApprovalRow.approved_by.is_not(None),
                    ApprovalRow.approved_at.is_not(None),
                    ApprovalRow.expires_at > now,
                )
                .values(status=ApprovalStatus.CONSUMED.value, consumed_at=now)
            )
            if result.rowcount != 1:
                raise ApprovalInvalid("Approval is invalid, expired, or already consumed")
        approval.consumed_at = now
        super().consume_approval(approval)

    def set_run(self, run: AgentRun) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(self._run_row(run))
        super().set_run(run)

    @staticmethod
    def _run_row(run: AgentRun) -> AgentRunRow:
        return AgentRunRow(
            id=run.id,
            incident_id=run.incident_id,
            provider=run.provider,
            model=run.model,
            workflow=run.workflow,
            status=run.status,
            trace_id=run.trace_id,
            correlation_id=run.correlation_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
            tool_call_count=run.tool_call_count,
            input_tokens=run.input_tokens,
            output_tokens=run.output_tokens,
            estimated_cost_usd=run.estimated_cost_usd,
            error=run.error,
        )

    def save_run(self, run: AgentRun) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                update(AgentRunRow)
                .where(AgentRunRow.id == run.id)
                .values(
                    status=run.status,
                    completed_at=run.completed_at,
                    tool_call_count=run.tool_call_count,
                    input_tokens=run.input_tokens,
                    output_tokens=run.output_tokens,
                    estimated_cost_usd=run.estimated_cost_usd,
                    error=run.error,
                )
            )
        super().save_run(run)

    def set_validation(self, validation: ValidationResult) -> None:
        self._assert_evidence_owned(validation.incident_id, validation.evidence_ids)
        with Session(self.engine) as session, session.begin():
            session.merge(
                ValidationResultRow(
                    incident_id=validation.incident_id,
                    passed=validation.passed,
                    summary=validation.summary,
                    evidence_ids=validation.evidence_ids,
                    checks_passed=validation.checks_passed,
                    checks_failed=validation.checks_failed,
                    recovered_transactions=validation.recovered_transactions,
                    created_at=validation.created_at,
                )
            )
        super().set_validation(validation)

    def set_report(self, report: IncidentReport) -> None:
        self._assert_evidence_owned(report.incident_id, report.evidence_ids)
        with Session(self.engine) as session, session.begin():
            session.merge(
                IncidentReportRow(
                    incident_id=report.incident_id,
                    correlation_id=report.correlation_id,
                    payload=report.model_dump(mode="json"),
                    generated_at=report.generated_at,
                )
            )
        super().set_report(report)

    def append_audit(self, record: AuditRecord) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(
                AuditLogRow(
                    id=record.id,
                    timestamp=record.timestamp,
                    actor_type=record.actor_type,
                    actor_id=record.actor_id,
                    action=record.action,
                    resource_type=record.resource_type,
                    resource_id=record.resource_id,
                    result=record.result,
                    risk_level=_value(record.risk_level) if record.risk_level else None,
                    metadata_json=record.metadata,
                    correlation_id=record.correlation_id,
                    incident_id=record.incident_id,
                    agent_run_id=record.agent_run_id,
                    tool_call_id=record.tool_call_id,
                    approval_id=record.approval_id,
                )
            )
        super().append_audit(record)

    def append_evaluation_run(self, run: EvaluationRun) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(
                EvaluationRunRow(
                    id=run.id,
                    provider=run.provider,
                    model=run.model,
                    sample_data=run.sample_data,
                    suite_version=run.suite_version,
                    run_kind=run.run_kind,
                    code_revision=run.code_revision,
                    metrics=run.metrics,
                    created_at=run.created_at,
                )
            )
            session.add_all(self._evaluation_result_rows(run))
        super().append_evaluation_run(run)

    @staticmethod
    def _evaluation_result_rows(run: EvaluationRun) -> Iterable[EvaluationCaseResultRow]:
        for result in run.results:
            payload = result.model_dump(mode="json")
            yield EvaluationCaseResultRow(
                run_id=run.id,
                case_id=result.case_id,
                passed=result.passed,
                metrics={
                    key: value
                    for key, value in payload.items()
                    if key not in {"case_id", "passed", "failure_reason"}
                },
                failure_reason=result.failure_reason,
            )
