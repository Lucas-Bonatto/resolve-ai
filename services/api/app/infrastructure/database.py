from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uuid_text() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class IncidentRow(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    state: Mapped[str] = mapped_column(String(40), index=True)
    affected_service: Mapped[str] = mapped_column(String(100), index=True)
    affected_customers: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IncidentEventRow(Base):
    __tablename__ = "incident_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_text)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    execution_status: Mapped[str] = mapped_column(String(24))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class EvidenceRow(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    source_reference: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    relevance: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_evidence_incident_source", "incident_id", "source_type"),)


class HypothesisRow(Base):
    __tablename__ = "hypotheses"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_text)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_for: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_against: Mapped[list[str]] = mapped_column(JSON, default=list)
    verification_strategy: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))


class DiagnosisRow(Base):
    __tablename__ = "diagnoses"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_text)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), unique=True
    )
    summary: Mapped[str] = mapped_column(Text)
    probable_root_cause: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    affected_services: Mapped[list[str]] = mapped_column(JSON)
    recommended_next_step: Mapped[str] = mapped_column(Text)


class ToolCallRow(Base):
    __tablename__ = "tool_calls"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    tool_name: Mapped[str] = mapped_column(String(120), index=True)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON)
    risk_level: Mapped[str] = mapped_column(String(32), index=True)
    execution_status: Mapped[str] = mapped_column(String(24))
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    duration_ms: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApprovalRow(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    tool_call_id: Mapped[str] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="CASCADE"), unique=True
    )
    requested_action: Mapped[str] = mapped_column(Text)
    arguments_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    approved_by: Mapped[str | None] = mapped_column(String(120))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLogRow(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    actor_type: Mapped[str] = mapped_column(String(32), index=True)
    actor_id: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(160), index=True)
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(120), index=True)
    result: Mapped[str] = mapped_column(String(32))
    risk_level: Mapped[str | None] = mapped_column(String(32))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class EvaluationRunRow(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_text)
    provider: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(100))
    metrics: Mapped[dict[str, float]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class EvaluationCaseResultRow(Base):
    __tablename__ = "evaluation_case_results"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_text)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True
    )
    case_id: Mapped[str] = mapped_column(String(120), index=True)
    passed: Mapped[bool]
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON)
    failure_reason: Mapped[str | None] = mapped_column(Text)
