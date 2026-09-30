from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.application.simulator import NovaPaySimulator
from app.application.store import InMemoryRepository
from app.config import settings
from app.domain.enums import ApprovalStatus, ExecutionStatus, PolicyDecision, ToolRiskLevel
from app.domain.errors import ApprovalInvalid, ToolExecutionFailed
from app.domain.models import Approval, AuditRecord, ToolCall, arguments_hash
from app.domain.permissions import PermissionEngine


@dataclass(frozen=True)
class ToolSpec:
    name: str
    risk_level: ToolRiskLevel
    description: str


TOOL_CATALOG = {
    spec.name: spec
    for spec in [
        ToolSpec(
            "search_transactions", ToolRiskLevel.READ, "Search bounded fictional transactions"
        ),
        ToolSpec(
            "get_service_health", ToolRiskLevel.READ, "Read one allowlisted service health summary"
        ),
        ToolSpec("query_application_logs", ToolRiskLevel.READ, "Search sanitized application logs"),
        ToolSpec("get_recent_deployments", ToolRiskLevel.READ, "List recent service deployments"),
        ToolSpec(
            "search_knowledge_base", ToolRiskLevel.READ, "Search untrusted internal documents"
        ),
        ToolSpec("run_regression_test", ToolRiskLevel.READ, "Run a controlled fixture test"),
        ToolSpec("validate_remediation", ToolRiskLevel.READ, "Validate the simulated remediation"),
        ToolSpec("create_incident_note", ToolRiskLevel.SAFE_WRITE, "Add an audited internal note"),
        ToolSpec(
            "request_service_rollback",
            ToolRiskLevel.CRITICAL_WRITE,
            "Rollback an allowlisted service",
        ),
    ]
}

ALLOWED_SERVICES = {
    "payment-api",
    "transaction-service",
    "customer-service",
    "webhook-worker",
    "notification-service",
    "auth-service",
    "incident-service",
    "payment-provider",
}


class ToolGateway:
    def __init__(self, repository: InMemoryRepository, simulator: NovaPaySimulator) -> None:
        self.repository = repository
        self.simulator = simulator
        self.permissions = PermissionEngine()

    def _audit_blocked(
        self,
        incident_id: str,
        name: str,
        arguments: dict[str, Any],
        reason: str,
        risk_level: ToolRiskLevel | None = None,
    ) -> None:
        self.repository.audit.append(
            AuditRecord(
                actor_type="TOOL",
                actor_id=name,
                action="tool.blocked",
                resource_type="incident",
                resource_id=incident_id,
                result=ExecutionStatus.BLOCKED,
                risk_level=risk_level,
                metadata={"reason": reason, "arguments_hash": arguments_hash(arguments)},
            )
        )

    def _validate(self, incident_id: str, name: str, arguments: dict[str, Any]) -> ToolSpec:
        try:
            spec = TOOL_CATALOG[name]
        except KeyError as exc:
            self._audit_blocked(incident_id, name, arguments, "unknown_tool")
            raise ToolExecutionFailed(f"Unknown tool: {name}") from exc
        if int(arguments.get("limit", 20)) > 100:
            self._audit_blocked(
                incident_id, name, arguments, "result_limit_exceeded", spec.risk_level
            )
            raise ToolExecutionFailed("Tool result limit cannot exceed 100")
        service = arguments.get("service")
        if service is not None and service not in ALLOWED_SERVICES:
            self._audit_blocked(
                incident_id, name, arguments, "service_not_allowlisted", spec.risk_level
            )
            raise ToolExecutionFailed("Service is outside the NovaPay allowlist")
        if any(
            token in str(value) for value in arguments.values() for token in ("..", ";", "&&", "|")
        ):
            self._audit_blocked(
                incident_id, name, arguments, "dangerous_arguments", spec.risk_level
            )
            raise ToolExecutionFailed("Potentially dangerous tool arguments were rejected")
        return spec

    def _enforce_tool_budget(
        self, incident_id: str, name: str, arguments: dict[str, Any], risk_level: ToolRiskLevel
    ) -> None:
        if len(self.repository.data(incident_id).tool_calls) >= settings.max_tool_calls_per_run:
            self._audit_blocked(
                incident_id, name, arguments, "tool_call_budget_exceeded", risk_level
            )
            raise ToolExecutionFailed("Maximum tool calls per run exceeded")

    def execute_safe(
        self, incident_id: str, name: str, arguments: dict[str, Any]
    ) -> tuple[ToolCall, dict[str, Any]]:
        spec = self._validate(incident_id, name, arguments)
        if self.permissions.evaluate(spec.risk_level) != PolicyDecision.ALLOW:
            self._audit_blocked(
                incident_id, name, arguments, "approval_gateway_required", spec.risk_level
            )
            raise ApprovalInvalid("Critical tools must use the approval gateway")
        self._enforce_tool_budget(incident_id, name, arguments, spec.risk_level)
        call = ToolCall(
            incident_id=incident_id, tool_name=name, arguments=arguments, risk_level=spec.risk_level
        )
        self.repository.data(incident_id).tool_calls.append(call)
        started = perf_counter()
        output = self.simulator.execute(name, arguments)
        call.duration_ms = max(1, int((perf_counter() - started) * 1000))
        call.status = ExecutionStatus.SIMULATED
        call.output_summary = self._summarize(output)
        self.repository.audit.append(
            AuditRecord(
                actor_type="TOOL",
                actor_id=name,
                action="tool.execute",
                resource_type="incident",
                resource_id=incident_id,
                result=call.status,
                risk_level=spec.risk_level,
                metadata={"tool_call_id": call.id, "arguments_hash": arguments_hash(arguments)},
            )
        )
        return call, output

    def propose_critical(
        self,
        incident_id: str,
        name: str,
        arguments: dict[str, Any],
        *,
        reason: str,
        evidence_ids: list[str],
        impact: str,
    ) -> tuple[ToolCall, Approval]:
        spec = self._validate(incident_id, name, arguments)
        if self.permissions.evaluate(spec.risk_level) != PolicyDecision.REQUIRE_APPROVAL:
            self._audit_blocked(
                incident_id, name, arguments, "critical_tool_required", spec.risk_level
            )
            raise ToolExecutionFailed("Only critical tools create approval requests")
        self._enforce_tool_budget(incident_id, name, arguments, spec.risk_level)
        call = ToolCall(
            incident_id=incident_id, tool_name=name, arguments=arguments, risk_level=spec.risk_level
        )
        approval = Approval(
            incident_id=incident_id,
            tool_call_id=call.id,
            requested_action=f"Rollback {arguments['service']} to {arguments['target_deployment']}",
            arguments_hash=arguments_hash(arguments),
            reason=reason,
            evidence_ids=evidence_ids,
            potential_impact=impact,
        )
        data = self.repository.data(incident_id)
        data.tool_calls.append(call)
        data.approval = approval
        self.repository.audit.append(
            AuditRecord(
                actor_type="AGENT",
                actor_id="incident-coordinator",
                action="approval.requested",
                resource_type="tool_call",
                resource_id=call.id,
                result="PENDING",
                risk_level=spec.risk_level,
                metadata={"approval_id": approval.id, "arguments_hash": approval.arguments_hash},
            )
        )
        return call, approval

    def execute_approved(self, approval: Approval) -> tuple[ToolCall, dict[str, Any]]:
        data = self.repository.data(approval.incident_id)
        call = next((item for item in data.tool_calls if item.id == approval.tool_call_id), None)
        if call is None:
            self._audit_blocked(
                approval.incident_id,
                "unknown-approved-tool",
                {},
                "approved_tool_call_missing",
                ToolRiskLevel.CRITICAL_WRITE,
            )
            raise ApprovalInvalid("Approved tool call no longer exists")
        try:
            self.permissions.authorize_critical(
                approval=approval,
                incident_id=call.incident_id,
                tool_call_id=call.id,
                arguments=call.arguments,
            )
        except ApprovalInvalid:
            self._audit_blocked(
                call.incident_id,
                call.tool_name,
                call.arguments,
                "critical_authorization_failed",
                call.risk_level,
            )
            raise
        # Consume before the side effect so a failure cannot make the approval replayable.
        approval.status = ApprovalStatus.CONSUMED
        started = perf_counter()
        output = self.simulator.execute(call.tool_name, call.arguments)
        call.duration_ms = max(1, int((perf_counter() - started) * 1000))
        call.status = ExecutionStatus.SIMULATED
        call.output_summary = self._summarize(output)
        self.repository.audit.append(
            AuditRecord(
                actor_type="TOOL",
                actor_id=call.tool_name,
                action="tool.execute.approved",
                resource_type="incident",
                resource_id=call.incident_id,
                result=call.status,
                risk_level=call.risk_level,
                metadata={"approval_id": approval.id, "tool_call_id": call.id},
            )
        )
        return call, output

    @staticmethod
    def _summarize(output: dict[str, Any]) -> str:
        keys = ", ".join(sorted(output)[:4])
        return f"Structured result returned ({keys})"
