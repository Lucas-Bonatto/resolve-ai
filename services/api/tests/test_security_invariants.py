from fastapi.routing import APIRoute

from app.main import app
from app.tools.gateway import TOOL_CATALOG


def test_audit_api_is_read_only() -> None:
    audit_routes = [
        route for route in app.routes if isinstance(route, APIRoute) and route.path == "/api/audit"
    ]
    assert len(audit_routes) == 1
    assert audit_routes[0].methods == {"GET"}


def test_agents_have_no_audit_mutation_tool() -> None:
    assert all(
        not ({"audit", "delete", "rewrite", "update"} <= set(name.lower().split("_")))
        for name in TOOL_CATALOG
    )
