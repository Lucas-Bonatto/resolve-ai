from __future__ import annotations

import asyncio

from app.agents.providers import AIProvider, configured_provider
from app.application.simulator import NovaPaySimulator, simulator
from app.application.store import InMemoryRepository, repository
from app.config import settings
from app.domain.enums import (
    ApprovalStatus,
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
    Evidence,
    Hypothesis,
    Incident,
    IncidentEvent,
    RemediationPlan,
    RemediationStep,
    utc_now,
)
from app.domain.state_machine import validate_transition
from app.tools.gateway import ToolGateway

FLAGSHIP_ID = "INC-2026-0042"


class IncidentCoordinator:
    def __init__(
        self,
        repo: InMemoryRepository = repository,
        environment: NovaPaySimulator = simulator,
        provider: AIProvider | None = None,
    ) -> None:
        self.repository = repo
        self.simulator = environment
        self.provider = provider or configured_provider()
        self.tools = ToolGateway(repo, environment)
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self.delay = min(max(settings.demo_event_delay_ms, 0), 2000) / 1000

    async def inject_flagship(self) -> Incident:
        existing = self.repository.incidents.get(FLAGSHIP_ID)
        active = self._tasks.get(FLAGSHIP_ID)
        if existing and active and not active.done():
            return existing.incident
        self.repository.incidents.pop(FLAGSHIP_ID, None)
        self.simulator.reset()
        self.simulator.inject("payment-webhook-regression")
        incident = Incident(
            id=FLAGSHIP_ID,
            title="Approved payments remain pending",
            description="NovaPay customers report successful payments remaining in pending state.",
            severity=Severity.SEV1,
            affected_service="webhook-worker",
            affected_customers=37,
        )
        self.repository.add_incident(incident)
        await self._emit(
            "incident.created",
            "Incident detected",
            "Monitoring detected 37 approved payments still pending.",
        )
        self.repository.audit.append(
            AuditRecord(
                actor_type="USER",
                actor_id="demo-operator",
                action="chaos.inject",
                resource_type="incident",
                resource_id=incident.id,
                result=ExecutionStatus.SIMULATED,
                metadata={"scenario": "payment-webhook-regression"},
            )
        )
        self._tasks[incident.id] = asyncio.create_task(self._investigate_bounded(incident.id))
        return incident

    async def _investigate_bounded(self, incident_id: str) -> None:
        try:
            await asyncio.wait_for(
                self.investigate(incident_id), timeout=settings.max_investigation_seconds
            )
        except TimeoutError:
            data = self.repository.data(incident_id)
            if data.run is None:
                data.run = AgentRun(
                    incident_id=incident_id, provider=self.provider.name, model=self.provider.model
                )
            data.run.status = "FAILED"
            data.run.error = "InvestigationTimeout"
            data.run.completed_at = utc_now()
            if data.incident.state not in {
                IncidentState.RESOLVED,
                IncidentState.FAILED,
                IncidentState.ESCALATED,
            }:
                await self._transition(
                    IncidentState.FAILED,
                    "Investigation timed out",
                    "The configured investigation deadline elapsed; no action was forced.",
                )

    async def investigate(self, incident_id: str) -> None:
        data = self.repository.data(incident_id)
        data.run = AgentRun(
            incident_id=incident_id, provider=self.provider.name, model=self.provider.model
        )
        try:
            await self._transition(
                IncidentState.TRIAGED, "Incident triaged", "Severity confirmed as SEV-1."
            )
            await self._transition(
                IncidentState.INVESTIGATING,
                "Investigation started",
                "Incident Coordinator started an evidence-first run.",
            )

            await self._tool_event(
                "search_transactions",
                {"status": "pending", "provider_status": "approved", "limit": 50},
            )
            self._add_evidence(
                Evidence(
                    id="TXN-901",
                    incident_id=incident_id,
                    source_type=EvidenceType.TRANSACTION,
                    source_reference="txn_901",
                    title="Affected transaction sample",
                    summary="37 transactions are approved by the provider but pending in NovaPay.",
                    raw_payload={"count": 37, "sample": ["txn_901", "txn_912", "txn_933"]},
                    relevance=0.84,
                )
            )
            await self._emit(
                "evidence.created",
                "Affected transactions identified",
                "37 correlated transactions added as evidence.",
                {"evidence_ids": ["TXN-901"]},
            )

            await self._tool_event("get_service_health", {"service": "payment-provider"})
            self._add_evidence(
                Evidence(
                    id="METRIC-PROVIDER-01",
                    incident_id=incident_id,
                    source_type=EvidenceType.SERVICE_METRIC,
                    source_reference="payment-provider",
                    title="Provider health normal",
                    summary=(
                        "The payment provider reports normal health during the incident window."
                    ),
                    raw_payload={"status": "healthy", "availability": 0.9998},
                    relevance=0.71,
                )
            )
            data.hypotheses.append(
                Hypothesis(
                    incident_id=incident_id,
                    title="Payment provider outage",
                    description="The external provider may not be confirming payments.",
                    confidence=0.24,
                    evidence_against=["METRIC-PROVIDER-01"],
                    verification_strategy="Compare provider health and transaction receipts.",
                    status="WEAKENED",
                )
            )
            await self._emit(
                "hypothesis.created",
                "Provider outage hypothesis weakened",
                "Provider health is normal; confidence reduced to low.",
            )

            await self._tool_event(
                "query_application_logs",
                {
                    "service": "webhook-worker",
                    "query": "ValidationError paymentStatus",
                    "limit": 100,
                },
            )
            for evidence in [
                Evidence(
                    id="LOG-291",
                    incident_id=incident_id,
                    source_type=EvidenceType.LOG,
                    source_reference="log_00291",
                    title="Webhook schema validation failure",
                    summary=(
                        "The worker rejects payment.approved events because "
                        "paymentStatus is not permitted."
                    ),
                    raw_payload={
                        "level": "error",
                        "message": "ValidationError: field paymentStatus not permitted",
                    },
                    relevance=0.96,
                ),
                Evidence(
                    id="LOG-294",
                    incident_id=incident_id,
                    source_type=EvidenceType.LOG,
                    source_reference="log_00294",
                    title="Failure window correlation",
                    summary="Validation failures began four minutes after dep_184.",
                    raw_payload={"first_seen": "2026-09-30T12:45:04Z", "count": 142},
                    relevance=0.94,
                ),
            ]:
                self._add_evidence(evidence)
            await self._emit(
                "evidence.created",
                "Error pattern identified",
                "Schema validation errors began inside the deployment window.",
                {"evidence_ids": ["LOG-291", "LOG-294"]},
            )

            await self._tool_event(
                "get_recent_deployments", {"service": "webhook-worker", "limit": 5}
            )
            self._add_evidence(
                Evidence(
                    id="DEPLOY-184",
                    incident_id=incident_id,
                    source_type=EvidenceType.DEPLOYMENT,
                    source_reference="dep_184",
                    title="Webhook worker deployment dep_184",
                    summary=(
                        "Deployment dep_184 changed the parser four minutes before failures began."
                    ),
                    raw_payload={"commit": "7be91af", "previous": "dep_183"},
                    relevance=0.95,
                )
            )
            webhook_hypothesis = Hypothesis(
                incident_id=incident_id,
                title="Webhook schema regression",
                description=(
                    "Deployment dep_184 removed compatibility for the provider's "
                    "paymentStatus field."
                ),
                confidence=0.68,
                evidence_for=["LOG-291", "LOG-294", "DEPLOY-184"],
                verification_strategy="Run the legacy payload regression fixture.",
                status="TESTING",
            )
            data.hypotheses.append(webhook_hypothesis)
            await self._emit(
                "hypothesis.created",
                "Webhook regression hypothesis",
                "Deployment and log timing support a parser regression.",
            )

            await self._tool_event("run_regression_test", {"fixture": "legacy-payment-approved-v2"})
            self._add_evidence(
                Evidence(
                    id="TEST-012",
                    incident_id=incident_id,
                    source_type=EvidenceType.TEST_RESULT,
                    source_reference="test_legacy_payment_status_alias",
                    title="Regression reproduced",
                    summary="The controlled legacy payload fails on dep_184 and passes on dep_183.",
                    raw_payload={"dep_184": "failed", "dep_183": "passed"},
                    relevance=0.99,
                )
            )
            webhook_hypothesis.confidence = 0.89
            webhook_hypothesis.evidence_for.append("TEST-012")
            webhook_hypothesis.status = "CONFIRMED"
            await self._emit(
                "hypothesis.updated",
                "Regression hypothesis confirmed",
                "Controlled test reproduced the exact failure; confidence is high.",
                {"evidence_ids": ["TEST-012"]},
            )

            await self._transition(
                IncidentState.EVIDENCE_COLLECTED,
                "Evidence collection complete",
                "Six evidence records support or challenge the active hypotheses.",
            )
            await self._transition(
                IncidentState.DIAGNOSING,
                "Generating diagnosis",
                "Provider is producing a typed diagnosis from validated evidence.",
            )
            diagnosis = await self.provider.diagnose(data.incident.description, data.evidence)
            known_evidence = {item.id for item in data.evidence}
            if not set(diagnosis.evidence_ids).issubset(known_evidence):
                raise ValueError("Diagnosis referenced evidence outside this incident")
            data.diagnosis = diagnosis
            await self._transition(
                IncidentState.DIAGNOSED, "Root cause identified", diagnosis.probable_root_cause
            )

            rollback_args = {
                "service": "webhook-worker",
                "deployment_id": "dep_184",
                "target_deployment": "dep_183",
            }
            data.remediation_plan = RemediationPlan(
                incident_id=incident_id,
                summary=(
                    "Rollback dep_184, restore the compatible parser, then replay "
                    "and validate affected events."
                ),
                steps=[
                    RemediationStep(
                        title="Rollback webhook worker",
                        description="Restore dep_183.",
                        tool_name="request_service_rollback",
                        arguments=rollback_args,
                        risk_level=ToolRiskLevel.CRITICAL_WRITE,
                    ),
                    RemediationStep(
                        title="Validate event processing",
                        description="Run regression and recovery checks.",
                        tool_name="validate_remediation",
                        arguments={"incident_id": incident_id},
                        risk_level=ToolRiskLevel.READ,
                    ),
                ],
                risk_level=ToolRiskLevel.CRITICAL_WRITE,
                rollback_plan=(
                    "If validation fails, keep dep_183 active and escalate to the payments team."
                ),
                validation_plan=(
                    "Run 12 parser tests and verify all 37 pending transactions recover."
                ),
            )
            await self._transition(
                IncidentState.PLAN_PROPOSED,
                "Remediation plan proposed",
                data.remediation_plan.summary,
            )
            _, approval = self.tools.propose_critical(
                incident_id,
                "request_service_rollback",
                rollback_args,
                reason=(
                    "Failures began after dep_184 and the regression test reproduces "
                    "the parser defect."
                ),
                evidence_ids=["DEPLOY-184", "LOG-291", "TEST-012"],
                impact="A brief webhook processing interruption while the worker restarts.",
            )
            await self._transition(
                IncidentState.AWAITING_APPROVAL,
                "Human approval required",
                "Critical rollback is paused pending an operator decision.",
            )
            await self._emit(
                "approval.requested",
                "Approval requested",
                approval.requested_action,
                {"approval_id": approval.id},
            )
            data.run.status = "WAITING_FOR_APPROVAL"
        except Exception as exc:
            data.run.status = "FAILED"
            data.run.error = type(exc).__name__
            data.run.completed_at = utc_now()
            if data.incident.state not in {
                IncidentState.FAILED,
                IncidentState.RESOLVED,
                IncidentState.ESCALATED,
            }:
                try:
                    await self._transition(
                        IncidentState.FAILED,
                        "Investigation failed",
                        "The run stopped safely and requires operator review.",
                    )
                except Exception as transition_error:
                    data.run.error = f"{data.run.error};{type(transition_error).__name__}"

    async def approve(self, incident_id: str, approval_id: str, actor: str) -> Approval:
        data = self.repository.data(incident_id)
        approval = data.approval
        if approval is None or approval.id != approval_id:
            raise ApprovalInvalid("Approval does not belong to this incident")
        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalInvalid("Approval has already been decided")
        if approval.expires_at <= utc_now():
            approval.status = ApprovalStatus.EXPIRED
            raise ApprovalInvalid("Approval has expired")
        approval.status = ApprovalStatus.APPROVED
        approval.approved_by = actor
        approval.approved_at = utc_now()
        self.repository.audit.append(
            AuditRecord(
                actor_type="USER",
                actor_id=actor,
                action="approval.approved",
                resource_type="approval",
                resource_id=approval.id,
                result="APPROVED",
                risk_level=ToolRiskLevel.CRITICAL_WRITE,
            )
        )
        await self._emit(
            "approval.approved",
            "Rollback approved",
            f"{actor} approved the exact requested action.",
            {"approval_id": approval.id},
        )
        await self._transition(
            IncidentState.EXECUTING,
            "Executing approved remediation",
            "The argument-bound rollback is now executing.",
        )
        call, _ = self.tools.execute_approved(approval)
        approval.status = ApprovalStatus.CONSUMED
        if data.remediation_plan:
            data.remediation_plan.steps[0].status = ExecutionStatus.SIMULATED
        await self._emit(
            "tool.completed",
            "Rollback completed",
            "webhook-worker now runs dep_183.",
            {"tool_call_id": call.id},
        )
        await self._transition(
            IncidentState.VALIDATING,
            "Validating outcome",
            "Regression and transaction recovery checks are running.",
        )
        await self._tool_event("validate_remediation", {"incident_id": incident_id})
        self._add_evidence(
            Evidence(
                id="TEST-POST-ROLLBACK",
                incident_id=incident_id,
                source_type=EvidenceType.TEST_RESULT,
                source_reference="validation_run_13",
                title="Post-remediation validation passed",
                summary="12 parser tests passed and all 37 pending transactions recovered.",
                raw_payload={"passed": 12, "failed": 0, "recovered": 37},
                relevance=1.0,
            )
        )
        if data.remediation_plan:
            data.remediation_plan.steps[1].status = ExecutionStatus.SIMULATED
        await self._emit(
            "validation.completed",
            "Validation passed",
            "All controlled checks passed; no pending transactions remain.",
            {"evidence_ids": ["TEST-POST-ROLLBACK"]},
        )
        await self._transition(
            IncidentState.RESOLVED,
            "Incident resolved",
            "Rollback succeeded and the recovery was verified.",
        )
        if data.run:
            data.run.status = "COMPLETED"
            data.run.completed_at = utc_now()
            data.run.tool_call_count = len(data.tool_calls)
        return approval

    async def reject(self, incident_id: str, approval_id: str, actor: str) -> Approval:
        data = self.repository.data(incident_id)
        approval = data.approval
        if (
            approval is None
            or approval.id != approval_id
            or approval.status != ApprovalStatus.PENDING
        ):
            raise ApprovalInvalid("Approval is invalid or already decided")
        approval.status = ApprovalStatus.REJECTED
        approval.approved_by = actor
        approval.approved_at = utc_now()
        self.repository.audit.append(
            AuditRecord(
                actor_type="USER",
                actor_id=actor,
                action="approval.rejected",
                resource_type="approval",
                resource_id=approval.id,
                result="REJECTED",
                risk_level=ToolRiskLevel.CRITICAL_WRITE,
            )
        )
        await self._emit(
            "approval.rejected",
            "Rollback rejected",
            "No critical action executed.",
            {"approval_id": approval.id},
        )
        await self._transition(
            IncidentState.ESCALATED,
            "Incident escalated",
            "Operator rejected the proposed rollback.",
        )
        if data.run:
            data.run.status = "ESCALATED"
            data.run.completed_at = utc_now()
        return approval

    async def _tool_event(self, name: str, arguments: dict[str, object]) -> None:
        await self._emit(
            "tool.started", f"Running {name}", "Validated tool call started.", {"tool": name}
        )
        await self._pause()
        call, _ = self.tools.execute_safe(FLAGSHIP_ID, name, arguments)
        await self._emit(
            "tool.completed",
            f"{name} completed",
            call.output_summary or "Structured result returned.",
            {"tool_call_id": call.id, "duration_ms": call.duration_ms},
        )

    def _add_evidence(self, evidence: Evidence) -> None:
        if evidence.id not in {
            item.id for item in self.repository.data(evidence.incident_id).evidence
        }:
            self.repository.data(evidence.incident_id).evidence.append(evidence)

    async def _transition(self, state: IncidentState, title: str, summary: str) -> None:
        incident = self.repository.data(FLAGSHIP_ID).incident
        validate_transition(incident.state, state)
        incident.state = state
        incident.updated_at = utc_now()
        await self._emit("incident.state_changed", title, summary, {"state": state})
        await self._pause()

    async def _emit(
        self, event_type: str, title: str, summary: str, metadata: dict[str, object] | None = None
    ) -> None:
        await self.repository.publish(
            IncidentEvent(
                incident_id=FLAGSHIP_ID,
                type=event_type,
                title=title,
                summary=summary,
                metadata=metadata or {},
            )
        )

    async def _pause(self) -> None:
        if self.delay:
            await asyncio.sleep(self.delay)


coordinator = IncidentCoordinator()
