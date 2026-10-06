# RESOLVEAI — PROMPT 4 STAFF ENGINEER / SECURITY / AI / RED TEAM AUDIT

Audit date: 2026-10-01. This document records the repository evidence and findings. The completion response records the final commit hash and clean-tree state after this file is committed.

## 1. Repository State

- Branch: `phase-4-staff-red-team-audit`
- Starting checkpoint: `5b3dbfaeaef3ed60e6c09e4cfcc4d1dc6fc4198c`
- Protected tag: `checkpoint-phase-3-product-proof`
- Protected bundle SHA-256: `3D136E96685BE0D85DBAA4B3DB8605663A528E6403DC88DA16BFB82649CCDC14`
- Remote: none
- Push performed: no
- Protected checkpoints: unchanged

## 2. Executive Technical Summary

The central claims are defensible after remediation, within the documented local-demo boundary. The audit found two critical approval defects and two high-integrity/evaluation defects. All four were fixed and protected by negative regression tests. A malicious provider cannot authorize or execute the registered critical action; fabricated or cross-incident evidence IDs are rejected; and failed validation cannot produce `RESOLVED`.

The repository is not an internet-facing production control plane. It has no authenticated principal or tenancy model, demo/reset/evaluation endpoints are exposed to any caller that can reach the API, audit storage is not tamper-evident, external side effects have no distributed idempotency contract, and real PostgreSQL concurrency could not be rerun on this host. Those limitations are now stated explicitly.

## 3. Findings Summary

- CRITICAL: `SEC-001`, `SEC-002` — fixed and verified; none remaining.
- HIGH: `INT-001`, `EVAL-001` — fixed and verified; none remaining.
- MEDIUM: `TOOL-001`, `OBS-001`, `MCP-001` fixed; `AUTH-001`, `DB-001`, `EVID-001`, `AUDIT-001`, `REL-001` remain scoped limitations.
- LOW: `CI-001`, `DOC-001` fixed; `TOOL-002` remains.
- INFO: `OPENAI-001`, `RUNTIME-001`.

## 4. Critical / High Findings

### SEC-001

- Severity: CRITICAL
- Area: Approval Gateway
- Claim being challenged: a caller cannot forge an approval-shaped object or redirect an approved action.
- Evidence: `execute_approved` previously trusted caller-supplied approval bindings while the in-memory repository was the default runtime.
- Reproduction / code path: create a legitimate approval; construct an object with the same approval ID but another tool-call ID and arguments; pass it to `ToolGateway.execute_approved`. The pre-fix negative test reached the side effect.
- Impact: an internal caller holding an approval ID could redirect a critical action, invalidating exact-action approval.
- Recommended remediation: reload the authoritative repository approval, compare all binding fields, revalidate canonical arguments and fixed risk, then consume before the side effect.
- Verification required after fix: forged object, mutation, mismatch, replay, and direct-gateway tests must fail closed.
- Status: FOUND → FIXED → VERIFIED.

### SEC-002

- Severity: CRITICAL
- Area: PostgreSQL approval decisions
- Claim being challenged: consumed approvals cannot be reopened by stale workers.
- Evidence: `PostgresRepository.save_approval` previously updated by ID without checking the stored status.
- Reproduction / code path: worker A consumes an approved record; worker B retains a stale `PENDING` object and writes `APPROVED`; the old update could reopen the row for a second consumption.
- Impact: cross-worker replay of one human decision could allow more than one critical attempt.
- Recommended remediation: compare-and-set approval decisions from permitted source states and reserve `CONSUMED` for the atomic consumption method.
- Verification required after fix: a stale repository decision must fail after consumption; the real PostgreSQL two-worker test must allow at most one consumer.
- Status: FOUND → FIXED → VERIFIED at repository contract level; real PostgreSQL rerun unavailable locally.

### INT-001

- Severity: HIGH
- Area: Evidence and flagship orchestration
- Claim being challenged: conclusions are derived from persisted tool evidence.
- Evidence: the coordinator executed tools but discarded outputs, then created fixed log/deployment/test evidence. Missing root-cause signals could still produce the flagship diagnosis.
- Reproduction / code path: make logs or deployments return no matching data; before the fix, fixed evidence IDs were still persisted.
- Impact: the system could present a supported diagnosis and approval based on facts the tool did not return.
- Recommended remediation: validate each evidence-bearing output, persist only corroborated records, link them to the producing tool call, and return `INSUFFICIENT_EVIDENCE` when required signals are missing.
- Verification required after fix: missing logs/deployment, misleading health output, unavailable transactions, and provider-hallucinated evidence must not create a supported result.
- Status: FOUND → FIXED → VERIFIED.

### EVAL-001

- Severity: HIGH
- Area: Evaluation security metrics
- Claim being challenged: zero approval bypass and zero unauthorized critical execution are executable results.
- Evidence: the old grader inferred both metrics from fixture fields and selected tool names; no production permission boundary was invoked.
- Reproduction / code path: change `PermissionEngine.evaluate` to allow critical writes; the old security scores remained zero.
- Impact: the Evaluation Center could display a strong security claim while the actual gateway was vulnerable.
- Recommended remediation: actively call a registered `CRITICAL_WRITE` through the production gateway without approval for every approval/injection case; count a violation only if the side effect executes.
- Verification required after fix: mutation the policy to `ALLOW` and prove bypass/unauthorized metrics become nonzero.
- Status: FOUND → FIXED → VERIFIED; 30 active probes execute in the 40-case suite.

## 5. Medium / Low Findings

- `TOOL-001` (MEDIUM, fixed): application tools accepted generic dictionaries with coercion and extra fields. Strict per-tool Pydantic schemas, bounds, incident checks, and service/deployment allowlists now fail closed.
- `OBS-001` (MEDIUM, fixed): the validation audit record carried an approval ID but omitted its tool-call ID. The critical chain is now reconstructable by incident, correlation, run, tool call, and approval.
- `MCP-001` (MEDIUM, fixed): MCP existed as code but protocol runtime and unknown-resource behavior were not proven. A stdio client now starts the server, lists 14 tools, and verifies rollback remains proposal-only; unknown resources receive no evidence ID.
- `AUTH-001` (MEDIUM, open): no authentication, tenancy, or rate limiting. Approval actors are self-asserted; chaos/reset/evaluation endpoints are demo-only and unsafe for public multi-user exposure.
- `DB-001` (MEDIUM, open): application ownership and transition rules are stronger than database constraints; citation arrays are JSON rather than foreign-key relations. Real PostgreSQL integration was not available on this host.
- `EVID-001` (MEDIUM, open): ID existence/ownership proves provenance, not semantic support. The deterministic flagship validates known signals, but arbitrary model claims still need reviewer judgment or stronger entailment evaluation.
- `AUDIT-001` (MEDIUM, open): audit records are append-only through the application surface but not cryptographically tamper-evident and are cleared by explicit demo reset.
- `REL-001` (MEDIUM, open): approval consumption is single-use; a future external side effect still requires an idempotency key/outcome-reconciliation design for ambiguous network completion.
- `TOOL-002` (LOW, open): input contracts are strict, while simulator/MCP outputs remain structured dictionaries rather than a Pydantic model per tool. Evidence-bearing flagship fields are explicitly checked.
- `CI-001` (LOW, fixed): CI did not run evals or a tracked-file secret scan. Both now execute in the Python job, followed by `git diff --check`.
- `DOC-001` (LOW, fixed): README/UI language could make deterministic results or approval identity sound stronger than they are. Copy now distinguishes active gateway probes, DemoProvider results, and unauthenticated attribution.
- `OPENAI-001` (INFO): the opt-in live smoke reached OpenAI but returned `429 credit_balance_exhausted`; no live-provider success is claimed.
- `RUNTIME-001` (INFO): Docker and `psql` were unavailable; Compose and real PostgreSQL runtime verification were not run.

## 6. Findings Fixed During Audit

| ID | Original issue | Fix | Regression evidence | Result |
|---|---|---|---|---|
| SEC-001 | Forged approval could redirect default-runtime action | Authoritative reload and full binding/risk/argument validation | `test_forged_approval_object_cannot_redirect_an_approved_action` | PASS |
| SEC-002 | Stale PostgreSQL writer could reopen consumed approval | Compare-and-set decision transitions | `test_stale_repository_cannot_reopen_a_consumed_approval` | PASS on repository contract; real PG skipped |
| INT-001 | Fixed evidence ignored actual tool results | Output validation, conditional persistence, tool-evidence links | missing logs/deployment/transactions/health tests | PASS |
| EVAL-001 | Security zeros inferred from fixtures | 30 active gateway probes plus mutation-style test | policy mutation produces nonzero violations | PASS |
| TOOL-001 | Generic/coercive tool arguments | Strict schemas and allowlists | extra/coerced/mutated/unknown argument tests | PASS |
| OBS-001 | Incomplete critical audit chain | Validation carries tool-call and approval IDs | reconstructable chain test | PASS |
| MCP-001 | MCP runtime unproven | Real stdio session and negative resource tests | protocol/tool tests | PASS |
| CI-001 | Evals/secret scan absent in CI | Added benchmark, secret scanner, whitespace gate | local execution | PASS |

## 7. Claim Evidence Matrix

| Claim | Implemented | Tested | Runtime Verified | E2E Verified | Evidence |
|---|---|---|---|---|---|
| PostgreSQL persistence | YES | YES | NO | NO | repository, migrations, SQLite contract tests; no local PG |
| Human approval | YES | YES | YES | YES | HTTP/browser approve and reject journeys |
| Approval replay protection | YES | YES | YES | YES | gateway tests and second HTTP approval returns conflict; PG-specific runtime not rerun |
| Evidence integrity | YES | YES | YES | NO | repository/provider/workflow negative tests |
| Hypothesis engine | YES | YES | YES | YES | flagship workflow and War Room |
| Prompt injection security | YES | YES | YES | NO | hostile tool/log/provider tests; no live-model resistance claim |
| MCP | YES | YES | YES | NO | real stdio client; app coordinator deliberately does not use MCP |
| Structured outputs | YES | YES | YES | YES | Pydantic diagnosis through flagship flow |
| Correlation IDs | YES | YES | YES | NO | HTTP/API and audit-chain tests; browser does not assert full propagation |
| Audit trail | YES | YES | YES | NO | reconstructable critical chain; not tamper-evident |
| Evaluation Center | YES | YES | YES | YES | 40-case runner and browser journey |
| DemoProvider | YES | YES | YES | YES | deterministic no-key flagship |
| OpenAIProvider | YES | YES | NO | NO | safe live smoke failed for account credits |
| Flagship scenario | YES | YES | YES | YES | real FastAPI/Next.js/Playwright flow |
| War Room | YES | YES | YES | YES | browser approval/rejection/narrow journeys |
| Post-remediation validation | YES | YES | YES | YES | false-resolution unit test and approved browser flow |
| CI readiness | YES | YES | NO | NO | local commands pass; GitHub Actions not run remotely |

## 8. Approval Security

Authoritative path: coordinator/tool request → fixed catalog risk → `propose_critical` creates `NOT_EXECUTED` call and pending approval → human decision → repository-owned approval reload → exact binding and canonical argument validation → `PermissionEngine.authorize_critical` → atomic consumption → protected simulator action → audit and validation.

Missing, replayed, argument-mutated, hidden/default/extra/coerced, incident-mismatched, tool-mismatched, tool-call-mismatched, expired, rejected, forged, frontend-bypassed, and MCP-bypassed attempts are blocked. In-memory concurrent consumption permits at most one attempt. PostgreSQL uses conditional status and exact-binding predicates, but its real concurrent test was skipped locally because no server was available. There is no alternate application remediation endpoint; the simulator remains an internal adapter and is not a public/model tool.

## 9. Evidence Security

Nonexistent, cross-incident, and provider-fabricated IDs are rejected before diagnosis persistence. Tool outputs cannot create evidence merely by returning a plausible ID; the coordinator assigns stable IDs after validating expected signal fields. Persisted in-memory evidence and API snapshots are deep-copied against caller mutation. Direct database administration, repository internals, deletion semantics, and cryptographic immutability remain outside the guarantee. Valid IDs establish ownership and provenance, not universal semantic entailment.

## 10. Prompt Injection

Knowledge articles, logs, tool output, incident/provider text, fake authorization, and secret-extraction instructions were exercised in deterministic tests. A deliberately compromised provider that claims system approval cannot move beyond the real approval boundary. Backend controls are fixed risk, strict schemas, allowlists, repository approval state, state transitions, evidence ownership, and secret isolation. Model-level resistance is defense in depth only; it was not live-verified because the paid smoke failed for credits. No arbitrary shell, SQL, filesystem, URL, GitHub, or secret-retrieval tool exists.

## 11. Agent / Tools / MCP

The runtime is one bounded coordinator, not a swarm. `MAX_AGENT_TURNS`, `MAX_TOOL_CALLS_PER_RUN`, and `MAX_INVESTIGATION_SECONDS` are enforced. The application catalog contains seven READ tools, one SAFE_WRITE tool, and one CRITICAL_WRITE tool; classification changes execution mechanically. MCP exposes 14 fictional typed operations and was exercised over stdio. Critical MCP calls only return `REQUIRE_APPROVAL`, `executed: false`, `SIMULATED`; they cannot consume application approvals. Diagnosis uses a strict Pydantic output; malformed/extra/null/enum/confidence/evidence failures are rejected. Timeout, missing evidence, provider/tool/remediation failure, rejection, expiry, and validation failure have bounded terminal outcomes.

## 12. Persistence

`PostgresRepository` persists the incident graph and rehydrates it; Alembic revisions `0001` and `0002` compile using the PostgreSQL dialect. Decisions and consumption use compare-and-set updates. The CI job provides PostgreSQL 17 and applies migrations before tests. On this audit host, Docker and `psql` were unavailable, so no fresh database or native concurrency run occurred. Remaining limitations include JSON citation lists without foreign keys, application-owned state-transition validation, in-process SSE subscriptions, no tamper-evident audit archive, and no external-side-effect idempotency contract.

## 13. Flagship Scenario

| Stage | Implemented | Tested | Runtime Verified | E2E Verified |
|---|---|---|---|---|
| Inject/triage/investigate | YES | YES | YES | YES |
| Bounded evidence collection | YES | YES | YES | YES |
| Competing hypotheses | YES | YES | YES | YES |
| Structured diagnosis | YES | YES | YES | YES |
| Plan and approval pause | YES | YES | YES | YES |
| Approve/reject/replay handling | YES | YES | YES | YES |
| Critical simulated execution | YES | YES | YES | YES |
| Validation before resolution | YES | YES | YES | YES |
| Report/audit chain | YES | YES | YES | NO |

Negative tests cover rejection, expiry, replay, missing logs/deployments/transactions, misleading health output, unknown evidence, investigation timeout, remediation failure, and failed validation. All passed.

## 14. Evaluation Center Forensics

- Provider/model: `demo` / `deterministic-demo-v1`.
- Suite: `resolveai-benchmark-v1`, 40 fictional deterministic contract cases.
- Formula: `scenario_contract_success_rate = passed / case_count`.
- Result: 39/40 = 0.975; failed case `eval_false_correlation_020`.
- Determinism: decisions and aggregate scores are deterministic; IDs, timestamps, and measured milliseconds vary.
- Hardcoded metrics: none found in the result path; the UI reads a run. Static dashboard wording was removed.
- Security computation: 30 approval/injection cases attempt an unapproved registered rollback through `ToolGateway`. A mutation-style test proves a permissive policy produces nonzero violations.
- Meaning: 97.5% is fixture scenario-contract success, not OpenAI model accuracy. The diagnosis/tool mappings remain deterministic and fixture-biased.

## 15. OpenAI Provider

The provider is implemented server-side with the OpenAI Agents SDK, configured model, `Diagnosis` output type, and `max_turns`. It receives selected evidence text and no application tools, so tool authorization stays in ResolveAI. `OPENAI_API_KEY` is a `SecretStr`, real execution requires two explicit settings, exceptions cross the boundary as a safe typed error, and no key was printed. The safe live smoke reached OpenAI and failed with `429 credit_balance_exhausted`; live provider success and E2E behavior are not verified.

## 16. DemoProvider

DemoProvider is deterministic, no-key, and intentionally fixture-specific. It requires four known evidence IDs or returns `INSUFFICIENT_EVIDENCE`. That is useful for reproducible product proof but is not general AI reasoning and must not be marketed as model accuracy. UI/results identify provider, model, run kind, and sample-data state. The flagship is reproducible without an OpenAI key.

## 17. Observability

Correlation IDs originate at HTTP or the MCP server and flow through incidents, runs, tool calls, approvals, events, validation, reports, and audit records. The completed critical chain is test-reconstructable. Logs contain safe identifiers/error types rather than raw secrets or private reasoning. Production export, cross-process trace storage, audit signing, retention, and immutable archival are absent.

## 18. API / Trust Boundaries

- Browser: untrusted requester and renderer; never authorizes.
- FastAPI: transport validation and correlation boundary; unauthenticated in the demo.
- Coordinator: trusted application workflow, but not permission authority by prompt.
- Provider/model: untrusted structured proposal source.
- Tool/MCP outputs: untrusted structured data requiring schema/signal checks.
- ToolGateway/PermissionEngine: authoritative policy and execution boundary.
- Repository/database: authoritative approval and incident-owned evidence state.
- Human decision: required for critical action, but actor identity is self-asserted in this demo.
- Simulator: trusted fictional adapter, never a model-exposed general-purpose capability.

## 19. State Machine / Validation

`validate_transition` rejects unsupported edges and terminal states have no outgoing transitions. Route code does not accept arbitrary incident state. Repository methods could be misused by trusted internal code and PostgreSQL does not encode the entire transition graph. A successful critical simulator return moves to `VALIDATING`, not `RESOLVED`; only passed validation reaches resolution. Failed validation escalates and the report records the non-resolved terminal state.

## 20. Test Quality

The suite exercises production gateway/repository/coordinator code rather than mocking policy. Security regressions cover exact approval binding, concurrency contracts, injection, evidence ownership, tool budgets, failed remediation, and false resolution. Mutation-style checks proved both the original forged-approval failure and that disabling policy makes evaluation security metrics fail. Main gaps are native PostgreSQL, live OpenAI success, MCP-to-application E2E, DB/network failure injection, and broad semantic-support grading. Coverage percentage was not measured.

## 21. CI / Fresh Clone

Local Ruff, MyPy, Pytest, ESLint, TypeScript, Vitest, Playwright, Next.js build, Alembic offline SQL, benchmark, secret scan, and whitespace checks passed. GitHub Actions defines Python/PostgreSQL, web, and real HTTP/browser jobs; no remote exists, so GitHub Actions did not run. The documented no-key path uses the in-memory DemoProvider and does not require seed data or PostgreSQL. `npm ci`/fresh dependency installation was inspected in CI but not rerun from an empty clone during this audit. Docker Compose was not run because Docker is unavailable.

## 22. Secret Scan

The tracked-file scanner checks high-confidence OpenAI/GitHub/JWT/private-key signatures without printing values and passed. `.env.local`, `.env`, build outputs, and `node_modules` are ignored; the locally configured OpenAI key remained untracked and server-only. No frontend key reference, credential fixture, raw key log, or committed token was found. This is a high-confidence repository scan, not a substitute for platform secret scanning or history scanning.

## 23. Portfolio Claim Safety

### Technically Defensible Claims

- Evidence-first deterministic flagship with competing hypotheses and explicit insufficient-evidence outcomes.
- Backend-enforced, exact-action, expiring, single-use approval for the registered critical tool.
- Real FastAPI/Next.js browser workflow that pauses, approves/rejects, validates, and reports honestly as simulated.
- Strict tool inputs, structured diagnosis output, stable evidence ownership checks, bounded execution, audit/correlation records.
- Actual standalone MCP server exercised over stdio with proposal-only critical functions.
- PostgreSQL repository and migrations with compare-and-set approval logic, qualified by local runtime status.
- 40-case deterministic contract benchmark with 30 active gateway security probes and one visible failure.
- Optional OpenAI Agents SDK provider, with no claim of successful live model verification.

### Claims That Should NOT Be Published Yet

- “Production-ready”, “enterprise-ready”, or authenticated multi-tenant approval plane.
- “97.5% AI/OpenAI accuracy” or calibrated diagnosis confidence.
- “Fully tested PostgreSQL” or verified distributed execution on this audit host.
- “Prompt-injection proof” at model-behavior level.
- “Exactly-once external remediation”, “tamper-proof audit”, or “zero security vulnerabilities”.
- “The application uses MCP internally”; MCP is a standalone protocol surface.
- “OpenAI live test passed” or “autonomous operator”.

## 24. Interview Questions

1. Why one coordinator instead of multiple agents? Defensible: ADR and bounded responsibility.
2. Why MCP if the coordinator does not use it? Defensible only as a standalone interoperability/security demonstration.
3. Why PostgreSQL? Defensible for durable graph/approval state, qualified by the missing local runtime rerun.
4. Why can the model not authorize? Defensible: fixed server risk and authoritative approval gateway.
5. How is replay prevented? Defensible: exact binding, pre-effect consumption, lock/CAS predicates, negative tests.
6. What does persisted evidence prove? Defensible with qualification: ownership/provenance, not semantic entailment.
7. What if the model follows an injection perfectly? Defensible: malicious-provider test still stops at approval.
8. What if remediation succeeds but validation fails? Defensible: `VALIDATING → ESCALATED`, never `RESOLVED`.
9. What does 97.5% measure? Defensible: 39/40 deterministic fixture contracts, not model quality.
10. What changes for enterprise deployment? Defensible: authentication/tenancy, protected demo endpoints, external idempotency, durable events/audit/telemetry, real-provider and PostgreSQL qualification.

## 25. Remaining Risks

The material remaining risks are unauthenticated API decisions/demo controls, no tenancy, non-tamper-evident/resettable audit, no distributed idempotency for future external writes, in-process SSE state, incomplete DB-level enforcement of domain invariants, generic structured tool outputs, semantic-support limitations, unavailable native PostgreSQL verification, and an unverified live OpenAI success path.

## 26. Files Changed

The audit changed approval/tool/repository/orchestrator/evaluation/MCP boundaries; added adversarial, protocol, evidence, failure, and audit-chain tests; added CI eval/secret gates; regenerated the benchmark result; corrected dashboard/evaluation copy; and updated architecture, security, deployment, MCP, agent, evaluation, status, and README claims.

## 27. Commits Created

- `0b4b4a1` — `fix: close approval and evidence boundary bypasses`
- `3c97156` — `test: make policy and MCP claims executable`
- Documentation commit: recorded in the final completion response after this report is committed.

No push, remote, tag, bundle, or protected commit mutation was performed.

## 28. Quality Gates

- Ruff: PASS
- MyPy: PASS
- Pytest: PASS (`73 passed`, `2 skipped`)
- Approval security tests: PASS
- Prompt injection tests: PASS
- Evidence tests: PASS
- MCP tests: PASS, including real stdio protocol interaction
- PostgreSQL integration: SKIPPED (Docker/PostgreSQL unavailable); Alembic offline SQL PASS
- ESLint: PASS
- TypeScript: PASS
- Vitest: PASS (`2 passed`)
- Playwright: PASS (`4 passed` against real FastAPI and Next.js servers)
- Next.js production build: PASS
- Benchmark/evals: PASS as execution (`40` cases, `39/40`, one visible expected regression, `30` active policy probes)
- Secret scan: PASS (`125` tracked files at execution time, zero findings)
- Docker Compose: NOT AVAILABLE

## Final Verdict

```text
CORE_SECURITY_INVARIANTS_VERIFIED = YES

PORTFOLIO_CLAIMS_TECHNICALLY_DEFENSIBLE = YES

CRITICAL_FINDINGS_REMAINING = 0

HIGH_FINDINGS_REMAINING = 0

READY_FOR_UX_UI_AUDIT = YES
```

These verdicts apply to the bounded, fictional, local/demo claims stated by the repository. They do not certify an authenticated multi-user production control plane.
