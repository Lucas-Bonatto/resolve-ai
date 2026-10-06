from __future__ import annotations

from pathlib import Path

from app.application.orchestrator import FLAGSHIP_ID, IncidentCoordinator
from app.application.simulator import NovaPaySimulator
from app.application.store import InMemoryRepository
from app.config import ROOT
from app.domain.enums import IncidentState
from app.domain.models import EvaluationRun

LATEST_EVALUATION_RESULT = ROOT / "evals" / "results" / "latest.json"


def load_committed_evaluation_result(
    result_path: Path = LATEST_EVALUATION_RESULT,
) -> EvaluationRun:
    try:
        result = EvaluationRun.model_validate_json(result_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError("The committed evaluation result is unavailable or invalid") from exc
    if result.sample_data:
        raise RuntimeError("The public showcase requires an executed evaluation result")
    return result


async def prepare_public_showcase(
    repo: InMemoryRepository,
    environment: NovaPaySimulator,
    incident_coordinator: IncidentCoordinator,
    result_path: Path = LATEST_EVALUATION_RESULT,
) -> None:
    """Build an inspectable deterministic snapshot before public traffic is accepted."""

    await repo.reset()
    environment.reset()
    previous_delay = incident_coordinator.delay
    incident_coordinator.delay = 0
    try:
        await incident_coordinator.inject_flagship(
            "corr_public_showcase",
            actor_id="public-showcase-seed",
            actor_type="SYSTEM",
        )
        await incident_coordinator.wait_for_investigation(FLAGSHIP_ID)
    finally:
        incident_coordinator.delay = previous_delay

    if repo.data(FLAGSHIP_ID).incident.state != IncidentState.AWAITING_APPROVAL:
        raise RuntimeError("The public showcase flagship snapshot failed to reach its safe pause")
    repo.append_evaluation_run(load_committed_evaluation_result(result_path))
