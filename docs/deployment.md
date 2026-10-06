# Deployment guide

## Local container deployment

Copy `.env.example` to `.env.local`, keep `AI_PROVIDER=demo`, and run `docker compose up --build`. The browser uses `http://localhost:8000` for API calls. Compose applies Alembic migrations and selects `PostgresRepository`; the application still keeps an in-process cache for SSE delivery, and the explicit demo reset deletes the fictional dataset.

## Read-only public showcase

The repository includes a narrow profile for an unauthenticated portfolio deployment. It is a read-only showcase, not a multi-user operations product. Configure the API before process startup:

```dotenv
DEPLOYMENT_PROFILE=public_showcase
AI_PROVIDER=demo
ENABLE_REAL_AI=false
PERSISTENCE_BACKEND=memory
CORS_ALLOWED_ORIGINS=https://your-web-origin.example
PUBLIC_RATE_LIMIT_REQUESTS=120
PUBLIC_RATE_LIMIT_WINDOW_SECONDS=60
```

Build the web app with `NEXT_PUBLIC_API_URL` set to the public API origin. Never place a credential in that variable.

The profile fails startup when real AI, PostgreSQL, wildcard CORS, or a localhost browser origin is configured. It seeds the deterministic flagship incident through the normal coordinator and pauses at `AWAITING_APPROVAL`, then loads the versioned executed result from `evals/results/latest.json`. The API returns `403` for Chaos injection, approval, rejection, evaluation execution, and demo reset. The browser labels the runtime as a public read-only showcase and disables matching controls, but backend policy is the enforcing boundary.

The in-process request limiter is defense in depth for this single-process profile. TLS, denial-of-service protection, request and connection limits, and monitoring still belong at the hosting edge. Do not horizontally scale this profile: its snapshot, limiter, and SSE subscribers are process-local.

## Hosted deployment checklist

Do not expose the interactive local demo unchanged. The read-only showcase above is the only unauthenticated hosted profile. Before a public interactive or multi-user deployment:

1. Run Alembic migrations as a release job and verify the PostgreSQL adapter against the target managed service.
2. Put the API behind authentication, tenant-aware authorization, TLS, rate limits, and an explicit CORS allowlist. Derive approval identity from the authenticated principal rather than the request body.
3. Store API and integration secrets in the platform secret manager.
4. Restrict outbound network access and use allowlisted, least-privilege service credentials.
5. Add distributed idempotency for the external side effect itself. Approval decision and consumption use database compare-and-set, but a database commit cannot prove an external service completed exactly once.
6. Export logs, traces, metrics, and immutable audit records without sensitive payloads.
7. Define retention, deletion, backup, rollback, and on-call procedures.
8. Re-run organization-specific security and model evaluations before enabling any live write adapter.

Authenticate and separately authorize Chaos injection, demo reset, evaluation execution, and approval endpoints outside a local demonstration environment. Do not convert the read-only showcase into an interactive profile without authenticated identities and tenant/session isolation.

## Environment variables

`DEPLOYMENT_PROFILE`, `CORS_ALLOWED_ORIGINS`, `AI_PROVIDER`, `OPENAI_MODEL`, `DEMO_EVENT_DELAY_MS`, request limits, and execution bounds are server settings. `OPENAI_API_KEY` is server-only. `NEXT_PUBLIC_API_URL` is intentionally public and embedded into the web build; it must contain only the API origin, never credentials.
