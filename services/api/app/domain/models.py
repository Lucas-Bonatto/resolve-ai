from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import (
    ApprovalStatus,
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


class Diagnosis(StrictModel):
    summary: str
    probable_root_cause: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    affected_services: list[str]
    recommended_next_step: str

    @field_validator("evidence_ids")
    @classmethod
    def requires_evidence(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("A diagnosis must reference evidence")
        return list(dict.fromkeys(value))


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


class AgentRun(StrictModel):
    id: str = Field(default_factory=lambda: new_id("run"))
    incident_id: str
    provider: str
    model: str
    workflow: str = "incident-coordinator"
    status: str = "RUNNING"
    trace_id: str = Field(default_factory=lambda: new_id("trace"))
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    tool_call_count: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    error: str | None = None


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
    duration_ms: int
    failure_reason: str | None = None


class EvaluationRun(StrictModel):
    id: str = Field(default_factory=lambda: new_id("eval"))
    provider: str
    model: str
    sample_data: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    results: list[EvaluationCaseResult]
    metrics: dict[str, float]
