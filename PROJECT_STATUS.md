# Project status

## Completed

- Phase 0: official documentation review and implementation plan
- Phase 1: monorepo architecture, ADRs, typed domain primitives, CI skeleton
- Phase 2: deterministic NovaPay simulator and flagship scenario fixtures
- Phase 3: incident state machine, evidence, hypotheses, diagnosis, audit trail
- Phase 4: typed tool catalog and NovaPay MCP server
- Phase 5: provider abstraction with Demo and OpenAI Agents SDK providers
- Phase 6: deterministic permission engine and argument-bound approvals
- Phase 7: responsive command center, incident war room, run, audit, security, and evaluation surfaces
- Phase 8: 40-case executable benchmark with visible per-case failures and computed metrics
- Phase 9: unit, typing, lint, build, component, and critical browser verification
- Phase 10: Docker, CI, open-source policy, launch, and operator documentation
- Phase 11: repository engineering constitution, security invariants, codebase map, task/PR templates, and task-specific Definition of Done
- Product Proof: PostgreSQL repository, reproducible migrations, atomic approval consumption, evidence integrity, correlation IDs, validation/reporting, adversarial security tests, and provider-aware evaluation metadata
- Staff/red-team hardening: authoritative approval reload, strict tool schemas, stale-decision protection, tool-output-backed evidence, active evaluation policy probes, protocol-level MCP verification, and tracked-file secret scanning
- UX remediation pass 1: API-backed Command Center truth, explicit fixture labels, mobile disclosure navigation, skip navigation, active-route semantics, and 390 px overflow protection
- UX remediation pass 2: top-level exact-action approval and validation/report outcome summaries in the flagship War Room, without duplicated state
- UX remediation pass 3: milestone-first investigation timeline with expandable technical activity, bounded-agentic product language, and executed evaluation provenance with in-process comparison
- UX remediation pass 4: accessible skip navigation, focus and disclosure behavior, async status announcements, named table regions, targeted contrast corrections, 320 px reflow, and forced-colors coverage
- Brazilian Portuguese product localization: public landing page, command center, incident surfaces, War Room, evaluations, security, audit, errors, accessible labels, and browser tests; canonical technical identifiers and execution labels remain visible for auditability
- Evaluation false-correlation remediation: provider-outage evidence now outranks an unrelated recent deployment in `eval_false_correlation_020`, with deterministic tool-selection coverage and a regenerated 40/40 contract result
- Public showcase release-candidate boundary: fail-closed deployment configuration, explicit CORS allowlist, deterministic startup snapshot, versioned evaluation result, backend-wide mutation denial, bounded local request limiting, security headers, and visibly disabled UI controls
- Public showcase deployment readiness: Render Blueprint with exact cross-service HTTPS origins, single-instance boundaries, executed-benchmark revision provenance, packaged evaluation artifact, platform-port support, and a CI container contract smoke test
- Pre-publication dependency hardening: Vitest upgraded to the first Node 20-compatible patched line and pytest raised past its insecure temporary-directory implementation; production npm dependencies audit clean

## Next

- Publish the release commit to a Git remote, deploy the read-only Render Blueprint, and capture desktop/narrow-layout release media
- Calibrate real-provider confidence on a larger private evaluation set
- Add authentication and tenant-aware authorization before any public multi-user deployment
- Add durable cross-process event delivery before horizontally scaling SSE workers

## Known limitations

- The no-dependency default remains a deterministic single-process in-memory demo. Compose selects PostgreSQL; horizontal workers still need a durable event bus for cross-process SSE delivery.
- The unauthenticated public showcase is intentionally read-only and single-process. Interactive public approvals require authenticated identity plus tenant/session isolation; hosting-edge denial-of-service and connection controls remain mandatory.
- The committed Render Blueprint uses free web services by default; inactive services can cold-start slowly, and platform usage/billing settings must be reviewed before external creation.
- The current Next.js ESLint toolchain retains a development-only `braces` denial-of-service advisory with no patched upstream release; lint inputs are repository-controlled and production dependencies audit clean.
- GitHub writes are mock-only unless an allowlisted live adapter is explicitly configured.
- Model confidence is a heuristic, not a calibrated probability.
- A live OpenAI provider smoke test reached the API on 2026-10-01 but returned `credit_balance_exhausted`; the real-provider result is therefore `NOT_EXECUTED` until account credits are available.
- Correlation IDs and structured audit records are implemented; production log export and tamper-evident archival are not.
- PostgreSQL migrations and repository contracts are tested locally, but real PostgreSQL concurrency was not rerun during the Phase 4 audit because Docker/PostgreSQL were unavailable on the audit host.
- The focused accessibility pass has automated keyboard, reflow, semantics, and forced-colors coverage, but it is not a WCAG certification; a real screen-reader session and 200% zoom review remain manual release checks.

## Important decisions

- App-owned orchestration with the OpenAI Agents SDK keeps authorization and persistence under server control.
- Server-Sent Events provide one-way live workflow updates with less operational complexity than WebSockets.
- Full-text search is sufficient for the small fictional knowledge base; vector infrastructure would not improve the demo materially.
- The first public release profile is a deterministic read-only snapshot; local development remains interactive, and no browser capability flag can override the backend mutation gate.
- Approval is consumed in the gateway before side-effect execution; PostgreSQL uses a status-predicate atomic update so competing workers cannot consume one approval twice.
