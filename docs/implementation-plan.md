# ResolveAI implementation plan

Status: active, updated 2026-09-30.

## Research baseline

- OpenAI recommends the Agents SDK when the application owns tools, storage, approval decisions, and orchestration. ResolveAI therefore uses an app-owned manager workflow rather than a hosted autonomous harness.
- Structured outputs are represented by Pydantic contracts. Tool calls use typed function contracts and deterministic server-side policy.
- Current OpenAI documentation recommends the GPT-6 family for new agent workflows; the configurable default is `gpt-6-luna` to keep portfolio demos cost-conscious.
- The current MCP Python SDK v2 uses `MCPServer` and supports the 2026-07-28 protocol. The NovaPay server follows that contract.
- Next.js 16.3 App Router is the verified frontend baseline. Server Components are the default; interactive war-room surfaces are bounded client components.

Sources: [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk), [OpenAI guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals), [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), [Next.js App Router](https://nextjs.org/docs/app).

## Delivery slices

1. Establish repository contracts, threat model, ADRs, configuration, and CI.
2. Build the deterministic NovaPay simulation and explicit incident state machine.
3. Add audited tools, evidence validation, hypotheses, and permission enforcement.
4. Add the manager-style agent runtime with interchangeable demo/OpenAI providers.
5. Implement exact-argument, expiring human approvals and validation after execution.
6. Deliver the landing page, command center, war room, security center, and evaluation center.
7. Ship 40 deterministic evaluation cases, including prompt-injection and approval-bypass cases.
8. Verify unit, API, component, build, and critical browser flows.
9. Finish open-source documentation, launch material, and an honest final review.

## Acceptance gates

- Demo mode runs without an API key and uses the same domain contracts as real mode.
- Every diagnosis references evidence IDs that exist for that incident.
- Critical tool execution without a valid approval is denied and audited.
- The flagship flow reaches `AWAITING_APPROVAL`, then resolves only after explicit approval and validation.
- Generated evaluation results are persisted; fixture results are labeled `SAMPLE DATA`.
- No private reasoning, credentials, real customer data, or unverified success claims appear in UI or logs.
