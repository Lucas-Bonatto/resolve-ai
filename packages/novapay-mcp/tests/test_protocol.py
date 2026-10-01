import asyncio
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_stdio_protocol_lists_tools_and_keeps_critical_action_proposal_only() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "novapay_mcp.server"],
    )

    async with (
        asyncio.timeout(15),
        stdio_client(parameters) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        names = {tool.name for tool in tools.tools}
        result = await session.call_tool(
            "request_service_rollback",
            {
                "service": "webhook-worker",
                "deployment_id": "dep_184",
                "target_deployment": "dep_183",
            },
        )

    assert len(names) == 14
    assert {"search_transactions", "request_service_rollback"} <= names
    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["execution"] == "SIMULATED"
    assert result.structured_content["data"]["decision"] == "REQUIRE_APPROVAL"
    assert result.structured_content["data"]["executed"] is False
