from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from time import perf_counter
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from app.application.evaluation import EvaluationRunner
from app.application.orchestrator import coordinator
from app.application.rate_limit import SlidingWindowRateLimiter
from app.application.runtime_policy import runtime_policy
from app.application.showcase import prepare_public_showcase
from app.application.simulator import simulator
from app.application.store import repository
from app.config import settings
from app.domain.errors import (
    ApprovalInvalid,
    IncidentNotFound,
    ReadOnlyRuntimeError,
    ResolveAIError,
)
from app.domain.models import new_id
from app.observability import log_event, reset_correlation_id, set_correlation_id

CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
public_showcase_limiter = SlidingWindowRateLimiter(
    request_limit=settings.public_rate_limit_requests,
    window_seconds=settings.public_rate_limit_window_seconds,
)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str = Field(
        default="demo-operator",
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9_.@-]+$",
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await public_showcase_limiter.reset()
    if runtime_policy.is_public_showcase:
        await prepare_public_showcase(repository, simulator, coordinator)
    yield


app = FastAPI(
    title="ResolveAI API",
    version="0.1.0",
    description="Auditable incident intelligence for the fictional NovaPay environment.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["content-type", "x-correlation-id"],
    expose_headers=["x-correlation-id"],
)


@app.middleware("http")
async def correlation_context(request: Request, call_next: Any) -> Any:
    supplied = request.headers.get("x-correlation-id", "")
    correlation_id = (
        supplied if CORRELATION_ID_PATTERN.fullmatch(supplied) else new_id("corr")
    )
    request.state.correlation_id = correlation_id
    token = set_correlation_id(correlation_id)
    started = perf_counter()
    try:
        retry_after = None
        if runtime_policy.is_public_showcase and request.method not in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            try:
                runtime_policy.require_mutations()
            except ReadOnlyRuntimeError as exc:
                response = JSONResponse(
                    status_code=403,
                    content={
                        "error": type(exc).__name__,
                        "message": str(exc),
                        "recoverable": True,
                        "correlation_id": correlation_id,
                    },
                )
        elif (
            runtime_policy.is_public_showcase
            and request.method != "OPTIONS"
            and request.url.path != "/health"
        ):
            client_id = request.client.host if request.client else "unknown"
            retry_after = await public_showcase_limiter.retry_after(client_id)
            if retry_after is not None:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "RateLimitExceeded",
                        "message": "Limite temporário de solicitações da vitrine excedido.",
                        "recoverable": True,
                        "correlation_id": correlation_id,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        response.headers.setdefault("cache-control", "no-store")
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
        log_event(
            "http.request.completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=max(1, int((perf_counter() - started) * 1000)),
        )
        return response
    except Exception as exc:
        log_event(
            "http.request.failed",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
            duration_ms=max(1, int((perf_counter() - started) * 1000)),
        )
        raise
    finally:
        reset_correlation_id(token)


@app.exception_handler(ResolveAIError)
async def domain_error(request: Request, exc: ResolveAIError) -> Any:
    if isinstance(exc, IncidentNotFound):
        status = 404
    elif isinstance(exc, ReadOnlyRuntimeError):
        status = 403
    else:
        status = 409
    return JSONResponse(
        status_code=status,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "recoverable": True,
            "correlation_id": request.state.correlation_id,
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "mode": "fictional-demo",
        "deployment_profile": settings.deployment_profile,
        "persistence": settings.persistence_backend,
    }


@app.get("/api/runtime")
async def runtime_capabilities() -> dict[str, str | bool]:
    return asdict(runtime_policy.capabilities())


@app.get("/api/chaos/scenarios")
async def list_scenarios() -> list[dict[str, Any]]:
    return simulator.scenarios


@app.post("/api/chaos/scenarios/{scenario_id}/inject", status_code=202)
async def inject_scenario(scenario_id: str, request: Request) -> dict[str, Any]:
    runtime_policy.require_mutations()
    if scenario_id != "payment-webhook-regression":
        raise HTTPException(
            status_code=422, detail="Select the polished flagship scenario in this build"
        )
    incident = await coordinator.inject_flagship(request.state.correlation_id)
    return {
        "incident": incident,
        "status": "SIMULATED",
        "message": "Incident injected successfully.",
    }


@app.get("/api/incidents")
async def list_incidents() -> list[Any]:
    return [data.incident for data in repository.incidents.values()]


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str) -> Any:
    return repository.snapshot(incident_id)


@app.get("/api/incidents/{incident_id}/report")
async def get_incident_report(incident_id: str) -> Any:
    report = repository.data(incident_id).report
    if report is None:
        raise HTTPException(status_code=404, detail="Incident report is not available yet")
    return report


@app.get("/api/incidents/{incident_id}/events")
async def get_events(incident_id: str) -> list[Any]:
    return repository.data(incident_id).events


@app.get("/api/incidents/{incident_id}/events/stream")
async def stream_events(incident_id: str, after_id: str | None = None) -> StreamingResponse:
    queue = repository.subscribe(incident_id)

    async def generate() -> AsyncIterator[str]:
        try:
            recorded = repository.data(incident_id).events
            start = 0
            if after_id:
                matching = next(
                    (index for index, event in enumerate(recorded) if event.id == after_id), None
                )
                start = matching + 1 if matching is not None else 0
            for event in recorded[start:]:
                yield f"id: {event.id}\nevent: incident\ndata: {event.model_dump_json()}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"id: {event.id}\nevent: incident\ndata: {event.model_dump_json()}\n\n"
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            repository.unsubscribe(incident_id, queue)

    return StreamingResponse(
        generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


@app.get("/api/approvals")
async def list_approvals() -> list[Any]:
    return [data.approval for data in repository.incidents.values() if data.approval]


@app.post("/api/approvals/{approval_id}/approve")
async def approve(approval_id: str, request: DecisionRequest) -> Any:
    runtime_policy.require_mutations()
    incident = repository.incident_for_approval(approval_id)
    if incident is None:
        raise ApprovalInvalid("Approval not found")
    return await coordinator.approve(incident.id, approval_id, request.actor)


@app.post("/api/approvals/{approval_id}/reject")
async def reject(approval_id: str, request: DecisionRequest) -> Any:
    runtime_policy.require_mutations()
    incident = repository.incident_for_approval(approval_id)
    if incident is None:
        raise ApprovalInvalid("Approval not found")
    return await coordinator.reject(incident.id, approval_id, request.actor)


@app.get("/api/audit")
async def audit_log(
    correlation_id: str | None = None,
    limit: int = Query(default=200, ge=1, le=200),
) -> list[Any]:
    records = repository.audit
    if correlation_id:
        records = [record for record in records if record.correlation_id == correlation_id]
    return list(reversed(records[-limit:]))


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> Any:
    run = repository.find_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@app.post("/api/evals/run")
async def run_evaluations() -> Any:
    runtime_policy.require_mutations()
    return EvaluationRunner(repository).run()


@app.get("/api/evals/runs")
async def evaluation_runs() -> list[Any]:
    return list(reversed(repository.evaluation_runs))


@app.post("/api/demo/reset")
async def reset_demo() -> dict[str, str]:
    runtime_policy.require_mutations()
    await repository.reset()
    simulator.reset()
    return {"status": "reset", "execution": "SIMULATED"}
