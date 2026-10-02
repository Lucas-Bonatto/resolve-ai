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
- Phase 8: 40-case executable benchmark with visible known regression
- Phase 9: unit, typing, lint, build, component, and critical browser verification
- Phase 10: Docker, CI, open-source policy, launch, and operator documentation
- Phase 11: repository engineering constitution, security invariants, codebase map, task/PR templates, and task-specific Definition of Done
- Product Proof: PostgreSQL repository, reproducible migrations, atomic approval consumption, evidence integrity, correlation IDs, validation/reporting, adversarial security tests, and provider-aware evaluation metadata
- Staff/red-team hardening: authoritative approval reload, strict tool schemas, stale-decision protection, tool-output-backed evidence, active evaluation policy probes, protocol-level MCP verification, and tracked-file secret scanning
- UX remediation pass 1: API-backed Command Center truth, explicit fixture labels, mobile disclosure navigation, skip navigation, active-route semantics, and 390 px overflow protection

## Next

- Promote pending approvals and resolved validation summaries near the incident header
- Group the War Room into milestone-first events with expandable technical detail
- Improve evaluation provenance and replace autonomous product claims with bounded-agentic language
- Capture demo media and deploy the public demo
- Calibrate real-provider confidence on a larger private evaluation set
- Add authentication and tenant-aware authorization before any public multi-user deployment
- Add durable cross-process event delivery before horizontally scaling SSE workers

## Known limitations

- The no-dependency default remains a deterministic single-process in-memory demo. Compose selects PostgreSQL; horizontal workers still need a durable event bus for cross-process SSE delivery.
- GitHub writes are mock-only unless an allowlisted live adapter is explicitly configured.
- Model confidence is a heuristic, not a calibrated probability.
- A live OpenAI provider smoke test reached the API on 2026-10-01 but returned `credit_balance_exhausted`; the real-provider result is therefore `NOT_EXECUTED` until account credits are available.
- Correlation IDs and structured audit records are implemented; production log export and tamper-evident archival are not.
- PostgreSQL migrations and repository contracts are tested locally, but real PostgreSQL concurrency was not rerun during the Phase 4 audit because Docker/PostgreSQL were unavailable on the audit host.

## Important decisions

- App-owned orchestration with the OpenAI Agents SDK keeps authorization and persistence under server control.
- Server-Sent Events provide one-way live workflow updates with less operational complexity than WebSockets.
- Full-text search is sufficient for the small fictional knowledge base; vector infrastructure would not improve the demo materially.
- Approval is consumed in the gateway before side-effect execution; PostgreSQL uses a status-predicate atomic update so competing workers cannot consume one approval twice.
