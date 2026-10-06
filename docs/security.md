# Security model

## Assets and trust boundaries

The protected assets are tool credentials, incident data, approval authority, audit integrity, and the truthfulness of execution status. Inputs from users, models, MCP tools, logs, tickets, and knowledge documents are untrusted.

The central boundary is simple: the model proposes, the application authorizes, and the operator approves critical writes.

## Threats and controls

| Threat | Control | Verification |
| --- | --- | --- |
| Prompt injection in logs or retrieved text | Data is delimited; permission logic cannot be changed by prompt text | Adversarial gateway tests and five benchmark cases |
| Critical action without a recorded decision | Fail-closed risk policy and exact-action approval | Unit, red-team, and browser rejection tests |
| Approval replay or argument substitution | Exact incident/action/tool/tool-call binding, canonical argument hash, expiration, atomic PostgreSQL consumption | Permission and PostgreSQL concurrency tests |
| Fabricated evidence | Diagnosis evidence IDs are checked against incident-owned records | Orchestrator tests |
| Cross-incident evidence/approval reuse | Repository ownership checks and exact incident binding | Negative evidence and approval tests |
| Arbitrary SQL, shell, or network behavior | No general-purpose execution tool; all tools have bounded schemas | Tool catalog review |
| Secret leakage | Pydantic secret type, ignored local env files, no key in client bundle | Git ignore and review checks |
| Misleading demo claims | `SIMULATED`, `EXECUTED`, and `NOT_EXECUTED` labels | UI tests and documentation |
| Unauthenticated public mutation or shared-state interference | Fail-closed `public_showcase` profile blocks every POST route and seeds a read-only snapshot | Configuration, API denial, and unchanged-state regression tests |
| Basic public request flooding | Bounded in-process per-client request window without trusting forwarded identity | Deterministic limiter tests; hosting-edge controls remain required |

## Tool risk classes

- `READ`: bounded retrieval with no side effect; automatic.
- `SAFE_WRITE`: reversible operation inside an allowlisted simulator; automatic and audited.
- `CRITICAL_WRITE`: material operational change; requires exact-action human approval.
- `FORBIDDEN`: unsupported or unbounded capability; denied.

The application recalculates risk on the server. A tool or model cannot downgrade its own risk class. The local API does not authenticate the person pressing Approve; `approved_by` is demo attribution, not a verified identity claim.

The testable hard properties and their current verification are cataloged in [security invariants](security-invariants.md).

## Production gaps

The `public_showcase` profile may be hosted only as a read-only portfolio surface: it forces the deterministic provider, rejects mutation routes, uses fictional in-memory state, and exposes no credential. It is not an internet-facing control plane. Interactive or production adoption still requires authentication, tenant-aware authorization, protected demo/reset/evaluation endpoints, encrypted secret storage, network egress rules, hosting-edge rate and connection limits, durable cross-process event delivery, external-side-effect idempotency, tamper-evident audit export, retention controls, production telemetry export, and incident-response ownership.
