"""Persist traceability, remediation, validation, and incident reports.

Revision ID: 0002
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("incidents", sa.Column("execution_status", sa.String(24), nullable=True))
    op.add_column("incidents", sa.Column("correlation_id", sa.String(64), nullable=True))
    op.execute("UPDATE incidents SET execution_status = 'SIMULATED'")
    op.execute("UPDATE incidents SET correlation_id = 'corr_' || md5(id)")
    op.alter_column("incidents", "execution_status", nullable=False)
    op.alter_column("incidents", "correlation_id", nullable=False)
    op.create_index("ix_incidents_correlation_id", "incidents", ["correlation_id"], unique=True)

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("workflow", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("tool_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("estimated_cost_usd", sa.Float()),
        sa.Column("error", sa.String(160)),
    )
    for column in ("incident_id", "status", "trace_id", "correlation_id"):
        op.create_index(
            f"ix_agent_runs_{column}",
            "agent_runs",
            [column],
            unique=column == "trace_id",
        )

    op.create_table(
        "remediation_plans",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("rollback_plan", sa.Text()),
        sa.Column("validation_plan", sa.Text(), nullable=False),
    )
    op.create_table(
        "remediation_steps",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "plan_id",
            sa.String(64),
            sa.ForeignKey("remediation_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(120)),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("execution_status", sa.String(24), nullable=False),
    )
    op.create_index("ix_remediation_steps_plan_id", "remediation_steps", ["plan_id"])
    op.create_table(
        "validation_results",
        sa.Column(
            "incident_id",
            sa.String(64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("checks_passed", sa.Integer(), nullable=False),
        sa.Column("checks_failed", sa.Integer(), nullable=False),
        sa.Column("recovered_transactions", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "incident_reports",
        sa.Column(
            "incident_id",
            sa.String(64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_incident_reports_correlation_id",
        "incident_reports",
        ["correlation_id"],
    )

    for name in ("correlation_id", "agent_run_id", "tool_call_id", "approval_id"):
        op.add_column("incident_events", sa.Column(name, sa.String(64), nullable=True))
        op.create_index(f"ix_incident_events_{name}", "incident_events", [name])
    op.execute("UPDATE incident_events SET correlation_id = 'corr_evt_' || md5(id)")
    op.alter_column("incident_events", "correlation_id", nullable=False)

    op.add_column("evidence", sa.Column("correlation_id", sa.String(64), nullable=True))
    op.execute("UPDATE evidence SET correlation_id = 'corr_evd_' || md5(id)")
    op.alter_column("evidence", "correlation_id", nullable=False)
    op.create_index("ix_evidence_correlation_id", "evidence", ["correlation_id"])

    op.add_column(
        "hypotheses",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "hypotheses",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "diagnoses",
        sa.Column(
            "outcome",
            sa.String(40),
            nullable=False,
            server_default="SUPPORTED_ROOT_CAUSE",
        ),
    )
    op.create_index("ix_diagnoses_outcome", "diagnoses", ["outcome"])

    op.add_column("tool_calls", sa.Column("output_summary", sa.Text()))
    op.add_column("tool_calls", sa.Column("correlation_id", sa.String(64), nullable=True))
    op.add_column("tool_calls", sa.Column("agent_run_id", sa.String(64)))
    op.execute("UPDATE tool_calls SET correlation_id = 'corr_tool_' || md5(id)")
    op.alter_column("tool_calls", "correlation_id", nullable=False)
    op.create_index("ix_tool_calls_correlation_id", "tool_calls", ["correlation_id"])
    op.create_index("ix_tool_calls_agent_run_id", "tool_calls", ["agent_run_id"])
    op.create_foreign_key(
        "fk_tool_calls_agent_run_id",
        "tool_calls",
        "agent_runs",
        ["agent_run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("approvals", sa.Column("tool_name", sa.String(120), nullable=True))
    op.add_column("approvals", sa.Column("reason", sa.Text(), nullable=True))
    op.add_column("approvals", sa.Column("evidence_ids", sa.JSON(), nullable=True))
    op.add_column("approvals", sa.Column("potential_impact", sa.Text(), nullable=True))
    op.add_column("approvals", sa.Column("consumed_at", sa.DateTime(timezone=True)))
    op.add_column("approvals", sa.Column("correlation_id", sa.String(64), nullable=True))
    op.add_column("approvals", sa.Column("agent_run_id", sa.String(64)))
    op.execute(
        "UPDATE approvals SET tool_name = tool_calls.tool_name, correlation_id = "
        "tool_calls.correlation_id FROM tool_calls WHERE approvals.tool_call_id = tool_calls.id"
    )
    op.execute("UPDATE approvals SET reason = 'Migrated approval', evidence_ids = '[]'::json")
    op.execute("UPDATE approvals SET potential_impact = 'Historical approval record'")
    for name in ("tool_name", "reason", "evidence_ids", "potential_impact", "correlation_id"):
        op.alter_column("approvals", name, nullable=False)
    op.create_index("ix_approvals_correlation_id", "approvals", ["correlation_id"])
    op.create_index("ix_approvals_agent_run_id", "approvals", ["agent_run_id"])
    op.create_foreign_key(
        "fk_approvals_agent_run_id",
        "approvals",
        "agent_runs",
        ["agent_run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    for name in ("correlation_id", "incident_id", "agent_run_id", "tool_call_id", "approval_id"):
        op.add_column("audit_logs", sa.Column(name, sa.String(64), nullable=True))
        op.create_index(f"ix_audit_logs_{name}", "audit_logs", [name])
    op.execute("UPDATE audit_logs SET correlation_id = 'corr_audit_' || md5(id)")
    op.alter_column("audit_logs", "correlation_id", nullable=False)

    op.add_column(
        "evaluation_runs",
        sa.Column("sample_data", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "suite_version",
            sa.String(80),
            nullable=False,
            server_default="resolveai-benchmark-v1",
        ),
    )
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "run_kind",
            sa.String(80),
            nullable=False,
            server_default="deterministic-contract",
        ),
    )
    op.add_column(
        "evaluation_runs",
        sa.Column("code_revision", sa.String(80), nullable=False, server_default="unknown"),
    )
    op.create_index("ix_evaluation_runs_suite_version", "evaluation_runs", ["suite_version"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_runs_suite_version", table_name="evaluation_runs")
    for name in ("code_revision", "run_kind", "suite_version", "sample_data"):
        op.drop_column("evaluation_runs", name)

    for name in ("approval_id", "tool_call_id", "agent_run_id", "incident_id", "correlation_id"):
        op.drop_index(f"ix_audit_logs_{name}", table_name="audit_logs")
        op.drop_column("audit_logs", name)

    op.drop_constraint("fk_approvals_agent_run_id", "approvals", type_="foreignkey")
    op.drop_index("ix_approvals_agent_run_id", table_name="approvals")
    op.drop_index("ix_approvals_correlation_id", table_name="approvals")
    for name in (
        "agent_run_id",
        "correlation_id",
        "consumed_at",
        "potential_impact",
        "evidence_ids",
        "reason",
        "tool_name",
    ):
        op.drop_column("approvals", name)

    op.drop_constraint("fk_tool_calls_agent_run_id", "tool_calls", type_="foreignkey")
    op.drop_index("ix_tool_calls_agent_run_id", table_name="tool_calls")
    op.drop_index("ix_tool_calls_correlation_id", table_name="tool_calls")
    for name in ("agent_run_id", "correlation_id", "output_summary"):
        op.drop_column("tool_calls", name)

    op.drop_index("ix_diagnoses_outcome", table_name="diagnoses")
    op.drop_column("diagnoses", "outcome")
    op.drop_column("hypotheses", "updated_at")
    op.drop_column("hypotheses", "created_at")
    op.drop_index("ix_evidence_correlation_id", table_name="evidence")
    op.drop_column("evidence", "correlation_id")

    for name in ("approval_id", "tool_call_id", "agent_run_id", "correlation_id"):
        op.drop_index(f"ix_incident_events_{name}", table_name="incident_events")
        op.drop_column("incident_events", name)

    op.drop_index("ix_incident_reports_correlation_id", table_name="incident_reports")
    op.drop_table("incident_reports")
    op.drop_table("validation_results")
    op.drop_index("ix_remediation_steps_plan_id", table_name="remediation_steps")
    op.drop_table("remediation_steps")
    op.drop_table("remediation_plans")
    for column in ("correlation_id", "trace_id", "status", "incident_id"):
        op.drop_index(f"ix_agent_runs_{column}", table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index("ix_incidents_correlation_id", table_name="incidents")
    op.drop_column("incidents", "correlation_id")
    op.drop_column("incidents", "execution_status")
