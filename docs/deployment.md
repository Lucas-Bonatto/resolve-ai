# Deployment guide

## Local container deployment

Copy `.env.example` to `.env.local`, keep `AI_PROVIDER=demo`, and run `docker compose up --build`. The browser uses `http://localhost:8000` for API calls. The Compose PostgreSQL service validates the migration target, but the demo repository remains process-local and resettable.

## Hosted deployment checklist

Do not expose the current local demo unchanged. Before a public multi-user deployment:

1. Implement the PostgreSQL repository interface and run Alembic migrations as a release job.
2. Put the API behind authentication, tenant-aware authorization, TLS, rate limits, and an explicit CORS allowlist.
3. Store API and integration secrets in the platform secret manager.
4. Restrict outbound network access and use allowlisted, least-privilege service credentials.
5. Add distributed idempotency for action execution and approval consumption.
6. Export logs, traces, metrics, and immutable audit records without sensitive payloads.
7. Define retention, deletion, backup, rollback, and on-call procedures.
8. Re-run organization-specific security and model evaluations before enabling any live write adapter.

## Environment variables

`AI_PROVIDER`, `OPENAI_MODEL`, `DEMO_EVENT_DELAY_MS`, and execution bounds are server settings. `OPENAI_API_KEY` is server-only. `NEXT_PUBLIC_API_URL` is intentionally public and embedded into the web build; it must contain only the API origin, never credentials.
