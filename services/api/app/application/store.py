from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.domain.errors import IncidentNotFound
from app.domain.models import (
    AgentRun,
    Approval,
    AuditRecord,
    Diagnosis,
    EvaluationRun,
    Evidence,
    Hypothesis,
    Incident,
    IncidentEvent,
    IncidentSnapshot,
    RemediationPlan,
    ToolCall,
)


@dataclass
class IncidentData:
    incident: Incident
    events: list[IncidentEvent] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    diagnosis: Diagnosis | None = None
    remediation_plan: RemediationPlan | None = None
    approval: Approval | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    run: AgentRun | None = None


class InMemoryRepository:
    """Replayable demo repository; replaceable through the repository boundary."""

    def __init__(self) -> None:
        self.incidents: dict[str, IncidentData] = {}
        self.audit: list[AuditRecord] = []
        self.evaluation_runs: list[EvaluationRun] = []
        self._subscribers: dict[str, set[asyncio.Queue[IncidentEvent]]] = {}
        self._lock = asyncio.Lock()

    async def reset(self) -> None:
        async with self._lock:
            self.incidents.clear()
            self.audit.clear()
            self.evaluation_runs.clear()
            self._subscribers.clear()

    def add_incident(self, incident: Incident) -> None:
        self.incidents[incident.id] = IncidentData(incident=incident)

    def data(self, incident_id: str) -> IncidentData:
        try:
            return self.incidents[incident_id]
        except KeyError as exc:
            raise IncidentNotFound(incident_id) from exc

    def snapshot(self, incident_id: str) -> IncidentSnapshot:
        data = self.data(incident_id)
        return IncidentSnapshot(
            incident=data.incident,
            events=data.events,
            evidence=data.evidence,
            hypotheses=data.hypotheses,
            diagnosis=data.diagnosis,
            remediation_plan=data.remediation_plan,
            approval=data.approval,
            tool_calls=data.tool_calls,
            run=data.run,
        )

    async def publish(self, event: IncidentEvent) -> None:
        self.data(event.incident_id).events.append(event)
        for queue in tuple(self._subscribers.get(event.incident_id, set())):
            await queue.put(event)

    def subscribe(self, incident_id: str) -> asyncio.Queue[IncidentEvent]:
        self.data(incident_id)
        queue: asyncio.Queue[IncidentEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(incident_id, set()).add(queue)
        return queue

    def unsubscribe(self, incident_id: str, queue: asyncio.Queue[IncidentEvent]) -> None:
        self._subscribers.get(incident_id, set()).discard(queue)


repository = InMemoryRepository()
