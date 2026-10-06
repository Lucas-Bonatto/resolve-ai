from __future__ import annotations

import asyncio
from typing import Any, Literal

from app.agents.providers import AIProvider, configured_provider
from app.application.simulator import NovaPaySimulator, simulator
from app.application.store import InMemoryRepository, repository
from app.config import settings
from app.domain.enums import (
    ApprovalStatus,
    DiagnosisOutcome,
    EvidenceType,
    ExecutionStatus,
    IncidentState,
    Severity,
    ToolRiskLevel,
)
from app.domain.errors import ApprovalInvalid, ToolExecutionFailed
from app.domain.models import (
    AgentRun,
    Approval,
    AuditRecord,
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

    async def inject_flagship(
        self,
        correlation_id: str | None = None,
        actor_id: str = "demo-operator",
        actor_type: Literal["USER", "SYSTEM"] = "USER",
    ) -> Incident:
        existing = self.repository.incidents.get(FLAGSHIP_ID)
        active = self._tasks.get(FLAGSHIP_ID)
        if existing and active and not active.done():
            return existing.incident
        self.repository.remove_incident(FLAGSHIP_ID)
        self.simulator.reset()
        self.simulator.inject("payment-webhook-regression")
        incident_values: dict[str, Any] = {
            "id": FLAGSHIP_ID,
            "title": "Approved payments remain pending",
            "description": (
                "NovaPay customers report successful payments remaining in pending state."
            ),
            "severity": Severity.SEV1,
            "affected_service": "webhook-worker",
            "affected_customers": 37,
        }
        if correlation_id:
            incident_values["correlation_id"] = correlation_id
        incident = Incident(**incident_values)
        self.repository.add_incident(incident)
        await self._emit(
            incident.id,
            "incident.created",
            "Incident detected",
            "Monitoring detected 37 approved payments still pending.",
        )
        self._audit(
            incident.id,
            actor_type=actor_type,
            actor_id=actor_id,
            action="chaos.inject",
            resource_type="incident",
            resource_id=incident.id,
            result=ExecutionStatus.SIMULATED,
            metadata={"scenario": "payment-webhook-regression"},
        )
        self._tasks[incident.id] = asyncio.create_task(self._investigate_bounded(incident.id))
        return incident

    async def wait_for_investigation(self, incident_id: str) -> None:
        task = self._tasks.get(incident_id)
        if task is not None:
            await task

    async def _investigate_bounded(self, incident_id: str) -> None:
        try:
            await asyncio.wait_for(
                self.investigate(incident_id), timeout=settings.max_investigation_seconds
            )
        except TimeoutError:
            data = self.repository.data(incident_id)
            if data.run is None:
                self.repository.set_run(
                    AgentRun(
                        incident_id=incident_id,
                        provider=self.provider.name,
                        model=self.provider.model,
                        correlation_id=data.incident.correlation_id,
                    )
                )
            assert data.run is not None
            data.run.status = "FAILED"
            data.run.error = "InvestigationTimeout"
            data.run.completed_at = utc_now()
            self.repository.save_run(data.run)
            if data.incident.state not in {
                IncidentState.RESOLVED,
                IncidentState.FAILED,
                IncidentState.ESCALATED,
            }:
                await self._transition(
                    incident_id,
                    IncidentState.FAILED,
                    "Investigation timed out",
                    "The configured investigation deadline elapsed; no action was forced.",
                )

    async def investigate(self, incident_id: str) -> None:
        data = self.repository.data(incident_id)
        run = AgentRun(
            incident_id=incident_id,
            provider=self.provider.name,
            model=self.provider.model,
            correlation_id=data.incident.correlation_id,
        )
        self.repository.set_run(run)
        try:
            await self._transition(
                incident_id,
                IncidentState.TRIAGED,
                "Incident triaged",
                "Severity confirmed as SEV-1.",
            )
            await self._transition(
                incident_id,
                IncidentState.INVESTIGATING,
                "Investigation started",
                "Incident Coordinator started an evidence-first run.",
            )

            transaction_call, transaction_output = await self._tool_event(
                incident_id,
                "search_transactions",
                {"status": "pending", "provider_status": "approved", "limit": 50},
            )
            transaction_count = transaction_output.get("count")
            if (
                not isinstance(transaction_count, int)
                or transaction_count <= 0
                or transaction_output.get("provider_status") != "approved"
                or transaction_output.get("novapay_status") != "pending"
            ):
                raise ToolExecutionFailed("Transaction evidence is unavailable")
            self._add_evidence(
                Evidence(
                    id="TXN-901",
                    incident_id=incident_id,
                    source_type=EvidenceType.TRANSACTION,
                    source_reference="txn_901",
                    title="Affected transaction sample",
                    summary=(
                        f"{transaction_count} transactions are approved by the provider "
                        "but pending in NovaPay."
                    ),
                    raw_payload=transaction_output,
                    relevance=0.84,
                    correlation_id=data.incident.correlation_id,
                )
            )
            self._link_tool_evidence(transaction_call, ["TXN-901"])
            await self._emit(
                incident_id,
                "evidence.created",
                "Affected transactions identified",
                f"{transaction_count} correlated transactions added as evidence.",
                {"evidence_ids": ["TXN-901"]},
            )

            health_call, health_output = await self._tool_event(
                incident_id,
                "get_service_health",
                {"service": "payment-provider"},
            )
            provider_healthy = (
                health_output.get("status") == "healthy"
                and isinstance(health_output.get("availability"), (int, float))
            )
            provider_evidence_ids: list[str] = []
            if provider_healthy:
                provider_evidence = Evidence(
                    id="METRIC-PROVIDER-01",
                    incident_id=incident_id,
                    source_type=EvidenceType.SERVICE_METRIC,
                    source_reference="payment-provider",
                    title="Provider health normal",
                    summary=(
                        "The payment provider reports normal health during the incident window."
                    ),
                    raw_payload=health_output,
                    relevance=0.71,
                    correlation_id=data.incident.correlation_id,
                )
                self._add_evidence(provider_evidence)
                provider_evidence_ids.append(provider_evidence.id)
                self._link_tool_evidence(health_call, provider_evidence_ids)
            self.repository.add_hypothesis(
                Hypothesis(
                    incident_id=incident_id,
                    title="Payment provider outage",
                    description="The external provider may not be confirming payments.",
                    confidence=0.24 if provider_healthy else 0.5,
                    evidence_against=provider_evidence_ids,
                    verification_strategy="Compare provider health and transaction receipts.",
                    status="WEAKENED" if provider_healthy else "OPEN",
                )
            )
            await self._emit(
                incident_id,
                "hypothesis.created",
                (
                    "Provider outage hypothesis weakened"
                    if provider_healthy
                    else "Provider outage hypothesis remains open"
                ),
                (
                    "Provider health is normal; confidence reduced to low."
                    if provider_healthy
                    else "No trusted health signal was available to weaken this hypothesis."
                ),
            )

            logs_call, logs_output = await self._tool_event(
                incident_id,
                "query_application_logs",
                {
                    "service": "webhook-worker",
                    "query": "ValidationError paymentStatus",
                    "limit": 100,
                },
            )
            log_evidence_ids: list[str] = []
            if (
                isinstance(logs_output.get("matches"), int)
                and logs_output["matches"] > 0
                and isinstance(logs_output.get("pattern"), str)
                and "paymentStatus" in logs_output["pattern"]
                and isinstance(logs_output.get("first_seen"), str)
            ):
                for evidence in (
                    Evidence(
                        id="LOG-291",
                        incident_id=incident_id,
                        source_type=EvidenceType.LOG,
                        source_reference="log_00291",
                        title="Webhook schema validation failure",
                        summary=str(logs_output["pattern"]),
                        raw_payload=logs_output,
                        relevance=0.96,
                        correlation_id=data.incident.correlation_id,
                    ),
                    Evidence(
                        id="LOG-294",
                        incident_id=incident_id,
                        source_type=EvidenceType.LOG,
                        source_reference="log_00294",
                        title="Failure window correlation",
                        summary="Validation failures began inside the deployment window.",
                        raw_payload=logs_output,
                        relevance=0.94,
                        correlation_id=data.incident.correlation_id,
                    ),
                ):
                    self._add_evidence(evidence)
                    log_evidence_ids.append(evidence.id)
                self._link_tool_evidence(logs_call, log_evidence_ids)
                await self._emit(
                    incident_id,
                    "evidence.created",
                    "Error pattern identified",
                    "Schema validation errors began inside the deployment window.",
                    {"evidence_ids": log_evidence_ids},
                )

            deployment_call, deployment_output = await self._tool_event(
                incident_id,
                "get_recent_deployments",
                {"service": "webhook-worker", "limit": 5},
            )
            deployments = deployment_output.get("deployments")
            deployment = (
                next(
                    (
                        item
                        for item in deployments
                        if isinstance(item, dict)
                        and item.get("id") == "dep_184"
                        and item.get("service") == "webhook-worker"
                    ),
                    None,
                )
                if isinstance(deployments, list)
                else None
            )
            if deployment is not None:
                deployment_evidence = Evidence(
                    id="DEPLOY-184",
                    incident_id=incident_id,
                    source_type=EvidenceType.DEPLOYMENT,
                    source_reference="dep_184",
                    title="Webhook worker deployment dep_184",
                    summary=(
                        "Deployment dep_184 changed the parser four minutes before failures began."
                    ),
                    raw_payload=deployment,
                    relevance=0.95,
                    correlation_id=data.incident.correlation_id,
                )
                self._add_evidence(deployment_evidence)
                self._link_tool_evidence(deployment_call, [deployment_evidence.id])
            owned_evidence = {item.id for item in data.evidence}
            hypothesis_support = [
                evidence_id
                for evidence_id in ["LOG-291", "LOG-294", "DEPLOY-184"]
                if evidence_id in owned_evidence
            ]
            webhook_hypothesis = Hypothesis(
                incident_id=incident_id,
                title="Webhook schema regression",
                description=(
                    "Deployment dep_184 removed compatibility for the provider's "
                    "paymentStatus field."
                ),
                confidence=0.68 if len(hypothesis_support) == 3 else 0.25,
                evidence_for=hypothesis_support,
                verification_strategy="Run the legacy payload regression fixture.",
                status="TESTING" if len(hypothesis_support) == 3 else "UNCONFIRMED",
            )
            self.repository.add_hypothesis(webhook_hypothesis)
            await self._emit(
                incident_id,
                "hypothesis.created",
                "Webhook regression hypothesis",
                "Deployment and log timing support a parser regression.",
            )

            regression_call, regression_output = await self._tool_event(
                incident_id, "run_regression_test", {"fixture": "legacy-payment-approved-v2"}
            )
            regression_reproduced = (
                regression_output.get("result") == "FAILED"
                and regression_output.get("reproduced") is True
            )
            if regression_reproduced:
                regression_evidence = Evidence(
                    id="TEST-012",
                    incident_id=incident_id,
                    source_type=EvidenceType.TEST_RESULT,
                    source_reference="test_legacy_payment_status_alias",
                    title="Regression reproduced",
                    summary="The controlled legacy payload fails on dep_184 and passes on dep_183.",
                    raw_payload=regression_output,
                    relevance=0.99,
                    correlation_id=data.incident.correlation_id,
                )
                self._add_evidence(regression_evidence)
                self._link_tool_evidence(regression_call, [regression_evidence.id])
                webhook_hypothesis.evidence_for.append(regression_evidence.id)
            required_root_cause_evidence = {"LOG-291", "LOG-294", "DEPLOY-184", "TEST-012"}
            if required_root_cause_evidence.issubset(set(webhook_hypothesis.evidence_for)):
                webhook_hypothesis.confidence = 0.89
                webhook_hypothesis.status = "CONFIRMED"
            else:
                webhook_hypothesis.confidence = min(webhook_hypothesis.confidence, 0.25)
                webhook_hypothesis.status = "UNCONFIRMED"
            self.repository.save_hypothesis(webhook_hypothesis)
            owned_evidence = {item.id for item in data.evidence}
            self.repository.add_hypothesis(
                Hypothesis(
                    incident_id=incident_id,
                    title="Database persistence failure",
                    description="NovaPay may have failed to persist provider confirmations.",
                    confidence=0.18,
                    evidence_against=[
                        evidence_id
                        for evidence_id in ["TXN-901", "LOG-291", "TEST-012"]
                        if evidence_id in owned_evidence
                    ],
                    verification_strategy="Compare stored state with parser acceptance results.",
                    status="WEAKENED",
                )
            )
            self.repository.add_hypothesis(
                Hypothesis(
                    incident_id=incident_id,
                    title="Deployment configuration mismatch",
                    description="A runtime flag may have changed webhook compatibility.",
                    confidence=0.21,
                    evidence_for=["DEPLOY-184"] if "DEPLOY-184" in owned_evidence else [],
                    evidence_against=["TEST-012"] if "TEST-012" in owned_evidence else [],
                    verification_strategy="Compare dep_183 and dep_184 parser behavior.",
                    status="WEAKENED",
                )
            )
            await self._emit(
                incident_id,
                "hypothesis.updated",
                "Regression hypothesis confirmed",
                (
                    "Controlled test and source evidence support the regression."
                    if webhook_hypothesis.status == "CONFIRMED"
                    else "The regression remains unconfirmed because required evidence is missing."
                ),
                {"evidence_ids": webhook_hypothesis.evidence_for},
            )

            await self._transition(
                incident_id,
                IncidentState.EVIDENCE_COLLECTED,
                "Evidence collection complete",
                f"{len(data.evidence)} evidence records support or challenge the hypotheses.",
            )
            await self._transition(
                incident_id,
                IncidentState.DIAGNOSING,
                "Generating diagnosis",
                "Provider is producing a typed diagnosis from validated evidence.",
            )
            diagnosis = await self.provider.diagnose(data.incident.description, data.evidence)
            self.repository.set_diagnosis(incident_id, diagnosis)
            if diagnosis.outcome == DiagnosisOutcome.INSUFFICIENT_EVIDENCE:
                await self._transition(
                    incident_id,
                    IncidentState.ESCALATED,
                    "Evidence insufficient",
                    "No root cause was forced; operator investigation is required.",
                )
                run.status = "ESCALATED"
                run.completed_at = utc_now()
                self.repository.save_run(run)
                self._build_report(incident_id)
                return

            await self._transition(
                incident_id,
                IncidentState.DIAGNOSED,
                "Root cause identified",
                diagnosis.probable_root_cause,
            )

            rollback_args = {
                "service": "webhook-worker",
                "deployment_id": "dep_184",
                "target_deployment": "dep_183",
            }
            plan = RemediationPlan(
                incident_id=incident_id,
                summary=(
                    "Rollback dep_184, restore the compatible parser, then replay and "
                    "validate affected events."
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
            self.repository.set_remediation_plan(plan)
            await self._transition(
                incident_id,
                IncidentState.PLAN_PROPOSED,
                "Remediation plan proposed",
                plan.summary,
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
                incident_id,
                IncidentState.AWAITING_APPROVAL,
                "Human approval required",
                "Critical rollback is paused pending an operator decision.",
            )
            await self._emit(
                incident_id,
                "approval.requested",
                "Approval requested",
                approval.requested_action,
                {"approval_id": approval.id, "tool_call_id": approval.tool_call_id},
            )
            run.status = "WAITING_FOR_APPROVAL"
            run.tool_call_count = len(data.tool_calls)
            self.repository.save_run(run)
        except Exception as exc:
            run.status = "FAILED"
            run.error = type(exc).__name__
            run.completed_at = utc_now()
            self.repository.save_run(run)
            if data.incident.state not in {
                IncidentState.FAILED,
                IncidentState.RESOLVED,
                IncidentState.ESCALATED,
            }:
                try:
                    await self._transition(
                        incident_id,
                        IncidentState.FAILED,
                        "Investigation failed",
                        "The run stopped safely and requires operator review.",
                    )
                except Exception as transition_error:
                    run.error = f"{run.error};{type(transition_error).__name__}"
                    self.repository.save_run(run)

    async def approve(self, incident_id: str, approval_id: str, actor: str) -> Approval:
        data = self.repository.data(incident_id)
        approval = data.approval
        if approval is None or approval.id != approval_id:
            raise ApprovalInvalid("Approval does not belong to this incident")
        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalInvalid("Approval has already been decided")
        if approval.expires_at <= utc_now():
            approval.status = ApprovalStatus.EXPIRED
            self.repository.save_approval(approval)
            self._audit_approval(approval, actor, "approval.expired", "EXPIRED")
            await self._transition(
                incident_id,
                IncidentState.ESCALATED,
                "Approval expired",
                "The critical action was not executed; operator review is required.",
            )
            if data.run:
                data.run.status = "ESCALATED"
                data.run.completed_at = utc_now()
                self.repository.save_run(data.run)
            self._build_report(incident_id)
            raise ApprovalInvalid("Approval has expired")
        approval.status = ApprovalStatus.APPROVED
        approval.approved_by = actor
        approval.approved_at = utc_now()
        self.repository.save_approval(approval)
        self._audit_approval(approval, actor, "approval.approved", "APPROVED")
        await self._emit(
            incident_id,
            "approval.approved",
            "Rollback approved",
            f"{actor} approved the exact requested action.",
            {"approval_id": approval.id, "tool_call_id": approval.tool_call_id},
        )
        await self._transition(
            incident_id,
            IncidentState.EXECUTING,
            "Executing approved remediation",
            "The argument-bound rollback is now executing.",
        )
        try:
            call, _ = self.tools.execute_approved(approval)
        except ToolExecutionFailed:
            await self._transition(
                incident_id,
                IncidentState.FAILED,
                "Remediation failed safely",
                "The approval was consumed, no retry was forced, and operator review is required.",
            )
            if data.run:
                data.run.status = "FAILED"
                data.run.error = "ToolExecutionFailed"
                data.run.completed_at = utc_now()
                self.repository.save_run(data.run)
            self._build_report(incident_id)
            raise
        if data.remediation_plan:
            data.remediation_plan.steps[0].status = ExecutionStatus.SIMULATED
            self.repository.set_remediation_plan(data.remediation_plan)
        await self._emit(
            incident_id,
            "tool.completed",
            "Rollback completed",
            "webhook-worker now runs dep_183.",
            {"tool_call_id": call.id, "approval_id": approval.id},
        )
        await self._transition(
            incident_id,
            IncidentState.VALIDATING,
            "Validating outcome",
            "Regression and transaction recovery checks are running.",
        )
        _, validation_output = await self._tool_event(
            incident_id, "validate_remediation", {"incident_id": incident_id}
        )
        passed = bool(
            validation_output.get("tests_failed") == 0
            and validation_output.get("pending_transactions_recovered") == 37
        )
        evidence = Evidence(
            id="TEST-POST-ROLLBACK",
            incident_id=incident_id,
            source_type=EvidenceType.TEST_RESULT,
            source_reference="validation_run_13",
            title=(
                "Post-remediation validation passed"
                if passed
                else "Post-remediation validation failed"
            ),
            summary=(
                "12 parser tests passed and all 37 pending transactions recovered."
                if passed
                else "The remediation executed, but recovery validation still reports failures."
            ),
            raw_payload=validation_output,
            relevance=1.0,
            correlation_id=data.incident.correlation_id,
        )
        self._add_evidence(evidence)
        validation = ValidationResult(
            incident_id=incident_id,
            passed=passed,
            summary=evidence.summary,
            evidence_ids=[evidence.id],
            checks_passed=int(validation_output.get("tests_passed", 0)),
            checks_failed=int(validation_output.get("tests_failed", 0)),
            recovered_transactions=int(
                validation_output.get("pending_transactions_recovered", 0)
            ),
        )
        self.repository.set_validation(validation)
        if data.remediation_plan:
            data.remediation_plan.steps[1].status = ExecutionStatus.SIMULATED
            self.repository.set_remediation_plan(data.remediation_plan)
        await self._emit(
            incident_id,
            "validation.completed" if passed else "validation.failed",
            "Validation passed" if passed else "Validation failed",
            evidence.summary,
            {
                "evidence_ids": [evidence.id],
                "approval_id": approval.id,
                "tool_call_id": call.id,
            },
        )
        self._audit(
            incident_id,
            actor_type="SYSTEM",
            actor_id="incident-coordinator",
            action="validation.completed" if passed else "validation.failed",
            resource_type="incident",
            resource_id=incident_id,
            result="PASSED" if passed else "FAILED",
            tool_call_id=call.id,
            approval_id=approval.id,
            metadata={"evidence_id": evidence.id},
        )
        if passed:
            await self._transition(
                incident_id,
                IncidentState.RESOLVED,
                "Incident resolved",
                "Rollback succeeded and the recovery was verified.",
            )
        else:
            await self._transition(
                incident_id,
                IncidentState.ESCALATED,
                "Incident remains unresolved",
                "Remediation executed, but validation failed; operator escalation is required.",
            )
        if data.run:
            data.run.status = "COMPLETED" if passed else "ESCALATED"
            data.run.completed_at = utc_now()
            data.run.tool_call_count = len(data.tool_calls)
            self.repository.save_run(data.run)
        self._build_report(incident_id)
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
        self.repository.save_approval(approval)
        self._audit_approval(approval, actor, "approval.rejected", "REJECTED")
        await self._emit(
            incident_id,
            "approval.rejected",
            "Rollback rejected",
            "No critical action executed.",
            {"approval_id": approval.id, "tool_call_id": approval.tool_call_id},
        )
        await self._transition(
            incident_id,
            IncidentState.ESCALATED,
            "Incident escalated",
            "Operator rejected the proposed rollback.",
        )
        if data.run:
            data.run.status = "ESCALATED"
            data.run.completed_at = utc_now()
            self.repository.save_run(data.run)
        self._build_report(incident_id)
        return approval

    def _audit_approval(
        self, approval: Approval, actor: str, action: str, result: str
    ) -> None:
        self._audit(
            approval.incident_id,
            actor_type="USER",
            actor_id=actor,
            action=action,
            resource_type="approval",
            resource_id=approval.id,
            result=result,
            risk_level=ToolRiskLevel.CRITICAL_WRITE,
            tool_call_id=approval.tool_call_id,
            approval_id=approval.id,
        )

    async def _tool_event(
        self, incident_id: str, name: str, arguments: dict[str, object]
    ) -> tuple[ToolCall, dict[str, Any]]:
        await self._emit(
            incident_id,
            "tool.started",
            f"Running {name}",
            "Validated tool call started.",
            {"tool": name},
        )
        await self._pause()
        call, output = self.tools.execute_safe(incident_id, name, arguments)
        await self._emit(
            incident_id,
            "tool.completed",
            f"{name} completed",
            call.output_summary or "Structured result returned.",
            {"tool_call_id": call.id, "duration_ms": call.duration_ms},
        )
        return call, output

    def _add_evidence(self, evidence: Evidence) -> None:
        self.repository.add_evidence(evidence)

    def _link_tool_evidence(self, call: ToolCall, evidence_ids: list[str]) -> None:
        call.evidence_ids = list(dict.fromkeys([*call.evidence_ids, *evidence_ids]))
        self.repository.save_tool_call(call)

    async def _transition(
        self, incident_id: str, state: IncidentState, title: str, summary: str
    ) -> None:
        incident = self.repository.data(incident_id).incident
        validate_transition(incident.state, state)
        incident.state = state
        incident.updated_at = utc_now()
        self.repository.save_incident(incident)
        self._audit(
            incident_id,
            actor_type="SYSTEM",
            actor_id="incident-coordinator",
            action="incident.state_transition",
            resource_type="incident",
            resource_id=incident_id,
            result=state,
            metadata={"state": state},
        )
        await self._emit(
            incident_id, "incident.state_changed", title, summary, {"state": state}
        )
        await self._pause()

    async def _emit(
        self,
        incident_id: str,
        event_type: str,
        title: str,
        summary: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        data = self.repository.data(incident_id)
        event_metadata = metadata or {}
        await self.repository.publish(
            IncidentEvent(
                incident_id=incident_id,
                type=event_type,
                title=title,
                summary=summary,
                metadata=event_metadata,
                correlation_id=data.incident.correlation_id,
                agent_run_id=data.run.id if data.run else None,
                tool_call_id=(
                    str(event_metadata["tool_call_id"])
                    if event_metadata.get("tool_call_id")
                    else None
                ),
                approval_id=(
                    str(event_metadata["approval_id"])
                    if event_metadata.get("approval_id")
                    else None
                ),
            )
        )

    def _audit(
        self,
        incident_id: str,
        *,
        actor_type: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        result: str,
        risk_level: ToolRiskLevel | None = None,
        tool_call_id: str | None = None,
        approval_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        data = self.repository.data(incident_id)
        self.repository.append_audit(
            AuditRecord(
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                risk_level=risk_level,
                metadata=metadata or {},
                correlation_id=data.incident.correlation_id,
                incident_id=incident_id,
                agent_run_id=data.run.id if data.run else None,
                tool_call_id=tool_call_id,
                approval_id=approval_id,
            )
        )

    def _build_report(self, incident_id: str) -> IncidentReport:
        data = self.repository.data(incident_id)
        report = IncidentReport(
            incident_id=incident_id,
            correlation_id=data.incident.correlation_id,
            summary=(
                "Evidence-backed investigation completed with validated recovery."
                if data.incident.state == IncidentState.RESOLVED
                else "Investigation ended safely without claiming an unverified resolution."
            ),
            timeline_event_ids=[event.id for event in data.events],
            evidence_ids=[evidence.id for evidence in data.evidence],
            hypothesis_ids=[hypothesis.id for hypothesis in data.hypotheses],
            diagnosis=data.diagnosis,
            remediation_plan_id=data.remediation_plan.id if data.remediation_plan else None,
            approval_id=data.approval.id if data.approval else None,
            validation=data.validation,
            final_status=data.incident.state,
        )
        self.repository.set_report(report)
        return report

    async def _pause(self) -> None:
        if self.delay:
            await asyncio.sleep(self.delay)


coordinator = IncidentCoordinator()
