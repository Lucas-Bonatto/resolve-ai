from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict

from app.application.evaluation import EvaluationRunner
from app.application.orchestrator import coordinator
from app.application.simulator import simulator
from app.application.store import repository
from app.config import settings
from app.domain.errors import ApprovalInvalid, IncidentNotFound, ResolveAIError
from app.domain.models import new_id
from app.observability import log_event, reset_correlation_id, set_correlation_id

CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str = "demo-operator"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="ResolveAI API",
    version="0.1.0",
    description="Auditable incident intelligence for the fictional NovaPay environment.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
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
    status = 404 if isinstance(exc, IncidentNotFound) else 409
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
        "persistence": settings.persistence_backend,
    }


@app.get("/api/chaos/scenarios")
async def list_scenarios() -> list[dict[str, Any]]:
    return simulator.scenarios


@app.post("/api/chaos/scenarios/{scenario_id}/inject", status_code=202)
async def inject_scenario(scenario_id: str, request: Request) -> dict[str, Any]:
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
    incident = repository.incident_for_approval(approval_id)
    if incident is None:
        raise ApprovalInvalid("Approval not found")
    return await coordinator.approve(incident.id, approval_id, request.actor)


@app.post("/api/approvals/{approval_id}/reject")
async def reject(approval_id: str, request: DecisionRequest) -> Any:
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
    return EvaluationRunner(repository).run()


@app.get("/api/evals/runs")
async def evaluation_runs() -> list[Any]:
    return list(reversed(repository.evaluation_runs))


@app.post("/api/demo/reset")
async def reset_demo() -> dict[str, str]:
    await repository.reset()
    simulator.reset()
    return {"status": "reset", "execution": "SIMULATED"}
