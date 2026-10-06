from __future__ import annotations

from typing import Any


class NovaPaySimulator:
    """Deterministic, fictional NovaPay environment used by Demo Mode."""

    scenarios = [
        {
            "id": "payment-webhook-regression",
            "title": "Payment Webhook Regression",
            "severity": "SEV-1",
        },
        {"id": "duplicate-charges", "title": "Duplicate Charges", "severity": "SEV-1"},
        {"id": "api-latency", "title": "API Latency Spike", "severity": "SEV-2"},
        {
            "id": "database-exhaustion",
            "title": "Database Connection Exhaustion",
            "severity": "SEV-1",
        },
        {"id": "auth-failure", "title": "Authentication Failure Spike", "severity": "SEV-2"},
        {"id": "provider-timeout", "title": "Payment Provider Timeout", "severity": "SEV-2"},
        {"id": "invalid-config", "title": "Invalid Deployment Configuration", "severity": "SEV-2"},
        {"id": "queue-backlog", "title": "Queue Backlog", "severity": "SEV-2"},
        {
            "id": "status-sync",
            "title": "Customer Status Synchronization Failure",
            "severity": "SEV-2",
        },
        {
            "id": "kb-injection",
            "title": "Knowledge Base Prompt Injection Attempt",
            "severity": "SEV-3",
        },
    ]

    def __init__(self, *, validation_should_fail: bool = False) -> None:
        self.deployment_active = "dep_184"
        self.flagship_injected = False
        self.validation_should_fail = validation_should_fail

    def reset(self) -> None:
        self.deployment_active = "dep_184"
        self.flagship_injected = False

    def inject(self, scenario_id: str) -> dict[str, Any]:
        if scenario_id != "payment-webhook-regression":
            raise ValueError("This polished demo build currently executes the flagship scenario")
        self.flagship_injected = True
        return {"scenario_id": scenario_id, "status": "SIMULATED", "affected_transactions": 37}

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "search_transactions":
            return {
                "count": 37,
                "sample_ids": ["txn_901", "txn_912", "txn_933"],
                "provider_status": "approved",
                "novapay_status": "pending",
            }
        if tool_name == "get_service_health":
            service = arguments["service"]
            if service == "payment-provider":
                return {"service": service, "status": "healthy", "availability": 0.9998}
            return {"service": service, "status": "degraded", "error_rate": 0.183}
        if tool_name == "query_application_logs":
            return {
                "matches": 142,
                "pattern": "ValidationError: field paymentStatus not permitted",
                "first_seen": "2026-09-30T12:45:04Z",
            }
        if tool_name == "get_recent_deployments":
            return {
                "deployments": [
                    {
                        "id": "dep_184",
                        "service": "webhook-worker",
                        "deployed_at": "2026-09-30T12:41:00Z",
                        "commit": "7be91af",
                    },
                    {
                        "id": "dep_183",
                        "service": "webhook-worker",
                        "deployed_at": "2026-09-28T09:20:00Z",
                        "commit": "ab3289d",
                    },
                ]
            }
        if tool_name == "search_knowledge_base":
            return {
                "documents": [
                    {"id": "kb_webhooks_01", "title": "Payment webhook contract", "trusted": False},
                    {
                        "id": "kb_rollback_02",
                        "title": "Webhook worker rollback procedure",
                        "trusted": False,
                    },
                ]
            }
        if tool_name == "run_regression_test":
            return {
                "test": "test_legacy_payment_status_alias",
                "result": "FAILED",
                "reproduced": True,
            }
        if tool_name == "request_service_rollback":
            self.deployment_active = arguments["target_deployment"]
            return {
                "service": arguments["service"],
                "active_deployment": self.deployment_active,
                "rolled_back": True,
            }
        if tool_name == "validate_remediation":
            if self.validation_should_fail:
                return {
                    "tests_passed": 10,
                    "tests_failed": 2,
                    "pending_transactions_recovered": 21,
                }
            return {"tests_passed": 12, "tests_failed": 0, "pending_transactions_recovered": 37}
        if tool_name == "create_incident_note":
            return {"created": True, "note_id": "note_demo_01"}
        raise ValueError(f"Unknown simulator tool: {tool_name}")


simulator = NovaPaySimulator()
