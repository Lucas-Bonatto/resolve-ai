# ADR 0005: PostgreSQL is the production repository

## Status

Accepted

## Context

The deterministic local demo benefits from an immediately resettable in-memory store, but that adapter cannot prove restart durability or cross-process approval replay protection. The schema already described PostgreSQL as the production contract, so Phase 3 needed an exercised implementation rather than another abstraction.

## Decision

Keep `InMemoryRepository` as the default no-dependency demo and unit-test adapter. Select `PostgresRepository` explicitly with `PERSISTENCE_BACKEND=postgres` and `DATABASE_URL`; Docker Compose does this by default. Alembic owns reproducible schema changes. PostgreSQL persists the complete incident proof record and atomically consumes an exact, approved, unexpired action before critical execution.

The coordinator retains an in-process event subscriber cache for the current single-process SSE runtime. PostgreSQL remains the system of record; horizontal realtime delivery is a separate future concern.

## Consequences

- Restarts can rehydrate investigations, approvals, audits, reports, and evaluation runs.
- Competing repository instances cannot consume one approval twice.
- Local contributors can still run Demo Mode without PostgreSQL.
- CI provisions PostgreSQL, applies migrations, and runs the guarded integration test.
- A multi-worker hosted deployment still needs durable event fan-out and production authentication.
