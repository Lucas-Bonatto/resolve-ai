# Codebase map

This map points to ownership boundaries and primary tests, not every file.

| Concept | Primary implementation | Primary verification |
| --- | --- | --- |
| Incident states and risk enums | `services/api/app/domain/enums.py` | `services/api/tests/test_state_machine.py` |
| Allowed state transitions | `services/api/app/domain/state_machine.py` | `services/api/tests/test_state_machine.py`, flagship tests |
| Domain contracts and argument hashing | `services/api/app/domain/models.py` | permission, flagship, and evaluation tests |
| Permission decision and exact approval checks | `services/api/app/domain/permissions.py` | `services/api/tests/test_permissions.py` |
| Tool registry, validation, budgets, audit, execution | `services/api/app/tools/gateway.py` | `services/api/tests/test_permissions.py` |
| Incident coordinator and approval flow | `services/api/app/application/orchestrator.py` | `services/api/tests/test_flagship_flow.py` |
| Deterministic NovaPay scenario engine | `services/api/app/application/simulator.py` | flagship and tool tests |
| Demo repository, snapshots, SSE queues, audit records | `services/api/app/application/store.py` | flagship and security-invariant tests |
| Demo/OpenAI provider boundary | `services/api/app/agents/providers.py` | `services/api/tests/test_providers.py` |
| Runtime configuration and cost limits | `services/api/app/config.py` | provider, permission, and timeout tests |
| Deterministic evaluation runner | `services/api/app/application/evaluation.py` | `services/api/tests/test_evaluation.py` |
| Evaluation cases and generated result | `evals/cases/benchmark.jsonl`, `evals/results/latest.json` | `evals/run_local.py` |
| FastAPI REST/SSE transport | `services/api/app/main.py` | browser tests and security-invariant route tests |
| PostgreSQL schema contract | `services/api/app/infrastructure/database.py` | Alembic migration and Compose migration service |
| Database migration history | `services/api/alembic/versions/` | CI/setup review; Docker required for PostgreSQL execution |
| NovaPay MCP server | `packages/novapay-mcp/src/novapay_mcp/server.py` | `packages/novapay-mcp/tests/test_tools.py` |
| Controlled buggy code fixture | `fixtures/novapay-services/webhook-worker/` | regression evidence in the flagship scenario |
| Frontend API client | `apps/web/src/lib/api.ts` | component/build/browser checks |
| Frontend API/domain types | `apps/web/src/types/domain.ts` | TypeScript type check and build |
| Incident War Room and SSE client | `apps/web/src/features/war-room/war-room.tsx` | `apps/web/tests/e2e/critical-flow.spec.ts` |
| Approval UI | War Room approval section | approval and rejection browser journeys |
| Evaluation Center | `apps/web/src/features/evaluations/evaluation-center.tsx` | component and evaluation browser test |
| Audit UI | `apps/web/src/features/audit/audit-log.tsx` | API-offline behavior and browser inspection |
| Landing and product narrative | `apps/web/src/app/page.tsx` | lint, type check, build, visual review |
| Design system and responsive layout | `apps/web/src/app/globals.css`, `apps/web/src/components/` | component tests, build, manual/visual review |
| CI | `.github/workflows/ci.yml` | GitHub Actions after publication |
| Architecture decisions | `docs/decisions/` | review when architectural strategy changes |

## Request path

```text
Browser → FastAPI route → IncidentCoordinator → ToolGateway → PermissionEngine
                                             ↘ AIProvider (diagnosis only)
ToolGateway → NovaPaySimulator → Evidence/Audit → InMemoryRepository → SSE → Browser
```

The standalone MCP server models a compatible external operations surface, but the current coordinator invokes its application gateway and simulator directly. Do not describe MCP availability as application authorization.
