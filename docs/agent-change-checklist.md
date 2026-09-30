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
