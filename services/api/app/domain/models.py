from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import (
    ApprovalStatus,
    DiagnosisOutcome,
    EvidenceType,
    ExecutionStatus,
    IncidentState,
    Severity,
    ToolRiskLevel,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def arguments_hash(arguments: dict[str, Any]) -> str:
    canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode()).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class Incident(StrictModel):
    id: str
    title: str
    description: str
    severity: Severity
    state: IncidentState = IncidentState.NEW
    affected_service: str
    affected_customers: int = 0
    execution_status: ExecutionStatus = ExecutionStatus.SIMULATED
    correlation_id: str = Field(default_factory=lambda: new_id("corr"))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class IncidentEvent(StrictModel):
    id: str = Field(default_factory=lambda: new_id("evt"))
    incident_id: str
    type: str
    title: str
    summary: str
    status: ExecutionStatus = ExecutionStatus.SIMULATED
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
    agent_run_id: str | None = None
    tool_call_id: str | None = None
    approval_id: str | None = None


class Evidence(StrictModel):
    id: str
    incident_id: str
    source_type: EvidenceType
    source_reference: str
    title: str
    summary: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    relevance: float = Field(ge=0, le=1)
    correlation_id: str


class Hypothesis(StrictModel):
    id: str = Field(default_factory=lambda: new_id("hyp"))
    incident_id: str
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    verification_strategy: str
    status: str = "OPEN"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Diagnosis(StrictModel):
    outcome: DiagnosisOutcome = DiagnosisOutcome.SUPPORTED_ROOT_CAUSE
    summary: str
    probable_root_cause: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    affected_services: list[str]
    recommended_next_step: str

    @model_validator(mode="after")
    def validates_evidence_contract(self) -> Diagnosis:
        self.evidence_ids = list(dict.fromkeys(self.evidence_ids))
        if self.outcome == DiagnosisOutcome.SUPPORTED_ROOT_CAUSE and not self.evidence_ids:
            raise ValueError("A supported diagnosis must reference evidence")
        if self.outcome == DiagnosisOutcome.INSUFFICIENT_EVIDENCE:
            self.probable_root_cause = DiagnosisOutcome.INSUFFICIENT_EVIDENCE
            self.confidence = min(self.confidence, 0.25)
        return self


class RemediationStep(StrictModel):
    id: str = Field(default_factory=lambda: new_id("step"))
    title: str
    description: str
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    risk_level: ToolRiskLevel
    status: ExecutionStatus = ExecutionStatus.NOT_EXECUTED


class RemediationPlan(StrictModel):
    id: str = Field(default_factory=lambda: new_id("plan"))
    incident_id: str
    summary: str
    steps: list[RemediationStep]
    risk_level: ToolRiskLevel
    rollback_plan: str | None
    validation_plan: str


class Approval(StrictModel):
    id: str = Field(default_factory=lambda: new_id("apr"))
    incident_id: str
    tool_call_id: str
    tool_name: str
    requested_action: str
    arguments_hash: str
    reason: str
    evidence_ids: list[str]
    potential_impact: str
    requested_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(default_factory=lambda: utc_now() + timedelta(minutes=15))
    approved_by: str | None = None
    approved_at: datetime | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    consumed_at: datetime | None = None
    correlation_id: str
    agent_run_id: str | None = None


class ToolCall(StrictModel):
    id: str = Field(default_factory=lambda: new_id("tool"))
    incident_id: str
    tool_name: str
    arguments: dict[str, Any]
    risk_level: ToolRiskLevel
    status: ExecutionStatus = ExecutionStatus.NOT_EXECUTED
    evidence_ids: list[str] = Field(default_factory=list)
    duration_ms: int | None = None
    output_summary: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    correlation_id: str
    agent_run_id: str | None = None


class AuditRecord(StrictModel):
    id: str = Field(default_factory=lambda: new_id("audit"))
    timestamp: datetime = Field(default_factory=utc_now)
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    result: str
    risk_level: ToolRiskLevel | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
    incident_id: str | None = None
    agent_run_id: str | None = None
    tool_call_id: str | None = None
    approval_id: str | None = None


class AgentRun(StrictModel):
    id: str = Field(default_factory=lambda: new_id("run"))
    incident_id: str
    provider: str
    model: str
    workflow: str = "incident-coordinator"
    status: str = "RUNNING"
    trace_id: str = Field(default_factory=lambda: new_id("trace"))
    correlation_id: str
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    tool_call_count: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    error: str | None = None


class ValidationResult(StrictModel):
    incident_id: str
    passed: bool
    summary: str
    evidence_ids: list[str]
    checks_passed: int = Field(ge=0)
    checks_failed: int = Field(ge=0)
    recovered_transactions: int = Field(ge=0)
    created_at: datetime = Field(default_factory=utc_now)


class IncidentReport(StrictModel):
    incident_id: str
    correlation_id: str
    summary: str
    timeline_event_ids: list[str]
    evidence_ids: list[str]
    hypothesis_ids: list[str]
    diagnosis: Diagnosis | None
    remediation_plan_id: str | None
    approval_id: str | None
    validation: ValidationResult | None
    final_status: IncidentState
    generated_at: datetime = Field(default_factory=utc_now)


class IncidentSnapshot(StrictModel):
    incident: Incident
    events: list[IncidentEvent]
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]
    diagnosis: Diagnosis | None
    remediation_plan: RemediationPlan | None
    approval: Approval | None
    tool_calls: list[ToolCall]
    run: AgentRun | None
    validation: ValidationResult | None
    report: IncidentReport | None


class EvaluationCase(StrictModel):
    id: str
    title: str
    category: str
    incident: dict[str, Any]
    expected_root_cause: str
    required_evidence_ids: list[str]
    allowed_tools: list[str]
    forbidden_tools: list[str]
    requires_human_approval: bool
    expected_action: str
    expected_state: str
    severity: str


class EvaluationCaseResult(StrictModel):
    case_id: str
    passed: bool
    diagnosis_correct: bool
    evidence_recall: float
    tool_selection_correct: bool
    unsupported_claims: int
    prohibited_action_attempts: int
    approval_bypass_attempts: int
    unauthorized_critical_executions: int
    prompt_injection_bypasses: int = 0
    evidence_integrity_violations: int = 0
    structured_output_valid: bool = True
    tool_failure_handled: bool = True
    duration_ms: int
    failure_reason: str | None = None


class EvaluationRun(StrictModel):
    id: str = Field(default_factory=lambda: new_id("eval"))
    provider: str
    model: str
    sample_data: bool = False
    suite_version: str = "resolveai-benchmark-v1"
    run_kind: str = "deterministic-contract"
    code_revision: str = "unknown"
    created_at: datetime = Field(default_factory=utc_now)
    results: list[EvaluationCaseResult]
    metrics: dict[str, float]
