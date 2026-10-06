"""Initial evidence-first incident schema.

Revision ID: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


metadata = sa.MetaData()

sa.Table(
    "incidents",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("title", sa.String(240), nullable=False),
    sa.Column("description", sa.Text(), nullable=False),
    sa.Column("severity", sa.String(16), nullable=False, index=True),
    sa.Column("state", sa.String(40), nullable=False, index=True),
    sa.Column("affected_service", sa.String(100), nullable=False, index=True),
    sa.Column("affected_customers", sa.Integer(), nullable=False, server_default="0"),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    "incident_events",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("incident_id", sa.ForeignKey("incidents.id", ondelete="CASCADE"), index=True),
    sa.Column("type", sa.String(80), nullable=False, index=True),
    sa.Column("title", sa.String(240), nullable=False),
    sa.Column("summary", sa.Text(), nullable=False),
    sa.Column("execution_status", sa.String(24), nullable=False),
    sa.Column("metadata_json", sa.JSON(), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
    ),
)

sa.Table(
    "evidence",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("incident_id", sa.ForeignKey("incidents.id", ondelete="CASCADE"), index=True),
    sa.Column("source_type", sa.String(40), nullable=False, index=True),
    sa.Column("source_reference", sa.String(160), nullable=False),
    sa.Column("title", sa.String(240), nullable=False),
    sa.Column("summary", sa.Text(), nullable=False),
    sa.Column("raw_payload", sa.JSON(), nullable=False),
    sa.Column("relevance", sa.Float(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Index("ix_evidence_incident_source", "incident_id", "source_type"),
)

sa.Table(
    "hypotheses",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("incident_id", sa.ForeignKey("incidents.id", ondelete="CASCADE"), index=True),
    sa.Column("title", sa.String(240), nullable=False),
    sa.Column("description", sa.Text(), nullable=False),
    sa.Column("confidence", sa.Float(), nullable=False),
    sa.Column("evidence_for", sa.JSON(), nullable=False),
    sa.Column("evidence_against", sa.JSON(), nullable=False),
    sa.Column("verification_strategy", sa.Text(), nullable=False),
    sa.Column("status", sa.String(32), nullable=False),
)

sa.Table(
    "diagnoses",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column(
        "incident_id", sa.ForeignKey("incidents.id", ondelete="CASCADE"), unique=True
    ),
    sa.Column("summary", sa.Text(), nullable=False),
    sa.Column("probable_root_cause", sa.Text(), nullable=False),
    sa.Column("confidence", sa.Float(), nullable=False),
    sa.Column("evidence_ids", sa.JSON(), nullable=False),
    sa.Column("affected_services", sa.JSON(), nullable=False),
    sa.Column("recommended_next_step", sa.Text(), nullable=False),
)

sa.Table(
    "tool_calls",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("incident_id", sa.ForeignKey("incidents.id", ondelete="CASCADE"), index=True),
    sa.Column("tool_name", sa.String(120), nullable=False, index=True),
    sa.Column("arguments", sa.JSON(), nullable=False),
    sa.Column("risk_level", sa.String(32), nullable=False, index=True),
    sa.Column("execution_status", sa.String(24), nullable=False),
    sa.Column("evidence_ids", sa.JSON(), nullable=False),
    sa.Column("duration_ms", sa.Integer()),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    "approvals",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("incident_id", sa.ForeignKey("incidents.id", ondelete="CASCADE"), index=True),
    sa.Column(
        "tool_call_id",
        sa.ForeignKey("tool_calls.id", ondelete="CASCADE"),
        unique=True,
    ),
    sa.Column("requested_action", sa.Text(), nullable=False),
    sa.Column("arguments_hash", sa.String(64), nullable=False),
    sa.Column("status", sa.String(24), nullable=False, index=True),
    sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
    sa.Column("approved_by", sa.String(120)),
    sa.Column("approved_at", sa.DateTime(timezone=True)),
)

sa.Table(
    "audit_logs",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column("actor_type", sa.String(32), nullable=False, index=True),
    sa.Column("actor_id", sa.String(120), nullable=False),
    sa.Column("action", sa.String(160), nullable=False, index=True),
    sa.Column("resource_type", sa.String(80), nullable=False),
    sa.Column("resource_id", sa.String(120), nullable=False, index=True),
    sa.Column("result", sa.String(32), nullable=False),
    sa.Column("risk_level", sa.String(32)),
    sa.Column("metadata_json", sa.JSON(), nullable=False),
)

sa.Table(
    "evaluation_runs",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("provider", sa.String(80), nullable=False),
    sa.Column("model", sa.String(100), nullable=False),
    sa.Column("metrics", sa.JSON(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
)

sa.Table(
    "evaluation_case_results",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column(
        "run_id", sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True
    ),
    sa.Column("case_id", sa.String(120), nullable=False, index=True),
    sa.Column("passed", sa.Boolean(), nullable=False),
    sa.Column("metrics", sa.JSON(), nullable=False),
    sa.Column("failure_reason", sa.Text()),
)


def upgrade() -> None:
    metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    metadata.drop_all(bind=op.get_bind())
