from novapay_mcp.server import (
    get_service_health,
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


def test_rollback_tool_only_requests_approval() -> None:
    result = request_service_rollback("webhook-worker", "dep_184", "dep_183")
    assert result["data"]["decision"] == "REQUIRE_APPROVAL"
    assert result["data"]["executed"] is False
