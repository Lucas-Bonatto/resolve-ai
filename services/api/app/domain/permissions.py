from __future__ import annotations

from datetime import datetime
from typing import Any

from .enums import ApprovalStatus, PolicyDecision, ToolRiskLevel
from .errors import ApprovalInvalid
from .models import Approval, arguments_hash, utc_now


class PermissionEngine:
    """Fail-closed policy boundary independent of model instructions."""

    def evaluate(self, risk_level: ToolRiskLevel) -> PolicyDecision:
        if risk_level in {ToolRiskLevel.READ, ToolRiskLevel.SAFE_WRITE}:
            return PolicyDecision.ALLOW
        if risk_level == ToolRiskLevel.CRITICAL_WRITE:
            return PolicyDecision.REQUIRE_APPROVAL
        return PolicyDecision.DENY

    def authorize_critical(
        self,
        *,
        approval: Approval | None,
        incident_id: str,
        tool_call_id: str,
        arguments: dict[str, Any],
        now: datetime | None = None,
    ) -> Approval:
        if approval is None:
            raise ApprovalInvalid("A valid human approval is required")
        current_time = now or utc_now()
        if approval.status != ApprovalStatus.APPROVED:
            raise ApprovalInvalid(f"Approval status is {approval.status}")
        if approval.expires_at <= current_time:
            approval.status = ApprovalStatus.EXPIRED
            raise ApprovalInvalid("Approval has expired")
        if approval.incident_id != incident_id:
            raise ApprovalInvalid("Approval belongs to another incident")
        if approval.tool_call_id != tool_call_id:
            raise ApprovalInvalid("Approval belongs to another tool call")
        if approval.arguments_hash != arguments_hash(arguments):
            raise ApprovalInvalid("Tool arguments changed after approval")
        return approval
