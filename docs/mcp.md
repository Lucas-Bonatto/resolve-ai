# NovaPay MCP server

`packages/novapay-mcp` is a standalone Python MCP v2 server over the controlled NovaPay simulator contract. It exposes typed, bounded operations for transactions, metrics, logs, deployments, tests, incidents, and remediation proposals.

## Run locally

```powershell
.\.venv\Scripts\python.exe -m novapay_mcp.server
```

The package is installed in editable mode by the repository setup command. Tool schemas reject unknown fields and constrain result sizes. Critical behavior remains behind the ResolveAI application permission and approval gateway; connecting directly to this fictional server is for protocol inspection, not an authorization shortcut.

## Design rules

- Stable fictional identifiers make traces and evaluation cases repeatable.
- Tool descriptions state risk and simulation boundaries.
- Results are structured objects, not prose instructions.
- The server exposes no arbitrary filesystem, shell, SQL, or network tool.
- Adding a write tool requires a risk classification, audit behavior, and approval tests.
