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

## Next

- Capture demo media and deploy the public demo
- Add an optional persistent PostgreSQL repository for hosted multi-user operation
- Calibrate real-provider confidence on a larger private evaluation set
- Add authentication and tenant-aware authorization before any public multi-user deployment

## Known limitations

- The default public experience is a deterministic single-process demo; durable PostgreSQL deployment is documented but not required for local exploration.
- GitHub writes are mock-only unless an allowlisted live adapter is explicitly configured.
- Model confidence is a heuristic, not a calibrated probability.
- A live OpenAI provider smoke test reached the API on 2026-09-30 but returned `credit_balance_exhausted`; the real-provider result is therefore `NOT_EXECUTED` until account credits are available.
- Structured audit records exist, but production log export and correlation-ID middleware are not yet implemented.

## Important decisions

- App-owned orchestration with the OpenAI Agents SDK keeps authorization and persistence under server control.
- Server-Sent Events provide one-way live workflow updates with less operational complexity than WebSockets.
- Full-text search is sufficient for the small fictional knowledge base; vector infrastructure would not improve the demo materially.
- Approval is consumed in the gateway before side-effect execution, and configured turn/tool/time budgets fail closed.
