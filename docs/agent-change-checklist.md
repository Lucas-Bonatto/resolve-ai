# AI behavior change checklist

Use this checklist for changes to providers, prompts, tools, orchestration, structured outputs, evidence handling, or model configuration.

## Prompt

- [ ] The reason for the prompt change is recorded.
- [ ] Retrieved content remains explicitly untrusted data.
- [ ] The prompt does not decide permissions or request private chain-of-thought.

## Tools

- [ ] Changed schemas are typed, bounded, validated, and documented.
- [ ] Result size, timeout, failure, evidence IDs, and audit behavior are defined.

## Permissions

- [ ] Risk classification is explicit and was not downgraded for convenience.
- [ ] `CRITICAL_WRITE` still requires exact-action backend approval.

## Structured outputs

- [ ] Pydantic and exposed TypeScript contracts agree.
- [ ] Malformed output and unknown evidence references fail observably.

## Evaluation

- [ ] Affected cases and the full security subset were run.
- [ ] The previous and new generated results were compared.
- [ ] Regressions remain visible and are explained.

## Security

- [ ] Injection cases `eval_security_031`–`035` still pass.
- [ ] The model cannot alter authorization, budgets, state transitions, or allowlists.
- [ ] No arbitrary shell, SQL, filesystem, URL, or repository capability was added.

## Cost

- [ ] Turn, tool-call, timeout, and retry bounds still apply.
- [ ] The change does not multiply paid calls without a measured reason.

## Failure modes

- [ ] Timeout, unavailable provider, malformed output, missing evidence, and rejection fail safely.
- [ ] `INSUFFICIENT_EVIDENCE`, `FAILED`, or `ESCALATED` remain valid outcomes.

## Evidence

- [ ] Claims cite incident-owned IDs and unknown references are rejected.
- [ ] Confidence is presented as heuristic unless calibrated.

## Human control

- [ ] Operators can still reject critical actions.
- [ ] Approval is incident/tool-call/arguments/expiry/user bound and cannot be replayed.

## Phase 3 product-proof review — 2026-10-01

- [x] Prompt treats retrieved records as untrusted and does not authorize actions.
- [x] Diagnosis, validation, and report outputs are typed; unknown evidence fails observably.
- [x] Critical risk remained fixed and exact-action approval is backend enforced.
- [x] Full deterministic benchmark and security subset were run; the known failure stayed visible.
- [x] Turn, tool-call, and investigation-time limits remain enforced.
- [x] Timeout, provider unavailability, tool failure, rejection, insufficient evidence, and failed validation have safe outcomes.
- [x] Frontend and backend public contracts were updated together.
- [x] Optional live-provider smoke remains opt-in and secret-safe.

## Phase 4 staff/red-team review — 2026-10-01

- [x] No prompt was changed; retrieved records remain untrusted data and private reasoning is excluded.
- [x] Tool arguments now use strict, bounded schemas; allowlists, failures, evidence links, and audit records were verified.
- [x] `CRITICAL_WRITE` stayed fixed and forged, stale, mutated, mismatched, expired, rejected, and replayed approvals fail closed.
- [x] Diagnosis schemas reject missing, extra, null, invalid-enum, invalid-confidence, and unknown-evidence output.
- [x] The full deterministic benchmark ran; 30 cases exercised the production gateway boundary and the visible 39/40 result remained unchanged.
- [x] Injection cases `eval_security_031`–`035`, malicious-provider behavior, missing evidence, tool failure, timeout, rejection, and failed validation have safe outcomes.
- [x] Tool-call, turn, and investigation-time bounds remain enforced; the OpenAI provider still performs one bounded structured diagnosis call.
- [x] A safe live OpenAI smoke reached the provider but failed with account-credit exhaustion; no success claim is made.
