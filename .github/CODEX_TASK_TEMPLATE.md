# Task

Describe the requested change and the observable outcome.

## Problem

What user, operator, contributor, or security problem does this solve? Include evidence rather than a proposed implementation when possible.

## Desired behavior

Describe the happy path, safe failure behavior, and execution labels (`EXECUTED`, `SIMULATED`, `NOT_EXECUTED`, or `BLOCKED`).

## Relevant areas

List likely modules, tests, ADRs, APIs, UI surfaces, fixtures, or evaluation cases if known.

## Security constraints

State affected trust boundaries, tool risk, approval needs, untrusted inputs, secret handling, allowlists, and abuse cases. Link `docs/security-invariants.md` when relevant.

## Acceptance criteria

- [ ] Observable behavior is defined.
- [ ] Failure and edge cases are defined.
- [ ] Security invariants remain enforceable.
- [ ] Demo Mode remains honest and resettable.

## Required verification

- [ ] Focused tests
- [ ] Full affected test suite
- [ ] Lint
- [ ] Type checks
- [ ] Relevant evaluations and regression comparison
- [ ] Production build when web code changes
- [ ] Flagship E2E when workflow/War Room code changes
- [ ] Secret and change-set review

## Documentation impact

List required README, architecture, security, runtime-agent, MCP, evaluation, ADR, API, or project-status updates. Write “None” with a reason if no documentation changes are expected.

## Non-goals

Explicitly state what is outside scope to prevent unrelated refactors or integrations.

## Known limitations

Record constraints that the implementation may not silently conceal.
