# Security invariants

These are hard properties, not prompt suggestions. A change that violates one must be redesigned. Test names refer to the current suite under `services/api/tests`, `packages/novapay-mcp/tests`, and `apps/web/tests`.

## Invariant 1 — No critical execution without human approval

**Reason.** Operational side effects must not be authorized by a model, UI, or demo shortcut.

**Enforcement.** `ToolRiskLevel.CRITICAL_WRITE` maps to `REQUIRE_APPROVAL`. `execute_safe` rejects it, and only `execute_approved` reaches the simulator after `PermissionEngine.authorize_critical` succeeds.

**Verification.** `test_critical_tool_cannot_execute_without_approval`, `test_rejected_approval_executes_no_critical_tool`, and the Playwright rejection journey.

## Invariant 2 — Approval is exact, scoped, expiring, and single-use

**Reason.** A legitimate decision must not authorize changed parameters, another incident/action, an expired request, or replay.

**Enforcement.** Approval binds incident ID, requested action, tool, tool-call ID, canonical arguments hash, status, expiry, and approving user. The gateway consumes approval before attempting the side effect. PostgreSQL uses an atomic `UPDATE ... WHERE status = APPROVED` with the exact bindings and expiry predicate, so only one competing worker can consume it.

**Verification.** The permission suite covers missing, rejected, expired, consumed, action/tool/tool-call/incident mismatch, modified arguments, replay, and concurrent consumption. `test_postgres_consumes_one_approval_across_repository_instances` exercises the database boundary when `TEST_DATABASE_URL` exists.

## Invariant 3 — Retrieved content cannot change authorization policy

**Reason.** Logs, tickets, customer messages, knowledge articles, code comments, and tool results may contain prompt injection.

**Enforcement.** Retrieved text is untrusted evidence. Permission decisions accept fixed risk and application state, never text or model instructions. Critical MCP functions remain proposal-only.

**Verification.** `test_tool_output_cannot_grant_approval_or_trigger_a_critical_action` and `test_log_injection_remains_untrusted_data` exercise hostile text through the real gateway. Benchmark cases `eval_security_031`–`035` cover the deterministic evaluation contract.

## Invariant 4 — Agent evidence references must exist on the incident

**Reason.** A plausible diagnosis is not auditable if its citations are invented or cross incident boundaries.

**Enforcement.** Repository writes validate supporting and contradicting hypothesis evidence, supported diagnoses, approvals, validation, and reports against the incident-owned evidence set. `INSUFFICIENT_EVIDENCE` is an explicit typed outcome.

**Verification.** `test_diagnosis_rejects_unknown_and_cross_incident_evidence`, `test_hypothesis_rejects_cross_incident_evidence`, and `test_unknown_agent_evidence_reference_fails_the_run` cover nonexistent, cross-incident, and provider-hallucinated IDs.

## Invariant 5 — Agents cannot execute arbitrary shell commands

**Reason.** General command execution would collapse filesystem, network, credential, and process isolation.

**Enforcement.** Neither `TOOL_CATALOG` nor the MCP server contains a shell/process tool. Code work is limited to controlled repository fixtures; the runtime agent receives no execution tool.

**Verification.** `test_dangerous_general_purpose_tools_are_not_exposed`; benchmark cases `eval_webhook_007`, `eval_db_025`, and `eval_security_034` list `execute_shell` as forbidden.

## Invariant 6 — Agents cannot execute raw generated SQL

**Reason.** Model-generated SQL could bypass tenancy, validation, least privilege, and audit rules.

**Enforcement.** No SQL tool exists. Application services use repository/domain interfaces; SQLAlchemy schema code is infrastructure owned and migrations are reviewed code.

**Verification.** `test_dangerous_general_purpose_tools_are_not_exposed`; `eval_webhook_008` and `eval_db_022` forbid `raw_sql`.

## Invariant 7 — Live GitHub writes are absent by default and future writes are allowlisted

**Reason.** Repository mutation can affect unrelated code, supply chains, and releases.

**Enforcement.** The current product has no GitHub adapter or GitHub tool; `.env.example` keeps integration disabled/mock. Any future adapter must require explicit opt-in, repository allowlist, least privilege, audit, and approval for critical writes.

**Verification.** `test_dangerous_general_purpose_tools_are_not_exposed` proves the application catalog exposes no GitHub capability. A future adapter must replace this absence proof with allowlist and denial tests before activation.

## Invariant 8 — Demo Mode never claims simulation is real execution

**Reason.** Recruiters, operators, and contributors must be able to distinguish product behavior from external side effects.

**Enforcement.** Domain/UI contracts use `SIMULATED`, `EXECUTED`, `NOT_EXECUTED`, and `BLOCKED`. The NovaPay simulator and MCP results explicitly return `SIMULATED`; rejection preserves `NOT_EXECUTED`.

**Verification.** `test_search_transactions_is_bounded`, `test_rollback_tool_only_requests_approval`, `test_rejected_approval_executes_no_critical_tool`, and `product UI › renders semantic status text`.

## Invariant 9 — Secrets never enter frontend or agent-visible business content

**Reason.** A model, browser bundle, log, or evidence payload must not become a credential exfiltration path.

**Enforcement.** `OPENAI_API_KEY` is a server-side `SecretStr`; local env files are ignored; prompts receive only selected evidence summaries; frontend configuration contains only the public API origin.

**Verification.** `test_openai_key_is_held_as_a_secret`, repository secret scanning, and `.gitignore` verification. Any new secret-bearing integration requires a dedicated non-disclosure test.

## Invariant 10 — Agents cannot modify security audit history

**Reason.** An actor must not erase or rewrite evidence of its own actions or policy denials.

**Enforcement.** The application exposes only `GET /api/audit`; the tool catalog has no audit mutation. Normal execution appends `AuditRecord` values, including blocked validation attempts. The local list resets only through the explicit whole-demo reset boundary.

**Verification.** `test_audit_api_is_read_only`, `test_agents_have_no_audit_mutation_tool`, and `test_malicious_tool_parameters_are_rejected`.

## Review rule

For tool, agent, MCP, authentication, or integration changes, explicitly ask: can untrusted text influence this, can parameters change after approval, can a decision replay or cross incidents, can it reveal secrets or access arbitrary resources, and can it create an unbounded loop? If any answer is yes, stop and fix the design.
