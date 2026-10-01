# NovaPay MCP server

`packages/novapay-mcp` is a standalone Python MCP v2 server over the controlled NovaPay simulator contract. It exposes typed, bounded operations for transactions, metrics, logs, deployments, tests, incidents, and remediation proposals.

## Run locally

```powershell
.\.venv\Scripts\python.exe -m novapay_mcp.server
```

The package is installed in editable mode by the repository setup command. Tool schemas reject unknown fields and constrain result sizes. Every structured result contains a server-generated `correlation_id`, evidence IDs, an execution label, and a matching sanitized audit envelope. Critical functions return `REQUIRE_APPROVAL` with `executed: false`; only the ResolveAI application gateway can consume an application approval.

## Design rules

- Stable fictional identifiers make traces and evaluation cases repeatable.
- Tool descriptions state risk and simulation boundaries.
- Results are structured objects, not prose instructions.
- MCP availability is not authorization; critical calls remain proposal-only.
- The server exposes no arbitrary filesystem, shell, SQL, or network tool.
- Adding a write tool requires a risk classification, audit behavior, and approval tests.
