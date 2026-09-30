# Runtime agent architecture

This document explains ResolveAI's runtime AI design to maintainers and reviewers. Mandatory coding-agent rules live in the repository root `AGENTS.md`.

## One coordinator, one probabilistic boundary

ResolveAI uses an application-owned manager workflow. `IncidentCoordinator` in `services/api/app/application/orchestrator.py` owns the incident lifecycle and invokes deterministic services for evidence collection, state transitions, remediation policy, approval, execution, and validation.

The only probabilistic boundary in the flagship flow is diagnosis:

```text
IncidentCoordinator
  ├─ deterministic simulator and ToolGateway
  ├─ evidence and hypothesis construction
  ├─ AIProvider.diagnose(...)
  │    ├─ DemoAIProvider
  │    └─ OpenAIProvider → OpenAI Agents SDK
  ├─ deterministic remediation plan
  ├─ exact-action human approval
  └─ deterministic post-remediation validation
```

Investigator, Code Analyst, Remediation Planner, and Incident Reporter are conceptual responsibilities, not separate autonomous agents. ADR 0001 deliberately rejects a swarm because it would add cost and obscure responsibility without improving the current workflow.

## Provider contract

`AIProvider` accepts the incident description plus validated `Evidence` objects and returns a Pydantic `Diagnosis`. Both implementations use that contract:

- `DemoAIProvider` returns a repeatable result from the fictional fixture, enabling offline use and CI.
- `OpenAIProvider` invokes a configured model through the OpenAI Agents SDK with `Diagnosis` as structured output.

The application validates every returned evidence ID against the incident-owned evidence set. Unknown IDs fail the run; they are not silently removed. The provider is never asked to authorize a tool or change incident state.

Real model execution is opt-in: `AI_PROVIDER=openai` and `ENABLE_REAL_AI=true` must both be set on the server, and the key remains a `SecretStr`. Demo mode is the default and uses the identical coordinator path.

## Bounded execution

Runtime limits come from `services/api/app/config.py`:

- `MAX_AGENT_TURNS` bounds Agents SDK turns;
- `MAX_TOOL_CALLS_PER_RUN` is enforced by `ToolGateway` before a new call is recorded;
- `MAX_INVESTIGATION_SECONDS` wraps the complete investigation task;
- `DEMO_EVENT_DELAY_MS` is capped and only slows deterministic events for legibility.

Timeout marks the run and incident `FAILED`; it does not force a remediation. Provider errors are converted to a safe `AIProviderUnavailable` boundary and the run records only a safe error type.

## Evidence and hypotheses

The coordinator collects stable evidence IDs from bounded tools before diagnosis. The flagship flow maintains a provider-outage hypothesis and a webhook-regression hypothesis, then changes their confidence/status as metrics, logs, deployments, and a controlled regression test arrive.

Confidence is a heuristic ranking aid, not a calibrated probability. The system may return `INSUFFICIENT_EVIDENCE` or escalate rather than invent a cause.

Retrieved content is enclosed as untrusted evidence for the OpenAI provider. Prompt instructions are defense in depth; `PermissionEngine`, schema validation, allowlists, and the approval gateway remain the security boundary.

## Tool and approval flow

Read and safe-write tools pass through `ToolGateway`, which validates arguments, enforces the tool-call budget, records the call, executes the simulator, and appends audit data. A critical tool is first recorded as `NOT_EXECUTED` with a pending `Approval`.

The approval stores the incident, tool-call ID, canonical arguments hash, rationale, evidence, impact, status, and expiration. On approval, the permission engine rechecks the binding. The gateway consumes the approval before attempting the simulated side effect, preventing replay even when execution fails. Rejection leaves the call `NOT_EXECUTED` and escalates the incident.

The standalone NovaPay MCP server is a protocol surface, not an alternate authorization path. Its critical functions return a proposal with `REQUIRE_APPROVAL` and never execute the action.

## State and observability

The coordinator alone requests transitions through `validate_transition`. Run records expose provider, model, status, trace ID, timings, tool-call count, safe error type, and token/cost fields when the provider supplies them. The UI intentionally does not expose private chain-of-thought.

Workflow events are published to incident-owned queues and delivered through cursor-based SSE. UI progress therefore reflects actual application events. Audit records cover workflow, tool, policy, and human decisions; the current local implementation is process-local and resets with the demo.

## Evaluation obligations

The 40-case deterministic suite covers multiple incident families, five prompt-injection cases, five insufficient-evidence cases, tool selection, evidence recall, approval bypass, and unauthorized critical execution. Prompt, model, provider, tool, orchestration, or evidence-contract changes require an evaluation run and comparison with `evals/results/latest.json`.

One false-correlation regression is deliberately visible. It is evidence to investigate, not a result to hide.

## Extension criteria

Add another runtime agent only when it has a genuinely separate bounded responsibility that a deterministic service or typed call cannot satisfy. The proposal must define input/output schemas, tools, risk policy, budgets, failure behavior, evals, observability, documentation, and an ADR. More agents are not inherently more capable or more trustworthy.
