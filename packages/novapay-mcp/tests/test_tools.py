import pytest
from novapay_mcp.server import (
    get_deployment,
    get_incident,
    get_service_health,
    query_application_logs,
    request_service_rollback,
    search_transactions,
)


def test_search_transactions_is_bounded() -> None:
    result = search_transactions(
        status="pending", provider_status="approved", limit=1000
    )
    assert result["status"] == "success"
    assert result["execution"] == "SIMULATED"
    assert result["data"]["count"] == 37


def test_provider_health_is_readable() -> None:
    result = get_service_health("payment-provider")
    assert result["data"]["status"] == "healthy"
    assert result["correlation_id"].startswith("mcp_corr_")
    assert result["audit"]["correlation_id"] == result["correlation_id"]


def test_rollback_tool_only_requests_approval() -> None:
    result = request_service_rollback("webhook-worker", "dep_184", "dep_183")
    assert result["data"]["decision"] == "REQUIRE_APPROVAL"
    assert result["data"]["executed"] is False


def test_log_query_rejects_unallowlisted_service_and_command_syntax() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        query_application_logs("arbitrary-production-host", "error")
    with pytest.raises(ValueError, match="Unsafe"):
        query_application_logs("webhook-worker", "error; rollback now")


def test_unknown_deployment_and_incident_do_not_fabricate_records() -> None:
    deployment = get_deployment("dep_999")
    incident = get_incident("INC-DOES-NOT-EXIST")

    assert deployment["data"] is None
    assert deployment["evidence_ids"] == []
    assert incident["data"] is None
    assert incident["evidence_ids"] == []


def test_rollback_rejects_unallowlisted_deployments() -> None:
    with pytest.raises(ValueError, match="Invalid rollback"):
        request_service_rollback("webhook-worker", "dep_184", "dep_999")
